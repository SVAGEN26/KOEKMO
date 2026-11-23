"""Native continuous Modelica runs and annual flow integration; standard library only."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
YEAR_SECONDS = 31557600
SCENARIOS = {
    'base': 'Base', 'school-decline': 'SchoolDecline',
    'fast-adjustment': 'FastAdjustment', 'staffing-cut': 'StaffingCut',
    'interest-shock': 'InterestShock', 'pension-accrual': 'PensionAccrual',
    'supply-constraint': 'SupplyConstraint',
    'extra-cost': 'ExtraCost',
    'tax-settlement': 'TaxSettlement',
}
SCENARIO_DESCRIPTIONS = {
    'base': 'Befolkningen utvecklas enligt kohortmodellen; övriga banor följer modellens grundantaganden.',
    'school-decline': 'Befolkningen hålls konstant. Utbildningsbehovet minskar 15 procent från 2027; personalen anpassas med tre års tidskonstant.',
    'fast-adjustment': 'Samma behovsminskning som school-decline, med ett halvt års tidskonstant för utbildningens personalminskning.',
    'staffing-cut': 'Befolkningen hålls konstant. Utbildningens bemanningsmål minskar 20 procent från 2027; ingen ersättande service köps.',
    'interest-shock': 'Marknadsräntan höjs till fem procent från 2027; låneportföljens ränta anpassas gradvis.',
    'pension-accrual': 'Pensionskostnaden ökar 85 mnkr per år från 2027; betalningsbanan är oförändrad.',
    'supply-constraint': 'Befolkningen hålls konstant. Omsorgsbehovet ökar 20 procent från 2027. Personalens förändringstakt och köpt service begränsas.',
    'extra-cost': 'Extra kostnad på 50 mnkr under 2027, med betalning 20 mnkr 2027 och 30 mnkr 2028. Beloppen är nominella scenarioantaganden.',
    'tax-settlement': 'Referensskatt och bidrag hålls konstanta. En antagen kollektiv skatteavräkning på 50 mnkr bokförs 2027 och betalas 2028. Övriga delar följer grundmodellen.',
}
FLOW_COLUMNS = {
    'result': 'finance.cumulativeResult', 'payroll': 'cumulativePayroll',
    'otherOperatingExpense': 'cumulativeOtherExpense', 'operatingRevenue': 'cumulativeRevenue',
    'tax': 'cumulativeTax', 'grants': 'cumulativeGrants', 'depreciation': 'cumulativeDepreciation',
    'disposalLoss': 'cumulativeDisposal', 'interest': 'cumulativeInterest',
    'pensionExpense': 'cumulativePensionExpense', 'operatingCash': 'finance.cumulativeOperatingCash',
    'investment': 'finance.cumulativeInvestment', 'borrowing': 'finance.cumulativeBorrowing',
    'repayment': 'finance.cumulativeRepayment',
    'transitionExpense': 'cumulativeTransitionExpense',
}
EXTRA_FLOW_COLUMNS = {'extraExpense': 'cumulativeExtraExpense', 'extraPayments': 'cumulativeExtraPayments'}
TAX_CASH_COLUMNS = {'taxPayments': 'finance.cumulativeTaxPayments',
                    'taxSettlement': 'cumulativeTaxSettlement'}


def compiler():
    path = os.environ.get('OMC') or shutil.which('omc')
    local = Path('/home/johti17/OpenModelicaWork/om-install/bin/omc')
    if not path and local.exists():
        path = str(local)
    if not path:
        raise RuntimeError('OpenModelica is required. Set OMC=/absolute/path/to/omc.')
    return path


def literal(value):
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) in (int, float) and math.isfinite(value):
        return repr(value)
    if isinstance(value, list) and value:
        if all(isinstance(row, list) for row in value):
            if not value[0] or any(len(row) != len(value[0]) for row in value):
                raise ValueError('Parameter matrices must be rectangular and nonempty')
            return '[' + ';'.join(','.join(literal(x) for x in row) for row in value) + ']'
        return '{' + ','.join(literal(x) for x in value) + '}'
    raise ValueError('Overrides must be finite numbers, booleans, or nonempty numeric arrays')


def scenario_source(name='base', parameters=None):
    parameters = {} if parameters is None else parameters
    if not isinstance(parameters, dict):
        raise ValueError('Parameter file must contain a JSON object')
    for key in parameters:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', key):
            raise ValueError('Invalid parameter/input name: ' + key)
    modifiers = ','.join(key + '=' + literal(value) for key, value in parameters.items())
    binding = '(plant(' + modifiers + '))' if modifiers else ''
    return ('within ;\nmodel Scenario\n  extends MotalaDynamics.Examples.'
            + SCENARIOS[name] + binding + ';\nend Scenario;\n')


def simulate(source, years, directory, *, package=None, intervals_per_year=12):
    """Save native source, log and CSV; reject assertion failures even with exit code 0."""
    if type(years) is not int or not 1 <= years <= 100:
        raise ValueError('years must be an integer from 1 to 100')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    package = Path(package or ROOT / 'MotalaDynamics/package.mo').resolve()
    omc = compiler()
    (directory / 'Scenario.mo').write_text(source, encoding='utf-8')
    mos = (f'loadFile({json.dumps(str(package))});\nloadFile("Scenario.mo");\n'
           'checkModel(Scenario);\ngetErrorString();\n'
           f'simulate(Scenario,stopTime={years * YEAR_SECONDS},numberOfIntervals={years * intervals_per_year},'
           'tolerance=1e-8,outputFormat="csv");\ngetErrorString();\n')
    (directory / 'run.mos').write_text(mos)
    with tempfile.TemporaryDirectory(prefix='motala-dynamics-native-') as temp:
        build = Path(temp)
        (build / 'Scenario.mo').write_text(source, encoding='utf-8')
        (build / 'run.mos').write_text(mos)
        proc = subprocess.run([omc, 'run.mos'], cwd=build, capture_output=True, text=True, timeout=180)
        log = proc.stdout + proc.stderr
        (directory / 'omc.log').write_text(log, encoding='utf-8')
        raw = build / 'Scenario_res.csv'
        if (proc.returncode or not raw.exists() or 'The simulation finished successfully' not in log
                or re.search(r'LOG_ASSERT\s*\|\s*error|\bError:', log)):
            raise RuntimeError(f'Native simulation failed; see {directory / "omc.log"}\n{log[-4000:]}')
        shutil.copy2(raw, directory / 'native.csv')
        shutil.copy2(build / 'Scenario_init.xml', directory / 'initialization.xml')
        # Calculated parameters have no XML start value. Read initialized runtime values.
        parameter_nodes = {}
        for variable in ET.parse(build / 'Scenario_init.xml').getroot().iter('ScalarVariable'):
            name = variable.get('name', '')
            if variable.get('variability') != 'parameter' or not name.startswith('plant.'):
                continue
            name = name.removeprefix('plant.')
            if '.' in name:
                continue
            parameter_nodes[name] = variable
        resolved = {}
        if parameter_nodes:
            values = subprocess.run([str(build / 'Scenario'), '-override=stopTime=0', '-outputFormat=empty',
                '-output=' + ','.join('plant.' + name for name in parameter_nodes)],
                cwd=build, capture_output=True, text=True, timeout=30)
            value_log = values.stdout + values.stderr
            (directory / 'parameter-values.log').write_text(value_log)
            if values.returncode or 'The simulation finished successfully' not in value_log:
                raise RuntimeError('Parameter initialization failed: ' + value_log[-2000:])
            runtime_values = dict(re.findall(r'(?:^|,)(plant\.[^=\r\n]+)=([^,\r\n]+)', values.stdout))
            for name, variable in parameter_nodes.items():
                value = runtime_values.get('plant.' + name)
                if value is None:
                    raise RuntimeError('Missing initialized parameter: ' + name)
                value_type = next(iter(variable)).tag
                if value_type == 'Real':
                    value = float(value)
                    if not math.isfinite(value):
                        raise RuntimeError('Non-finite parameter: ' + name)
                elif value_type == 'Integer':
                    value = int(value)
                elif value_type == 'Boolean':
                    value = bool(int(value))
                resolved[name] = {'value': value, 'description': variable.get('description', '')}
        (directory / 'resolved-parameters.json').write_text(json.dumps(resolved, indent=2) + '\n')
    with (directory / 'native.csv').open() as handle:
        rows = [{key.removeprefix('plant.'): float(value) for key, value in row.items() if key}
                for row in csv.DictReader(handle)]
    if not rows or any(not math.isfinite(value) for row in rows for value in row.values()):
        raise RuntimeError(f'Empty or non-finite native result: {directory / "native.csv"}')
    return rows


def at_year(rows, year):
    matches = [r for r in rows if abs(r['time'] - year * YEAR_SECONDS) < 0.01]
    if not matches:
        raise ValueError(f'Missing annual boundary {year}')
    return matches[-1]  # Post-event stocks; cumulative flows are continuous.


def annual_rows(rows, years, *, base_year=2025):
    n = sum(bool(re.fullmatch(r'services.staff\[\d+\]', key)) for key in rows[0])
    records = []
    for year in range(1, years + 1):
        before, now = at_year(rows, year - 1), at_year(rows, year)
        record = {'year': base_year + year, 'elapsedYears': year}
        record.update({key: now[key] for key in ('population', 'debt', 'cash', 'assets', 'workInProgress', 'balanceResidual')})
        record.update({name: now[key] - before[key] for name, key in FLOW_COLUMNS.items()})
        # Frozen v2 has no extra-cost component. Do not manufacture observations
        # when reading its old CSV, or silently accept a partially present bridge.
        extra_keys = set(EXTRA_FLOW_COLUMNS.values()) | {'finance.extraAccrualBalance'}
        if extra_keys & now.keys():
            if not extra_keys <= now.keys() or not extra_keys <= before.keys():
                raise ValueError('Incomplete additional-cost cash bridge in native results')
            record.update({name: now[key]-before[key] for name, key in EXTRA_FLOW_COLUMNS.items()})
            record['extraAccrualBalance'] = now['finance.extraAccrualBalance']
        tax_keys = set(TAX_CASH_COLUMNS.values()) | {'taxReceivable'}
        if tax_keys & now.keys():
            if not tax_keys <= now.keys() or not tax_keys <= before.keys():
                raise ValueError('Incomplete tax receivable cash bridge in native results')
            record.update({name: now[key]-before[key] for name, key in TAX_CASH_COLUMNS.items()})
            record['taxReceivable'] = now['taxReceivable']
        for i in range(1, n + 1):
            for name, key in (('staff', 'services.staff'), ('capacity', 'capital.capacity'), ('demand', 'demand')):
                record[f'{name}{i}'] = now[f'{key}[{i}]']
            record[f'unmetService{i}'] = now[f'cumulativeUnmet[{i}]'] - before[f'cumulativeUnmet[{i}]']
            for label, variable in (('annualDemand', 'cumulativeDemand'), ('purchasedService', 'cumulativePurchased'),
                                    ('payroll', 'cumulativePayrollByService'), ('otherExpense', 'cumulativeOtherByService')):
                record[f'{label}{i}'] = now[f'{variable}[{i}]'] - before[f'{variable}[{i}]']
            record[f'unmetShare{i}'] = record[f'unmetService{i}'] / record[f'annualDemand{i}'] if record[f'annualDemand{i}'] else 0
        records.append(record)
    return records


def write_report(directory, scenario, annual, overrides):
    def table(columns):
        headings = ''.join('<th>' + html.escape(label) + '</th>' for _, label in columns)
        body = ''.join('<tr>' + ''.join('<td>' + (str(int(row[key])) if key == 'year' else f'{row[key]:,.2f}')
                                      + '</td>' for key, _ in columns) + '</tr>' for row in annual)
        return '<div class="scroll"><table><tr>' + headings + '</tr>' + body + '</table></div>'
    financial = table([('year', 'År'), ('population', 'Invånare vid årets slut'), ('result', 'Årets resultat'),
                       ('transitionExpense', 'Omställningskostnad'), ('operatingCash', 'Driftens kassaflöde'), ('investment', 'Investering'),
                       ('debt', 'Skuld vid årets slut'), ('cash', 'Kassa vid årets slut')])
    extra_table = ''
    if 'extraExpense' in annual[0]:
        extra_table = '<h2>Extra kostnader och betalningar</h2><p>Nominella tillägg utöver övriga kostnader. Positivt periodiseringssaldo betyder ännu obetald kostnad; negativt betyder förskottsbetalning. Saldot avser endast dessa tillägg sedan simuleringens start.</p>' + table([
            ('year', 'År'), ('extraExpense', 'Kostnad'), ('extraPayments', 'Betalning'),
            ('extraAccrualBalance', 'Periodiseringssaldo vid årets slut')])
    service_tables = ''
    tax_table = ''
    if 'taxPayments' in annual[0]:
        tax_table = '<h2>Skatt och betalning</h2><p>Positiv skattefordran är bokförd intäkt som ännu inte betalats. Negativt saldo är nettoskatteskuld. Öppningssaldo och betalningsplan är scenarioantaganden om inget annat underlag anges.</p>' + table([
            ('year', 'År'), ('tax', 'Bokförd skatteintäkt'), ('taxSettlement', 'Varav separat avräkning'),
            ('taxPayments', 'Inbetald skatt, netto'), ('taxReceivable', 'Skattefordran vid årets slut')])
    for i in range(1, 1 + sum(re.fullmatch(r'staff\d+', key) is not None for key in annual[0])):
        label = {1: 'Utbildning', 2: 'Äldreomsorg', 3: 'Övrigt'}.get(i, f'Verksamhet {i}')
        service_tables += '<h3>' + label + '</h3>' + table([
            ('year', 'År'), (f'demand{i}', 'Behov vid årets slut'),
            (f'staff{i}', 'Årsarbetare vid årets slut'), (f'capacity{i}', 'Kapacitet vid årets slut'),
            (f'purchasedService{i}', 'Årets köpta service'), (f'unmetService{i}', 'Årets otillgodosedda behov'),
            (f'payroll{i}', 'Årets personal­kostnad'), (f'otherExpense{i}', 'Årets övriga kostnad')])
    document = f'''<!doctype html><html lang="sv"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Motala: dynamiskt scenario</title>
<style>body{{font:17px/1.5 system-ui;max-width:1150px;margin:2rem auto;padding:0 1rem;color:#183042}}
table{{border-collapse:collapse;width:100%}}td,th{{padding:.5rem;border-bottom:1px solid #ccd6dc;text-align:right}}
.scroll{{overflow-x:auto}}.notice{{background:#fff2d1;padding:1rem}}pre{{white-space:pre-wrap}}</style>
<h1>Motala: dynamiskt scenario</h1><p>Scenario: {html.escape(scenario)}. Utgångspunkt: 31 december 2025.</p>
<p>Grundscenario före parameterändringar: {html.escape(SCENARIO_DESCRIPTIONS[scenario])}</p>
<p class="notice">Forskningsprototyp med scenarioantaganden. Sektorandelar, initial personal,
kapacitet och anpassningstider är ännu inte skattade för Motala. Resultaten visar mekanismer;
ingen prognosöverlägsenhet eller oberoende SKR-jämförelse är visad.</p>
<h2>Ekonomi</h2><p>Belopp i mnkr. Årsflöden är integrerade över hela året.</p>{financial}
{extra_table}
{tax_table}
<h2>Behov, faktisk bemanning och kapacitet</h2>
<p>Service mäts i demografiska ekvivalenter. Dessa tal är inte observerade elever eller brukare.
Köpt service kan begränsas av leverantörernas kapacitet. Grundscenariot antar obegränsad
tillgång; supply-constraint aktiverar begränsningarna. Personalens ökning och minskning
kan också begränsas i årsarbetare per år.</p>{service_tables}
<h2>Ändrade parametrar och konstanta indata</h2><pre>{html.escape(json.dumps(overrides, ensure_ascii=False, indent=2))}</pre>
<p>Samtliga standardvärden: <a href="source/MotalaDynamics/Parameters.mo">Parameters.mo</a>.
Tidsberoende scenariobindningar: <a href="source/MotalaDynamics/Examples.mo">Examples.mo</a>.</p>
<p><a href="native/resolved-parameters.json">Faktiska parametervärden efter beräkning av beroenden</a>.</p>
<p>Källstatus i parameterunderlaget avser standardvärdena; egna ändringar redovisas ovan.</p>
<p><a href="annual.csv">Årsvärden CSV</a> · <a href="annual.json">Årsvärden JSON</a> ·
<a href="native/Scenario.mo">Körscenario</a> · <a href="native/native.csv">Alla tillstånd</a> ·
<a href="equations.md">Ekvationer och källor</a> · <a href="evidence.json">Parameterunderlag</a> ·
<a href="manifest.json">Versioner och kontroller</a></p></html>'''
    (directory / 'report.html').write_text(document, encoding='utf-8')


def resolved_revenue_modes(native_directory):
    """Report effective Modelica settings, including inherited scenario modifiers."""
    resolved = json.loads((Path(native_directory) / 'resolved-parameters.json').read_text())
    modes = {}
    for field, parameter in (('externalRevenue', 'useExternalRevenue'),
                             ('externalTax', 'useExternalTax')):
        entry = resolved.get(parameter) if isinstance(resolved, dict) else None
        value = entry.get('value') if isinstance(entry, dict) else None
        if type(value) is not bool:
            raise ValueError('Missing or non-boolean resolved parameter: ' + parameter)
        modes[field] = value
    return modes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=SCENARIOS, default='base')
    parser.add_argument('--years', type=int, default=8)
    parser.add_argument('--parameters', type=Path, help='JSON object of parameter or constant input overrides')
    parser.add_argument('--output', type=Path, help='New/empty output directory; existing runs are preserved')
    args = parser.parse_args(argv)
    if not 1 <= args.years <= 100:
        parser.error('--years must be 1 to 100')
    try:
        overrides = json.loads(args.parameters.read_text()) if args.parameters else {}
        source = scenario_source(args.scenario, overrides)
        omc = compiler()
        output = args.output or ROOT / 'runs' / ('dynamics-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        if output.exists() and any(output.iterdir()):
            raise ValueError('Preserve the existing run; choose a new --output directory')
        output.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / 'MotalaDynamics', output / 'source/MotalaDynamics')
        (output / 'source/data').mkdir()
        for name in ('baseline.json', 'history.json', 'operating-accounts-history.json', 'sources.json'):
            shutil.copy2(ROOT.parent / 'data' / name, output / 'source/data' / name)
        shutil.copy2(ROOT / 'dynamics-equations.md', output / 'equations.md')
        shutil.copy2(ROOT / 'data/dynamics-evidence.json', output / 'evidence.json')
        shutil.copy2(__file__, output / 'source/dynamics.py')
        (output / 'parameters.json').write_text(json.dumps(overrides, indent=2) + '\n')
        rows = simulate(source, args.years, output / 'native', package=output / 'source/MotalaDynamics/package.mo')
        # Validate before writing results, so a failed run leaves no report that looks finished.
        residuals = {name: max(abs(row[name]) for row in rows) for name in
                     ('balanceResidual', 'demography.populationResidual', 'finance.cashResidual', 'finance.debtResidual')}
        if max(residuals.values()) > 1e-3:
            raise ArithmeticError('Native balance validation failed: ' + str(residuals))
        annual = annual_rows(rows, args.years)
        (output / 'annual.json').write_text(json.dumps(annual, indent=2) + '\n')
        with (output / 'annual.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(annual[0]))
            writer.writeheader(); writer.writerows(annual)
        write_report(output, args.scenario, annual, overrides)
        manifest = {'model': 'MotalaDynamics-v3', 'scenario': args.scenario, 'years': args.years,
                    'baseYear': 2025, 'simulationTimeUnit': 'second', 'yearSeconds': YEAR_SECONDS,
                    'moneyUnit': 'mnkr', 'flowReporting': 'annual integrals',
                    'status': 'native_balances_checked_scenario_not_forecast_validated',
                    **resolved_revenue_modes(output / 'native'),
                    'overrides': overrides, 'maximumAbsoluteBalanceResiduals': residuals,
                    'compiler': subprocess.check_output([omc, '--version'], text=True).strip(),
                    'artifacts': {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(output.rglob('*')) if p.is_file()}}
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps({'report': str((output / 'report.html').resolve()),
                          'annualCSV': str((output / 'annual.csv').resolve()),
                          'balanceResiduals': residuals}, indent=2))
    except (OSError, ValueError, ArithmeticError, RuntimeError, subprocess.SubprocessError, ET.ParseError) as exc:
        raise SystemExit(str(exc))


if __name__ == '__main__':
    main()
