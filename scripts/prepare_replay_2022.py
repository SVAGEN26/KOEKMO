"""Build the 2022 replay inputs from archived SCB data and a recalculated SKR 21:35 copy."""
import argparse
import hashlib
import json
from pathlib import Path

from import_skr import extract, read_workbook
from prepare_municipality import jsonstat, px

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def load(name):
    return json.loads((ROOT / name).read_text())


def november_population():
    totals = {}
    archives = ('20261118T110040Z', '20261118T111419Z')
    for stamp in archives:
        archive = DATA / 'downloads' / stamp
        entry = json.loads((archive / 'manifest.json').read_text())['files'][0]
        raw = (archive / entry['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry['sha256']
        for record in json.loads(raw)['data']:
            municipality, _, _, year = record['key']
            assert municipality == '0583'
            year = int(year)
            if 2021 <= year <= 2025:
                totals[year] = totals.get(year, 0) + int(record['values'][0])
    return {
        'source': 'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6725',
        'rows': [{'year': year, 'population': value} for year, value in sorted(totals.items())],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path, help='Macro-free, recalculated XLSX with Motala selected')
    parser.add_argument('--scb-check', type=Path, help='Optional fresh download of TAB6777 with the archived query')
    args = parser.parse_args()
    source = load('data/skr-historical/manifest.json')['files'][0]
    workbook = read_workbook(args.workbook)
    totals, inputs = (workbook[s] for s in ('Blad 1 Totala intäkter', 'Blad 2 Indata'))
    assert workbook['Prognosunderlag']['A2']['value'] == '21:35'
    mapping = {
        'vintage': source['publicationDate'],
        'populationReference': 'Folkmängd 1 november året före intäktsåret enligt SKR.',
        'municipalityCheck': {'sheet': 'Prognosunderlag', 'cell': 'B1', 'expected': 583},
        'calculatedMunicipalityCheck': {'sheet': 'Prognosunderlag', 'cell': 'C1'},
        'rows': [],
    }
    rates = []
    for year, out, col in zip(range(2022, 2029), 'CDEFGHI', 'DEFGHIJ'):
        assert totals[out + '9']['value'] == inputs[col + '99']['value'] == year
        mapping['rows'].append({
            'year': year,
            'tax': {'sheet': 'Blad 1 Totala intäkter', 'cell': out + '38', 'scale': .001},
            'grants': {'sheet': 'Blad 1 Totala intäkter', 'cell': out + '40', 'scale': .001},
            'population': {'sheet': 'Blad 2 Indata', 'cell': col + '29'},
        })
        rates.append({'year': year, **{
            key: inputs[col + str(row)]['value'] for key, row in
            [('taxBaseGrowth', 9), ('labourCostGrowth', 100), ('otherPriceGrowth', 101)]
        }})
    path = extract(args.workbook, mapping)
    for row, col in zip(path['rows'], 'CDEFGHI'):
        assert abs(row['tax'] + row['grants'] - totals[col + '36']['value']/1000) < .001
        cells = {i: (totals.get(f'{col}{i}', {}).get('value') or 0) / 1000
                 for i in (12, 14, 16, 18, 20, 22, 24, 28, 30, 32, 34)}
        assert abs(row['tax'] - sum(cells[i] for i in (12, 28, 30, 32))) < .001
        assert abs(row['grants'] - sum(cells[i] for i in (14, 16, 18, 20, 22, 24, 34))) < .001
        row['components'] = {'recurringTax': cells[12], 'incomeEqualisation': cells[14], 'regulation': cells[18]}
    path['provenance'].update(originalUrl=source['originalUrl'], archiveUrl=source['archiveUrl'],
                              originalSha256=source['sha256'], circular=source['circular'])

    scb = load('data/municipalities/0583/base-years.json')
    archive = ROOT / scb['archive']
    accounts = jsonstat(archive / 'TAB6777.json')
    balance = jsonstat(archive / 'TAB6779.json')
    if args.scb_check:
        fresh = jsonstat(args.scb_check)
        for row in ('040', '050', '120'):
            for year in range(2021, 2026):
                assert accounts[row][year] == fresh[row][year], (row, year)
    closing = scb['years']['2021']
    deaths = {int(k['Tid']): v for k, v in px(archive / 'changes-2017-2024.json')
              if k['Forandringar'] == '130' and int(k['Tid']) <= 2021}
    history = [dict(year=year, population=p, reportedTotal=total, births=births, deaths=deaths[year])
               for year,p,total,births in zip(range(2019, 2022), closing['cohorts'], closing['reportedPopulation'],
                                              [None, *closing['births']])]
    net = -accounts['030'][2021] - closing['depreciation']
    sector_shares = closing['sectorShares']
    education_shares = closing['educationShares']
    baseline = load('data/baseline.json')
    assumptions = {**baseline['assumptions'], 'years': 5, 'taxRate': closing['taxRate'],
                   'investment': closing['investment'], 'interestRate': 100*closing['interestExpense']/closing['openingDebt'],
                   'sectorCosts': [net*x/sum(sector_shares) for x in sector_shares],
                   'educationWeights': [x/sum(education_shares) for x in education_shares]}
    assumed_population = {2020: baseline['nationalPopulation']['population']['2020']}
    # SKR uses the preceding November, whereas the first level is the known December 2020 count.
    assumed_population.update({y-1: inputs[c+'26']['value'] for y,c in zip(range(2022, 2029), 'DEFGHIJ')})
    baseline = {
        'municipality': '0583', 'baseYear': 2021, 'ageGroups': baseline['ageGroups'],
        **{k: closing[k] for k in ('tax','grants','depreciation','financialIncome','interestExpense',
                                   'otherFinancialExpense','debt','cash','assets','investment','taxRate','deaths',
                                   'priorYearSettlement')},
        'cashCost': net, 'publishedResult': accounts['120'][2021],
        'births': closing['births'][-1], 'population': closing['cohorts'][-1],
        'reportedPopulation': closing['reportedPopulation'][-1], 'assumptions': assumptions,
        'workInProgress': 0,
        'workingCapital': {'receivables': balance['045'][2021], 'payables': balance['086'][2021],
                           'grantAdvances': None,
                           'tradeSource': 'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6779'},
        'workInProgressSource': {'url': 'https://www.motala.se/media/uploads/arsredovisning-2022.pdf',
                                 'printedPages': [42],
                                 'note': 'Not 12, kommunen i jämförelsekolumnen 2021. Streck för pågående ny- och ombyggnation; tolkas som inget separat bokfört saldo i denna not.'},
        'source': 'https://www.scb.se/OE0107/',
        'nationalPopulation': {'population': assumed_population, 'extrapolateAfter': 2027},
        'operatingAccounts': {
            'payrollExcludingPensions': closing['payroll'], 'pensionExpense': closing['pension'],
            'otherOperatingExpense': closing['otherOperatingExpense'],
            'operatingRevenue': closing['operatingRevenue'], 'netCostRoundingAdjustment': 0,
        },
    }
    ledgers = load('research/data/annual-ledgers.json')
    budget = load('research/benchmark/municipal-budget-history.json')
    comparisons = []
    operating_cash_before = {2022: 306.9, 2023: 211, 2024: 183, 2025: 286}
    for r in ledgers['rows']:
        year = r['year']
        if not 2022 <= year <= 2025:
            continue
        budget_row = next(x for x in budget['budgets'] if x['targetYear']==year and x['stage']=='budget')
        comparisons.append({'year': year, 'outcome': {k:r[k] for k in ('tax','grants','result')},
                            'outcomeSource': ledgers['sources'][r['sourceId']]['url'],
                            'capital': {k:r[k] for k in ('workInProgress','depreciation','debt','investment')},
                            'capitalSource': ledgers['sources'][r.get('stockSourceId') or r['sourceId']]['url'],
                            'cashFlow': {'operatingCash': r['operatingCash'],
                                         'workingCapitalCash': round(r['operatingCash'] - operating_cash_before[year], 1)},
                            'scb': {k:accounts[c][year] for k,c in [('tax','040'),('grants','050'),('result','120')]},
                            'budgetResult': budget_row['value'],
                            'budgetSource': budget['sources'][budget_row['sourceId']]['url']})
    municipal_budgets = load('data/municipal-budgets.json')
    budget_2026 = municipal_budgets['budgets'][0]
    comparisons.append({
        'year': 2026, 'outcome': None, 'scb': None,
        'budgetResult': budget_2026['result'][0], 'budgetSource': budget_2026['sourceUrl'],
        'budgetTax': budget_2026['tax'][0], 'budgetGrants': budget_2026['grants'][0],
    })
    output = {
        'baseline': baseline, 'history': history,
        'planning': {'municipality': '0583', 'baseYear': 2021, 'demography': 'calibrated',
                     'rows': rates, 'revenuePath': path,
                     'sources': {'workbook': source['file'], 'skrCircular': '21:35', 'archive': scb['archive']}},
        'comparisons': comparisons,
        'novemberPopulation': november_population(),
        'scbSource': {'archive': scb['archive'], 'tables': ['TAB6777','TAB6779','TAB6782','TAB4202','TAB5179'],
                      'tab6777Sha256': hashlib.sha256((archive/'TAB6777.json').read_bytes()).hexdigest()},
    }
    (DATA/'replay-2022.json').write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    main()
