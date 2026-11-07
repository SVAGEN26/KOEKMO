"""Import reviewed municipal observations from a CSV and an explicit column map.

Usage: python3 -m motala_lab.import_csv INPUT.csv MAP.json OUTPUT.json

MAP requires scope, moneyUnit, definitions, evidenceClass, columns, source,
vintage and retrievedAt; sourceRelease may be null in retrospective mode.
columns maps canonical metric names, municipality and year to CSV headers.
Optional scales maps financial fields to explicit conversion multipliers.
Optional cohortColumns lists exactly five population columns in age order.
No file is written unless the entire normalized observation set validates.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from .data import METRICS,validate


def convert(text,mapping):
    if mapping.get('role')=='benchmark_only' or mapping.get('usesBenchmarkOutputs'):
        raise ValueError('Benchmark outputs are not observed training data')
    columns=mapping['columns'];rows=[]
    for raw in csv.DictReader(text.splitlines()):
        row={'municipality':raw[columns['municipality']].strip().zfill(4),
             'year':int(raw[columns['year']]),'source':mapping['source'],
             'vintage':mapping['vintage'],'retrievedAt':mapping['retrievedAt'],
             'sourceRelease':raw[columns['sourceRelease']] if 'sourceRelease' in columns else mapping.get('sourceRelease')}
        for metric in (*METRICS,'births','deaths','netMigration','accountingAdjustment'):
            if metric not in columns:
                continue
            value=raw[columns[metric]].strip()
            if value=='':raise ValueError(f'Missing {metric}; blanks cannot become zeros')
            row[metric]=float(value)*mapping.get('scales',{}).get(metric,1)
        if mapping.get('cohortColumns'):
            if len(mapping['cohortColumns'])!=5:raise ValueError('Exactly five cohort columns required')
            row['cohorts']=[float(raw[c]) for c in mapping['cohortColumns']]
        rows.append(row)
    data={k:mapping[k] for k in ('scope','moneyUnit','definitions','evidenceClass')}
    data.update(schemaVersion=1,rows=rows)
    if 'evaluationOrigins' in mapping:data['evaluationOrigins']=mapping['evaluationOrigins']
    return validate(data)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',type=Path);parser.add_argument('mapping',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    try:normalized=convert(args.csv.read_text(),json.loads(args.mapping.read_text()))
    except (ValueError,KeyError,TypeError) as exc:raise SystemExit(f'Import rejected: {exc}')
    args.output.write_text(json.dumps(normalized,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
