"""Build the static site into site/dist without network access.

The forecast engine is OpenModelica's in-browser compiler; stage it first with
scripts/stage_omc.py. The result is plain static files, ready for GitHub Pages.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'site/dist'
OMC = ROOT / 'site/omc-web'
# engine.js is the independent JavaScript reference for the tests; the site never runs it.
NOT_SHIPPED = {'engine.js'}
DATA = ['baseline.json', 'history.json', 'sources.json', 'backtest.json', 'municipal-benchmarks.json',
        'operating-accounts-history.json', 'planning-inputs.json', 'skr-revenue-path.json', 'replay-2022.json',
        'model-experiments.json', 'age-income.json', 'rate-fixing.json']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def series_catalogue():
    """Outcomes and history the AI tools read (site/src/ai-tools.js, get_series): one file, with sources."""
    load = lambda path: json.loads((ROOT / path).read_text())
    residual = load('data/cost-residual.json')
    long = load('data/long-hindcast.json')
    long_continuous = load('data/long-hindcast-continuous.json')
    responses = load('data/response-test.json')
    responses['prices'] = {k: v for k, v in responses['prices'].items() if k != 'rows'}
    national = load('data/national-population.json')
    out = {'municipalities': {}, 'national': {
        'pkv': {'unit': 'share per year', 'source': residual['source'],
                'description': "SKR's price index for municipal activities, outcomes: pkv (total), labour, other",
                'rows': [{'year': int(y), **v} for y, v in sorted(residual['pkv'].items())]},
        'population': {'unit': 'persons, 31 December', 'source': national.get('source'), 'note': national.get('note'),
                       'rows': [{'year': int(y), 'population': v} for y, v in sorted(national['population'].items())]},
        'hindcast': {'source': 'scripts/hindcast_long.py, data/long-hindcast.json and data/long-hindcast-continuous.json', 'units': long['units'],
                     'description': 'Model against outcomes 2017-2019 to 2025, 13 municipalities: mean error and mean absolute '
                                    'error per horizon, and the benchmark persistence (the base year\'s result share kept)',
                     'models': 'summaryByHorizon is the yearly model (Kommunekonomi.Annual); summaryByHorizonContinuous is the '
                               'continuous model, which the site runs by default. Persistence is the same for both.',
                     'summaryByHorizon': long['summaryByHorizon'],
                     'summaryByHorizonContinuous': {k: v for k, v in long_continuous['summaryByHorizon'].items() if k != 'persistence'}},
        'responses': {'source': 'scripts/response_test.py, data/response-test.json',
                      'description': 'The model\'s rules against the accounts of 13 municipalities: slope of the observed change on the '
                                     'model\'s (1 = history moved as the model says), with a 95 % interval', **responses}}}
    for folder in sorted((ROOT / 'data/municipalities').glob('[0-9]*')):
        if not (folder / 'base-years.json').is_file():
            continue
        code = folder.name
        records = json.loads((folder / 'base-years.json').read_text())
        rows = []
        for y, r in sorted(records['years'].items()):
            net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['depreciation']
            rows.append({'year': int(y), 'population': r['reportedPopulation'][-1], 'births': r['births'], 'deaths': r['deaths'],
                         'taxRate': r['taxRate'], 'tax': r['tax'], 'grants': r['grants'], 'netCost': net,
                         'result': r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense'],
                         'payroll': r['payroll'], 'pension': r['pension'], 'otherOperatingExpense': r['otherOperatingExpense'],
                         'operatingRevenue': r['operatingRevenue'], 'depreciation': r['depreciation'],
                         'interestExpense': r['interestExpense'], 'debt': r['debt'], 'cash': r['cash'], 'assets': r['assets'],
                         'investment': r['investment'], 'grantComponents': r['grantComponents']})
        drift = residual['municipalities'].get(code, {})
        out['municipalities'][code] = {
            'name': records['name'],
            'accounts': {'unit': 'mnkr; population in persons; taxRate in percent', 'source': records['source'],
                         'archive': records['archive'], 'definitions': ' '.join(records['definitions'].split()),
                         'note': 'Kommunen, not the group. The result leaves out extraordinary items and the one-offs the annual '
                                 'reports mark as jämförelsestörande (annual-report-inputs.json). grantComponents: income, cost, '
                                 'regulation and LSS equalisation and the property fee.',
                         'rows': rows},
            'costGrowth': {'unit': 'share per year', 'source': residual['source'],
                           'description': 'Cost growth beyond prices and the service volume, measured as the model uses costDrift '
                                          '(scripts/cost_residual.py)', 'excludedYears': drift.get('excludedYears', []),
                           'rows': [{'year': int(y), 'residual': v['residual'], 'volumeGrowth': v['volumeGrowth'], 'pkv': v['pkv']}
                                    for y, v in sorted(drift.get('years', {}).items())]}}
    return out


def main():
    manifest_file = OMC / 'manifest.json'
    if not manifest_file.is_file():
        raise SystemExit('OpenModelica web compiler missing. Run scripts/stage_omc.py <share/omc/web> first.')
    manifest = json.loads(manifest_file.read_text())
    for name, entry in manifest['files'].items():
        if sha(OMC / name) != entry['sha256']:
            raise SystemExit(f'site/omc-web/{name} does not match its manifest. Stage the compiler again.')

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for source in (ROOT / 'site/src').iterdir():
        if source.is_file() and source.name not in NOT_SHIPPED:
            shutil.copy2(source, DIST / source.name)
    for name in DATA:
        shutil.copy2(ROOT / 'data' / name, DIST / name)
    shutil.copy2(ROOT / 'modelica/Kommunekonomi.mo', DIST / 'Kommunekonomi.mo')
    shutil.copy2(ROOT / 'modelica/Motala.mo', DIST / 'Motala.mo')
    municipal_data = {}
    for folder in sorted((ROOT / 'data/municipalities').glob('[0-9]*')):
        if not (folder / 'web.json').is_file():
            continue
        code = folder.name
        records = json.loads((folder / 'base-years.json').read_text())
        package = records['packageName']
        municipal_data[code] = {
            'current': json.loads((folder / 'web.json').read_text()),
            'historical': json.loads((folder / 'web-2024.json').read_text()),
        }
        if code != '0583':
            shutil.copy2(ROOT / 'modelica/municipalities' / f'{package}.mo', DIST / f'{package}.mo')
        reference = folder / 'skr-revenue-path.json'
        if reference.is_file():
            target = DIST / 'municipalities' / code
            target.mkdir(parents=True)
            shutil.copy2(reference, target / reference.name)
    (DIST / 'municipalities-data.json').write_text(json.dumps(municipal_data, ensure_ascii=False))
    (DIST / 'series.json').write_text(json.dumps(series_catalogue(), ensure_ascii=False))
    # Preserve the Finspång URLs used before the shared municipality picker.
    shutil.copy2(ROOT / 'data/municipalities/0562/web.json', DIST / 'finspang.json')
    shutil.copy2(ROOT / 'data/municipalities/0562/skr-revenue-path.json', DIST / 'finspang-skr-revenue-path.json')
    shutil.copy2(ROOT / 'data/municipalities/0562/vintage-hindcast.json', DIST / 'finspang-vintage-hindcast.json')
    shutil.copy2(ROOT / 'modelica/MotalaBrowser.mo', DIST / 'MotalaBrowser.mo')
    shutil.copytree(OMC, DIST / 'omc-web')
    shutil.copy2(ROOT / 'docs/methodology.md', DIST / 'methodology.md')
    shutil.copy2(ROOT / 'LICENSE', DIST / 'LICENSE.txt')
    planning = json.loads((ROOT / 'data/planning-inputs.json').read_text())
    for document in planning['documents']:
        shutil.copy2(ROOT / planning['sources']['archive'] / document['file'], DIST / document['file'])
    (DIST / '.nojekyll').write_text('')
    print('Static site ready in', DIST, '· OpenModelica', manifest['revision'])


if __name__ == '__main__':
    main()
