"""Evaluate the frozen PKV rule on the predeclared external municipality panel."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
import math
from pathlib import Path
import shutil
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
MODELS = ('PKV-accounting', 'Persistence', 'Historical mean')
OPENING_FIELDS = ('operatingRevenue', 'grossExpense', 'personnel', 'depreciation',
                  'netCost', 'tax', 'grants', 'financialIncome', 'financialExpense', 'result')


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def load_frozen(directory=ROOT/'reference/pkv-accounting-v1'):
    directory = Path(directory)
    for name, expected in read(directory/'manifest.json').items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen candidate hash mismatch: '+name)
    protocol = read(directory/'protocol.json')
    for filename, key in [('macro.py', 'sourceHash'), ('skr-pkv-vintages.json', 'macroSourceHash')]:
        if hashlib.sha256((directory/filename).read_bytes()).hexdigest() != protocol[key]:
            raise ValueError('Protocol hash mismatch: '+filename)
    spec = importlib.util.spec_from_file_location('motala_lab._frozen_panel_macro', directory/'macro.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, protocol, read(directory/'skr-pkv-vintages.json')


def opening(row):
    """Adapt a reported total to the frozen aggregate personnel interface."""
    for key in OPENING_FIELDS:
        if type(row.get(key)) not in (int, float) or not math.isfinite(row[key]):
            raise ValueError('Missing/nonfinite opening field: '+key)
    if row['tax']+row['grants'] <= 0 or not 0 <= row['personnel'] <= row['grossExpense']:
        raise ValueError('Invalid opening scale or personnel total')
    result = deepcopy(row)
    result.update(payroll=row['personnel'], pension=0,
        otherExpense=row['grossExpense']-row['personnel'],
        costRounding=row['netCost']-(row['grossExpense']-row['operatingRevenue']+row['depreciation']),
        resultRounding=row['result']-(row['tax']+row['grants']-row['netCost']+
                                     row['financialIncome']-row['financialExpense']),
        population=None, interest=None,
        personnelAdapter='payroll holds total personnel; pension=0 is an interface placeholder, not observed zero pension')
    quantum = row.get('roundingUnitMnkr')
    if type(quantum) not in (int, float) or not math.isfinite(quantum) or quantum <= 0:
        raise ValueError('Source rounding precision must be explicit')
    # Four rounded quantities in net cost; six in the result identity.
    # Half a reporting unit per quantity is the largest rounding-only error.
    for key, terms in [('costRounding', 4), ('resultRounding', 6)]:
        if abs(result[key]) > terms*quantum/2+1e-9:
            raise ValueError('Unexplained accounting residual: '+key)
    if 'personnelComponents' in row and abs(sum(row['personnelComponents'].values())-row['personnel']) > 1e-9:
        raise ValueError('Personnel components do not match reported total')
    return result


def evaluate(data, protocol, macro_data, candidate):
    if data['scope'] != 'kommunen' or data['moneyUnit'] != 'mnkr':
        raise ValueError('Expected municipal accounts in mnkr')
    supplied = {m['id']: m for m in data['municipalities']}
    declared = {m['id'] for m in protocol['municipalities']}
    if len(supplied) != len(data['municipalities']) or set(supplied) != declared:
        raise ValueError('Panel must contain exactly the predeclared municipalities')
    cases = []
    for municipality in protocol['municipalities']:
        source = supplied[municipality['id']]
        rows = {r['year']: r for r in source['rows']}
        expected_years = set(range(protocol['historyStartYear'], protocol['targetEndYear']+1))
        if len(rows) != len(source['rows']) or set(rows) != expected_years:
            raise ValueError('Every declared year must have one row, using null for missing values')
        for row in rows.values():
            if row['source'] not in data['sources']:
                raise ValueError('Unknown ledger source')
            value = row.get('result')
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError('Nonfinite result')
            if value is None and not row.get('missingReason'):
                raise ValueError('Missing result must have an explicit reason')
        for origin in protocol['originYears']:
            horizons = [h for h in protocol['horizons'] if origin+h <= protocol['targetEndYear']]
            start = rows[origin]
            missing = [key for key in OPENING_FIELDS if start.get(key) is None]
            adapted = None if missing else opening(start)
            vintage = candidate.select_vintage(macro_data, origin, max(horizons))
            predictions = {} if adapted is None else {
                r['year']: r for r in candidate.accounting_projection(adapted, vintage, protocol['parameters'])}
            history = [rows[y]['result'] for y in range(protocol['historyStartYear'], origin+1)]
            for h in horizons:
                target = rows[origin+h]
                scale = None if adapted is None else start['tax']+start['grants']
                values = {
                    'PKV-accounting': predictions.get(origin+h, {}).get('result'),
                    'Persistence': start['result'],
                    'Historical mean': None if None in history else mean(history)}
                reasons = []
                if missing:
                    reasons.append('Missing opening fields: '+', '.join(missing))
                if None in history:
                    reasons.append('Incomplete pre-origin history for mean baseline')
                if target['result'] is None:
                    reasons.append(target['missingReason'])
                comparable = scale is not None and target['result'] is not None and all(v is not None for v in values.values())
                case = dict(municipality=municipality['name'], municipalityId=municipality['id'],
                    origin=origin, target=origin+h, horizon=h, actual=target['result'],
                    scaleTaxAndGrants=scale, predictions=values,
                    components=predictions.get(origin+h), opening=adapted,
                    macroPublicationDate=vintage['publicationDate'], macroCutoff=vintage['macroCutoff'],
                    openingAccountsAvailableAtMacroCutoff=False,
                    openingSource=start['source'], outcomeSource=target['source'],
                    comparable=comparable, missingReasons=reasons)
                case['errors'] = {} if not comparable else {m: dict(
                    errorMnkr=v-target['result'],
                    errorPercentagePoints=100*(v-target['result'])/scale) for m, v in values.items()}
                cases.append(case)
    return dict(protocolRegisteredAt=protocol['registeredAt'], evaluatedAt=datetime.now(timezone.utc).isoformat(),
                cases=cases, scores=score(cases, protocol))


def metrics(cases):
    result = {}
    for model in MODELS:
        errors = [c['errors'][model]['errorMnkr'] for c in cases]
        normalized = [c['errors'][model]['errorPercentagePoints'] for c in cases]
        result[model] = dict(n=len(cases), maeMnkr=mean(map(abs, errors)),
            biasMnkr=mean(errors), rmseMnkr=math.sqrt(mean(e*e for e in errors)),
            maePercentagePoints=mean(map(abs, normalized)), biasPercentagePoints=mean(normalized),
            rmsePercentagePoints=math.sqrt(mean(e*e for e in normalized)))
    return result


def equal_municipality(cases, ids):
    result = {}
    for mid in ids:
        selected = [c for c in cases if c['municipalityId'] == mid and c['comparable']]
        if selected:
            result[mid] = metrics(selected)
    # Never present a missing municipality as a zero error or silently change panel composition.
    if set(result) != set(ids):
        return None
    return {model: mean(result[mid][model]['maePercentagePoints'] for mid in ids) for model in MODELS}


def score(cases, protocol):
    scores = []
    ids = [m['id'] for m in protocol['municipalities']]
    for h in protocol['horizons']:
        selected = [c for c in cases if c['horizon'] == h]
        comparable = [c for c in selected if c['comparable']]
        by_municipality = {}
        for mid in ids:
            expected = [c for c in selected if c['municipalityId'] == mid]
            observed = [c for c in expected if c['comparable']]
            by_municipality[mid] = dict(expected=len(expected), scored=len(observed),
                                        models=metrics(observed) if observed else None)
        by_year = []
        for year in sorted({c['target'] for c in selected}):
            keep = [c for c in selected if c['target'] == year]
            by_year.append(dict(target=year, expected=len(keep), scored=sum(c['comparable'] for c in keep),
                equalMunicipalityMaePercentagePoints=equal_municipality(keep, ids)))
        loo = []
        for year in sorted({c['target'] for c in selected}):
            keep = [c for c in selected if c['target'] != year]
            if keep:
                loo.append(dict(excludedTarget=year, expected=len(keep), scored=sum(c['comparable'] for c in keep),
                    equalMunicipalityMaePercentagePoints=equal_municipality(keep, ids)))
        scores.append(dict(horizon=h, expected=len(selected), scored=len(comparable),
            complete=len(selected) == len(comparable), byMunicipality=by_municipality,
            equalMunicipalityMaePercentagePoints=equal_municipality(selected, ids),
            byTargetYear=by_year, leaveOneTargetYearOut=loo))
    return scores


def report(result, data, directory):
    esc = html.escape
    def fmt(v):
        return 'saknas' if v is None else f'{v:.3f}'
    parts = ['<!doctype html><html lang="sv"><meta charset="utf-8"><title>Extern PKV-prövning</title>',
        '<style>body{font:16px system-ui;max-width:1250px;margin:2rem auto;padding:1rem;line-height:1.5}'
        'table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #ccc;padding:.4rem;text-align:right}'
        'th:first-child,td:first-child{text-align:left}.notice{background:#fff0c2;padding:1rem}a{color:#0645ad}</style>',
        '<h1>Extern prövning av fryst PKV-regel</h1>',
        '<p>Vadstena, Mjölby och Norrköping. Ursprung 2022–2024, målår 2023–2025. '
        'Kommuner, år, beräkningsregel och makroprognoser låstes före insamlingen av panelens bokslut. '
        'Ingen koefficient har anpassats till panelens utfall.</p>',
        '<p class="notice">Detta är ett retrospektivt test med bokslutsvärden som blev tillgängliga efter '
        'decemberprognosen. Det är inte en historisk realtidsprognos. Gemensamma målår innebär gemensamma '
        'makrochocker; kommunerna är inte oberoende observationer av konjunkturen. Alla engångsposter behålls. '
        'Saknade värden ingår i täckningen men poängsätts inte. Ofullständiga poäng är preliminära.</p>',
        '<p><a href="evaluation.json">Alla prognoser, fel och känslighetsmått</a> · '
        '<a href="ledgers.json">Data och källor</a> · <a href="sources/reference/pkv-accounting-v1/protocol.json">Låst protokoll</a> · '
        '<a href="manifest.json">Filhashar</a></p>',
        '<h2>Genomsnittligt absolut fel, procentenheter av öppningsårets skatter och generella bidrag</h2>',
        '<p>Varje kommun har samma vikt. Ett värde på 1 betyder ett fel motsvarande 1 procent av dessa intäkter. '
        'Resultat i mnkr redovisas per kommun nedan.</p>',
        '<table><tr><th>Horisont</th><th>Poängsatta/planerade</th>'+''.join('<th>'+m+'</th>' for m in MODELS)+'</tr>']
    for score_row in result['scores']:
        total = score_row['equalMunicipalityMaePercentagePoints'] or {}
        parts.append(f'<tr><td>{score_row["horizon"]} år</td><td>{score_row["scored"]}/{score_row["expected"]}</td>'+
                     ''.join('<td>'+fmt(total.get(m))+'</td>' for m in MODELS)+'</tr>')
    parts.append('</table><h2>Fel per kommun</h2><table><tr><th>Kommun / horisont</th><th>Modell</th>'
                 '<th>N</th><th>MAE mnkr</th><th>Bias mnkr</th><th>RMSE mnkr</th></tr>')
    names = {m['id']: m['name'] for m in data['municipalities']}
    for score_row in result['scores']:
        for mid, cell in score_row['byMunicipality'].items():
            for model, m in (cell['models'] or {}).items():
                parts.append(f'<tr><td>{esc(names[mid])} / {score_row["horizon"]} år</td><td>{model}</td>'
                    f'<td>{m["n"]}/{cell["expected"]}</td><td>{fmt(m["maeMnkr"])}</td>'
                    f'<td>{fmt(m["biasMnkr"])}</td><td>{fmt(m["rmseMnkr"])}</td></tr>')
    parts.append('</table><h2>Samtliga fall, mnkr</h2><table><tr><th>Kommun</th><th>Ursprung → mål</th>'
        '<th>Utfall</th>'+''.join('<th>'+m+'</th>' for m in MODELS)+'<th>Status</th></tr>')
    for c in result['cases']:
        parts.append(f'<tr><td>{esc(c["municipality"])}</td><td>{c["origin"]} → {c["target"]}</td>'
            f'<td>{fmt(c["actual"])}</td>'+''.join('<td>'+fmt(c['predictions'][m])+'</td>' for m in MODELS)+
            '<td>'+esc('; '.join(c['missingReasons']) or 'poängsatt')+'</td></tr>')
    parts.append('</table><h2>Gemensamma målår och känslighet</h2><p>Positiv skillnad betyder större '
        'absolut fel för PKV-regeln. Alla värden är procentenheter med lika kommunvikt. '
        'Att lämna ett målår ute är en beskrivande känslighetskontroll, inget konfidensintervall.</p>'
        '<table><tr><th>Horisont / urval</th><th>Poängsatta/planerade</th>'
        '<th>PKV − oförändrat resultat</th><th>PKV − historiskt medel</th></tr>')
    for score_row in result['scores']:
        for field, prefix, key in [('byTargetYear', 'målår', 'target'),
                                  ('leaveOneTargetYearOut', 'utan målår', 'excludedTarget')]:
            for row in score_row[field]:
                values = row['equalMunicipalityMaePercentagePoints']
                differences = [None, None] if values is None else [values[MODELS[0]]-values[m] for m in MODELS[1:]]
                parts.append(f'<tr><td>{score_row["horizon"]} år / {prefix} {row[key]}</td>'
                    f'<td>{row["scored"]}/{row["expected"]}</td>'+
                    ''.join('<td>'+fmt(value)+'</td>' for value in differences)+'</tr>')
    parts.append('</table><h2>Databegränsningar och källor</h2><p>'+esc(data['accessNote'])+'</p>')
    for municipality in data['municipalities']:
        notes = municipality.get('notes', []) + [f'{r["year"]}: '+n for r in municipality['rows'] for n in r.get('sourceNotes', [])]
        parts.append('<h3>'+esc(municipality['name'])+'</h3><ul>'+''.join('<li>'+esc(n)+'</li>' for n in notes)+'</ul>')
    parts.append('<ul>'+''.join('<li><a href="'+esc(s['url'], quote=True)+'">'+esc(s['title'])+'</a>, '+
        esc(str(s.get('pages', '')))+'</li>' for s in data['sources'].values())+'</ul></html>')
    (Path(directory)/'report.html').write_text('\n'.join(parts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'data/external-pkv-ledgers.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    candidate, protocol, macro_data = load_frozen()
    data = read(args.data)
    result = evaluate(data, protocol, macro_data, candidate)
    args.out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT/'reference/pkv-accounting-v1', args.out/'sources/reference/pkv-accounting-v1')
    dump(args.out/'ledgers.json', data)
    dump(args.out/'evaluation.json', result)
    for name in ('motala_lab/__init__.py', 'motala_lab/external_pkv.py', 'motala_lab/dynamics.py',
                 'run_external_pkv.py', 'tests/test_external_pkv.py'):
        destination = args.out/'sources'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, destination)
    (args.out/'sources/data').mkdir()
    dump(args.out/'sources/data/external-pkv-ledgers.json', data)
    report(result, data, args.out)
    dump(args.out/'manifest.json', {str(p.relative_to(args.out)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.out.rglob('*')) if p.is_file()})
    print(args.out/'report.html')
    return 0
