#!/usr/bin/env python3
"""Base years for any municipality from SCB, and a Modelica package that uses the library.

    python3 scripts/prepare_municipality.py 0586 Mjolby "Mjölby" data/downloads/<archive> [--modelica]

Reads an archive written by fetch_municipality.py (SCB's account summary, balance sheet,
equalisation, operating costs, investment and population), and the municipality's care
weights and sector shares (fetch_care_data.py + prepare_care.py, fetch_sector_costs.py) under
data/municipalities/<code>/. Writes data/municipalities/<code>/base-years.json and, with
--modelica, modelica/municipalities/<Package>.mo: Data (one BaseYear per year 2020-2025), Annual extending
Kommunekonomi.Annual with the latest base year, and a one-year test against the outcome.

Definitions (SCB item codes):
  tax 6777:040, of which priorYearSettlement 6782:040; grants 6777:050, of which income
  equalisation 6782:090-170, cost equalisation 130-190, regulation 120-180, LSS 140-200 and
  property fee 210; payroll 4202:100+110; pension 4202:115+120+180+185+186; other operating
  expense the rest of 6777:022; operating revenue 6777:010; depreciation 6777:025; financial
  income 6777:060 and costs 6777:072, of which interest 6782:380 (390 is the group's); debt is bank loans and bonds
  (6779:081+082+136) plus the short-term part (134); cash 6779:065; fixed assets 6779:025
  (including work in progress, which SCB does not separate); investment 5179:950.
For Motala the same definitions reproduce the annual reports to within 2 mnkr from 2023 (tests/test_municipality.py);
for 2020-2022 the annual reports split payroll and pension differently, and fixed assets here include work in progress.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2020, 2026)


def jsonstat(path):
    """{item: {year: value}} from a json-stat2 file with one item dimension."""
    st = json.loads(Path(path).read_text())
    ids, sizes = st['id'], st['size']
    labels = [list(st['dimension'][d]['category']['index']) for d in ids]
    out = {}
    for flat, value in enumerate(st['value']):
        index, rest = [], flat
        for size in reversed(sizes):
            index.append(rest % size)
            rest //= size
        key = dict(zip(ids, (labels[k][i] for k, i in enumerate(reversed(index)))))
        item = [key[d] for d in ids if d not in ('Region', 'ContentsCode', 'Tid')][0]
        out.setdefault(item, {})[int(key['Tid'])] = (value or 0) / 1000  # tkr -> mnkr
    return out


def px(path):
    """Rows of a PxWeb v1 json response as (dict of key codes, value)."""
    t = json.loads(Path(path).read_text())
    keys = [c['code'] for c in t['columns'] if c['type'] != 'c']
    return [(dict(zip(keys, r['key'])), float(r['values'][0]) if r['values'][0] not in ('..', '') else 0.0) for r in t['data']]


def groups(ages):
    return [sum(ages[0:7]), sum(ages[7:16]), sum(ages[16:19]), sum(ages[19:65]), sum(ages[65:])]


def build(code, archive):
    rr, bs, tx, ct, inv = (jsonstat(archive / f'{t}.json') for t in ('TAB6777', 'TAB6779', 'TAB6782', 'TAB4202', 'TAB5179'))
    population = {}
    for name in ('population-2017-2024', 'population-2025'):
        for k, v in px(archive / f'{name}.json'):
            age = k['Alder']
            a = 100 if age.startswith('100') else int(age)
            population.setdefault(int(k['Tid']), [0.0] * 101)[a] += v
    changes = {}
    for name in ('changes-2017-2024', 'changes-2025'):
        for k, v in px(archive / f'{name}.json'):
            changes.setdefault(int(k['Tid']), {})[{'115': 'births', '130': 'deaths'}[k['Forandringar']]] = v
    rates = {int(k['Tid']): v for k, v in px(archive / 'tax-rate.json')}
    folder = ROOT / ('data' if code == '0583' else f'data/municipalities/{code}')
    care = json.loads((folder / 'care-weights.json').read_text())['baseYears']
    sectors = json.loads((folder / 'sector-costs.json').read_text())['years']

    def g(table, item, year):
        return table.get(item, {}).get(year, 0.0)

    def debt(year):
        return sum(g(bs, i, year) for i in ('081', '082', '136', '134'))

    years = {}
    for y in YEARS:
        payroll = g(ct, '100', y) + g(ct, '110', y)
        pension = sum(g(ct, i, y) for i in ('115', '120', '180', '185', '186'))
        expense = -g(rr, '022', y)
        interest = g(tx, '380', y)  # 390 is the group's (koncern), not the municipality's
        financial_cost = -g(rr, '072', y)
        record = {
            'year': y,
            'cohorts': [groups(population[x]) for x in (y - 2, y - 1, y)],
            'reportedPopulation': [sum(population[x]) for x in (y - 2, y - 1, y)],
            'births': [changes[y - 1]['births'], changes[y]['births']], 'deaths': changes[y]['deaths'],
            'tax': g(rr, '040', y), 'priorYearSettlement': g(tx, '040', y), 'grants': g(rr, '050', y),
            'grantComponents': [g(tx, '090', y) - g(tx, '170', y), g(tx, '130', y) - g(tx, '190', y),
                                g(tx, '120', y) - g(tx, '180', y), g(tx, '140', y) - g(tx, '200', y), g(tx, '210', y)],
            'payroll': payroll, 'pension': pension, 'otherOperatingExpense': expense - payroll - pension,
            'operatingRevenue': g(rr, '010', y), 'netCostRoundingAdjustment': 0.0,
            'depreciation': -g(rr, '025', y), 'financialIncome': g(rr, '060', y), 'interestExpense': interest,
            'otherFinancialExpense': financial_cost - interest,
            'debt': debt(y), 'openingDebt': debt(y - 1), 'cash': g(bs, '065', y), 'assets': g(bs, '025', y),
            'investment': g(inv, '950', y), 'taxRate': rates[y],
            'sectorShares': [round(sectors[str(y)]['shares'][k], 4) for k in ('education', 'elderly', 'other')],
            'educationShares': [round(x, 4) for x in sectors[str(y)]['educationSplit']],
            'careCostPerInhabitant': [round(care[str(y)]['costPerInhabitant'][k]) for k in ('65-79', '80+')],
        }
        # The accounts must add up: tax and grants minus net cost plus financial items is the result.
        net = record['payroll'] + record['pension'] + record['otherOperatingExpense'] - record['operatingRevenue'] + record['depreciation']
        result = record['tax'] + record['grants'] - net + record['financialIncome'] - financial_cost
        if abs(net + g(rr, '030', y)) > 0.01 or abs(result - g(rr, '120', y)) > 0.01:
            raise SystemExit(f'{code} {y}: accounts do not reconcile (net {net:.1f} vs {-g(rr, "030", y):.1f}, '
                             f'result {result:.1f} vs {g(rr, "120", y):.1f})')
        if abs(sum(record['reportedPopulation'][-1:]) - sum(record['cohorts'][-1])) > 0.5:
            raise SystemExit(f'{code} {y}: population groups do not add up')
        years[y] = record
    older = population[max(YEARS)][65:]
    older_shares = [sum(older[0:15]) / sum(older), sum(older[15:25]) / sum(older), sum(older[25:]) / sum(older)]
    return years, older_shares


def number(x, digits=1):
    return f'{round(x, digits):g}'


def vector(values, digits=1):
    return '{' + ', '.join(number(v, digits) for v in values) + '}'


def modelica(package, name, code, archive, years, older_shares):
    last = max(years)
    constants = []
    for y in sorted(years, reverse=True):
        r = years[y]
        constants.append(f'''    constant BaseYear {package.lower()}{y} = BaseYear(
      year = {y},
      cohorts = {{{', '.join(vector(c, 0) for c in r['cohorts'])}}},
      reportedPopulation = {vector(r['reportedPopulation'], 0)},
      births = {vector(r['births'], 0)}, deaths = {number(r['deaths'], 0)},
      tax = {number(r['tax'])}, priorYearSettlement = {number(r['priorYearSettlement'])}, grants = {number(r['grants'])},
      grantComponents = {vector(r['grantComponents'])},
      payroll = {number(r['payroll'])}, pension = {number(r['pension'])}, otherOperatingExpense = {number(r['otherOperatingExpense'])}, operatingRevenue = {number(r['operatingRevenue'])}, netCostRoundingAdjustment = 0,
      depreciation = {number(r['depreciation'])}, financialIncome = {number(r['financialIncome'])}, interestExpense = {number(r['interestExpense'])}, otherFinancialExpense = {number(r['otherFinancialExpense'])},
      debt = {number(r['debt'])}, openingDebt = {number(r['openingDebt'])}, cash = {number(r['cash'])}, assets = {number(r['assets'])}, investment = {number(r['investment'])}, taxRate = {number(r['taxRate'], 2)},
      sectorShares = {vector(r['sectorShares'], 4)}, educationShares = {vector(r['educationShares'], 4)},
      careCostPerInhabitant = {vector(r['careCostPerInhabitant'], 0)})
      "SCB:s räkenskapssammandrag och befolkningsstatistik {y} (kommunen); Kolada för omsorgs- och sektorvikter";''')
    newline = '\n'
    return f'''package {package} "{name}: kommunens ekonomi år för år med biblioteket Kommunekonomi; belopp i mnkr, tid i kalenderår"
  package Data "{name}s basår ur SCB:s räkenskapssammandrag och befolkningsstatistik; genereras av scripts/prepare_municipality.py"
    import Kommunekonomi.Data.BaseYear;

{newline.join(constants)}

    constant Real olderShares[3] = {vector(older_shares, 6)} "Andel av 65+ som är 65-79, 80-89 och 90+ vid slutet av {last} (SCB)";
    annotation(Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0): räkenskapssammandraget (TAB6777, TAB6779,
TAB6782, TAB4202, TAB5179), befolkningen per ettårsålder och befolkningsförändringar; Kolada för omsorgskostnad per invånare
och nettokostnad per verksamhet. Arkiv {archive}. Värdena avser kommunen, inte koncernen. Anläggningstillgångarna innehåller
pågående arbeten, som SCB inte särredovisar. Definitionerna står i scripts/prepare_municipality.py.</p></html>"));
  end Data;

  model Annual "{name}s ekonomi år för år från bokslutet {last}"
    extends Kommunekonomi.Annual(base = Data.{package.lower()}{last}, olderShares = Data.olderShares);
    annotation(experiment(StartTime = {last}, StopTime = {last + 8}, Interval = 1),
      Documentation(info = "<html><p><b>Tid: start {last}, slut {last + 8}.</b> Med standardantagandena (illustrativ tillväxt).
Starta från ett annat år med <code>Annual(base = Data.{package.lower()}{last - 1})</code>.</p></html>"));
  end Annual;

  package Examples "Färdiga modeller att simulera"
    model Hindcast{last} "Starta i bokslutet {last - 1} och räkna fram {last}; jämför med utfallet i Data.{package.lower()}{last}"
      extends Annual(base = Data.{package.lower()}{last - 1}, horizon = 1);
      annotation(experiment(StartTime = {last - 1}, StopTime = {last}, Interval = 1));
    end Hindcast{last};
  end Examples;
  annotation(uses(Kommunekonomi(version = "0.1.0")), Documentation(info = "<html><p>{name} (kommunkod {code}) med biblioteket
<a href=\\"modelica://Kommunekonomi\\">Kommunekonomi</a>. Data från SCB och Kolada, genererade av scripts/prepare_municipality.py.
Detta är en forskningsmodell, inte kommunens prognos.</p></html>"));
end {package};
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('code')
    parser.add_argument('package', help='Modelica package name, ASCII (for example Mjolby)')
    parser.add_argument('name', help='Municipality name as written (for example Mjölby)')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--modelica', action='store_true', help='also write modelica/municipalities/<package>.mo')
    args = parser.parse_args()
    archive = args.archive.resolve()
    manifest = json.loads((archive / 'manifest.json').read_text())
    if manifest['municipality'] != args.code:
        raise SystemExit(f'{archive} is for {manifest["municipality"]}, not {args.code}')
    years, older_shares = build(args.code, archive)
    folder = ROOT / f'data/municipalities/{args.code}'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'base-years.json').write_text(json.dumps(
        {'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0); Kolada (RKA)', 'archive': str(archive.relative_to(ROOT)),
         'municipality': args.code, 'name': args.name, 'unit': 'mnkr; persons',
         'definitions': __doc__.split('Definitions (SCB item codes):', 1)[1].strip(),
         'olderShares': older_shares, 'years': {str(y): r for y, r in years.items()}}, indent=1, ensure_ascii=False) + '\n')
    if args.modelica:
        if not args.package.isascii() or not args.package.isidentifier():
            raise SystemExit('The package name must be an ASCII identifier')
        (ROOT / f'modelica/municipalities/{args.package}.mo').write_text(
            modelica(args.package, args.name, args.code, archive.relative_to(ROOT), years, older_shares))
    for y, r in years.items():
        print(y, f"pop {r['reportedPopulation'][-1]:.0f} tax {r['tax']:.0f} grants {r['grants']:.0f} "
                 f"net {r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue']:.0f} "
                 f"dep {r['depreciation']:.0f} debt {r['debt']:.0f} inv {r['investment']:.0f} rate {r['taxRate']}")


if __name__ == '__main__':
    main()
