#!/usr/bin/env python3
"""Prepare one browser data package from verified SCB and Kolada inputs."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_municipality import county_archive, jsonstat, px
from prepare_model_experiments import migration_cells, migration_inputs

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text())


SCB_ACCOUNTS = 'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6777'

def historical_inputs(code, common):
    def vintage(key):
        vintages = read(Path(f'research/data/skr-{key}-vintages.json'))['vintages']
        return next(item for item in vintages if item['originYear'] == 2024)

    tax = vintage('tax')
    pkv = vintage('pkv')
    population = vintage('revenue')
    national = {key: value for key, value in common['nationalPopulation']['population'].items() if int(key) <= 2024}
    november = {item['year']: item['nationalNovemberPopulation'] for item in population['rows']}
    national.update({str(y): round(national['2024'] * value / november[2024])
                     for y, value in november.items() if y > 2024})
    return (
        {'population': national, 'extrapolateAfter': max(november), 'source': population['source']},
        {'municipality': code, 'baseYear': 2024, 'demography': 'calibrated',
         'sources': {'workbook': 'Decembercirkulär 2024', 'skrCircular': tax['circular'], 'skr': tax['source']},
         'rows': [{'year': t['year'], 'taxBaseGrowth': t['taxBasePercent'], 'labourCostGrowth': p['laborPercent'],
                   'otherPriceGrowth': p['otherPercent']}
                  for t, p in zip(tax['rows'], pkv['rows'], strict=True)]}
    )


def prepare(code, year, source):
    records = read(Path(f'data/municipalities/{code}/base-years.json'))
    archive = Path(records['archive'])
    book = records['years'][str(year)]
    folder = ROOT/f'data/municipalities/{code}'
    supplement_file = folder/'annual-report-inputs.json'
    supplement = read(supplement_file) if supplement_file.exists() else {}
    accounts = jsonstat(ROOT/archive/'TAB6777.json')
    balance = jsonstat(ROOT/archive/'TAB6779.json')
    salary = jsonstat(ROOT/archive/'TAB4202.json')
    changes = {int(k['Tid']): n for name in ('changes-2017-2024', 'changes-2025')
               for k, n in px(ROOT/archive/f'{name}.json') if k['Forandringar']=='130'}
    history = [{'year': y, 'population': p, 'reportedTotal': population, 'births': births, 'deaths': changes[y]}
               for y, p, population, births in zip(range(year-2, year+1), book['cohorts'],
                                                  book['reportedPopulation'], [None, *book['births']])]
    common = read(Path('data/baseline.json'))
    national, planning = historical_inputs(code, common) if year == 2024 else (common['nationalPopulation'], None)
    net = book['payroll']+book['pension']+book['otherOperatingExpense']-book['operatingRevenue']
    inferred_rate = 100*book['interestExpense']/book['openingDebt'] if book['openingDebt'] else 0
    forecast_rate = supplement.get('forecastInterestRate', {}).get(str(year), inferred_rate)
    assumptions = {**common['assumptions'], 'taxRate': book['taxRate'], 'investment': book['investment'],
                   'interestRate': forecast_rate,
                   'educationWeights': [x/sum(book['educationShares']) for x in book['educationShares']],
                   'sectorCosts': [x*net/sum(book['sectorShares']) for x in book['sectorShares']]}
    baseline = {
        'municipality':code, 'name':records['name'], 'baseYear':year, 'source':source,
        'ageGroups':common['ageGroups'], 'population':book['cohorts'][-1], 'reportedPopulation':book['reportedPopulation'][-1],
        'nationalPopulation':national, 'cashCost':net, 'publishedResult':accounts['120'][year],
        'births':book['births'][-1], 'assumptions':assumptions,
        **{key:book[key] for key in ('tax','grants','cash','debt','assets','investment','deaths','depreciation',
                                    'financialIncome','otherFinancialExpense','interestExpense','priorYearSettlement','taxRate')},
        'operatingAccounts':{'payrollExcludingPensions':book['payroll'], 'pensionExpense':book['pension'],
                             'otherOperatingExpense':book['otherOperatingExpense'], 'operatingRevenue':book['operatingRevenue'],
                             'netCostRoundingAdjustment':0},
        'workingCapital':{'receivables':balance['045'][year],'payables':balance['086'][year],
                          'tradeSource':'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6779'},
        'experiments':{'wages':salary['100'][year],'employerContributions':salary['110'][year]},
    }
    work_in_progress = supplement.get('workInProgress', {}).get(str(year))
    if work_in_progress is not None:
        baseline['workInProgress'] = work_in_progress
    grant_advances = supplement.get('grantAdvances', {}).get(str(year))
    if grant_advances is not None:
        baseline['workingCapital']['grantAdvances'] = grant_advances
    archive = supplement.get('novemberPopulationArchive')
    november = None
    if archive:
        manifest = read(Path(archive)/'manifest.json')
        if manifest['municipality'] != code:
            raise ValueError('November population archive is for another municipality')
        raw = read(Path(archive)/manifest['files'][0]['file'])
        november = {'source': 'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6725',
                    'rows': [{'year': int(row['key'][-1]), 'population': int(row['values'][0])}
                             for row in raw['data']]}
        value = next((row['population'] for row in november['rows'] if row['year'] == year), None)
        if value is not None:
            baseline['experiments']['novemberPopulation'] = value
    county_sources = read(Path('data/municipalities/ostergotland-sources.json'))
    migration_archive = county_sources.get('migrationArchive')
    if migration_archive and year in (2024, 2025):
        archive = Path(migration_archive)
        manifest = read(archive/'manifest.json')
        if code in manifest['municipalities']:
            entry = manifest['files'][0]
            raw = (ROOT/archive/entry['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('Migration data do not match the manifest')
            baseline['experiments'].update(migration_inputs(migration_cells(raw), code, [2022, 2023, 2024]))
    skr_file = folder/'skr-revenue-path.json'
    archive_path = county_archive(code)
    if archive_path:
        totals = {}
        for y in (2024, 2025):
            for k, value in px(archive_path/f'november-{y}.json'):
                if k['Region'] == code:
                    totals[y] = totals.get(y, 0) + int(value)
        november = {'source': 'https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6725',
                    'rows': [{'year': y, 'population': total} for y, total in totals.items()]}
        if year in totals:
            baseline['experiments']['novemberPopulation'] = totals[year]

    return {'version': 1, 'baseline': baseline, 'history': history, 'planning': planning, 'novemberPopulation': november,
            'skrRevenue': read(skr_file) if year == 2025 and skr_file.exists() else None,
            'budgetResult': supplement.get('budgetResult', {}).get(str(year)),
            'sources': {**supplement.get('sources', {}), 'statistics': records['source'],
                        'archive': records['archive'], 'accounts': source,
                        'population': f'https://api.kolada.se/v3/data/kpi/N01951/municipality/{code}/year/{year}'}}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('code')
    p.add_argument('year',type=int)
    p.add_argument('source', nargs='?', default=SCB_ACCOUNTS, help='Source URL for municipal accounts')
    args=p.parse_args()
    data=prepare(args.code,args.year,args.source)
    file = 'web.json' if args.year == 2025 else f'web-{args.year}.json'
    (ROOT/f'data/municipalities/{args.code}'/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
