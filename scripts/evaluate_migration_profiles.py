"""Cross-municipality sensitivity with the same age-income mechanics and fixed reference amounts."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
income = json.loads((root / 'data/age-income.json').read_text())
cases = []
with tempfile.TemporaryDirectory(prefix='motala-age-regions-') as directory:
    folder = Path(directory)
    models = []
    for municipality, package in [('0583', 'Motala'), ('0586', 'Mjolby')]:
        rates = '{' + ','.join(map(str, income['municipalities'][municipality]['2024'])) + '}'
        for profile, weights in [('Work', '{0,0,0,1,0}'), ('Older', '{0,0,0,0,1}')]:
            name = package + profile
            models.append(f'''model {name}
  extends {package}.Continuous(horizon=2, importedRevenue=true, importedRevenueMode=2,
    migrationWeights={weights}, migrationDeltaPath={{100,100}},
    ageIncomeWeights={rates}, equalisationCountyRate={income['countyRate']},
    referenceTax=fill(tax0,2), referenceGrants=fill(grants0,2), referencePopulation=fill(sum(p0),2),
    importedComponents=[tax0,grantComponents0[1],grantComponents0[3]; tax0,grantComponents0[1],grantComponents0[3]]);
end {name};''')
            cases.append((municipality, profile, name))
    (folder/'test.mo').write_text('\n'.join(models))
    (folder/'test.mos').write_text(''.join(
        f'loadFile({json.dumps(str(file))}); getErrorString();\n' for file in [
        root/'modelica/Kommunekonomi.mo', root/'modelica/municipalities/Motala.mo',
        root/'modelica/municipalities/Mjolby.mo', folder/'test.mo']) + '\n'.join(
        f'simulate({name},startTime=2025,stopTime=2027,numberOfIntervals=24,outputFormat="csv",'
        f'variableFilter="tax|grants|population|careIndex"); getErrorString();'
        for _, _, name in cases))
    command = subprocess.run([shutil.which('omc'),'test.mos'],cwd=folder,capture_output=True,text=True,timeout=150)
    if not all((folder/f'{case[2]}_res.csv').exists() for case in cases):
        raise RuntimeError(command.stdout + command.stderr)
    metrics = ('tax','grants','population','careIndex')
    output = {}
    for municipality, profile, name in cases:
        rows = list(csv.DictReader((folder/f'{name}_res.csv').open()))
        first = [r for r in rows if abs(float(r['time'])-2026)<1e-9][-1]
        last = rows[-1]
        output[municipality,profile] = {**{k:float(last[k]) for k in metrics},'population2026':float(first['population'])}
    for municipality in ('0583','0586'):
        a,b = (output[municipality,k] for k in ('Work','Older'))
        assert abs(a['population2026']-b['population2026'])<5  # arrivals of different ages die at different rates during the year
        assert a['tax']>b['tax'] and a['grants']<b['grants'] and a['careIndex']<b['careIndex']
        print(municipality,{k:round(a[k]-b[k],6) for k in a})
