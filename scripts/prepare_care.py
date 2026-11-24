#!/usr/bin/env python3
"""Care cost per inhabitant by age group, from archived Kolada data for a municipality.

    python3 scripts/prepare_care.py data/downloads/<archive> [--output path]

Reads an archive written by fetch_care_data.py, checks it against its manifest and writes
data/care-weights.json. Källa: Kolada (RKA); statistics from Socialstyrelsen and SCB.

For each year and age group g (65-79, 80+):

    cost per inhabitant(g) = home-care users(g) / inhabitants(g) * cost per home-care user
                           + residential-care users(g) / inhabitants(g) * cost per residential place

- Cost per home-care user = home-care cost per inhabitant 65+ (N21009) * inhabitants 65+
  / home-care users 65+ (N21702). The same cost per user is assumed at every age.
- Cost per residential place = N23009 (kr per user).
- Users: N21703/N21705 (home care), N23807/N23806 (residential care); inhabitants N01956/N01957.

Each base year uses the mean of the three years ending in it. Kolada has no split of 80+;
the model's default gives 80-89 and 90+ the same cost per inhabitant.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/care-weights.json')
    args = parser.parse_args()
    archive = args.archive.resolve()
    manifest = json.loads((archive / 'manifest.json').read_text())
    entry = next(f for f in manifest['files'] if f['file'].startswith('kolada-care-') and 'metadata' not in f['file'])
    raw = (archive / entry['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise SystemExit(f"{entry['file']} does not match its manifest")
    series = {}
    for item in json.loads(raw)['values']:
        total = [x['value'] for x in item['values'] if x['gender'] == 'T' and x['value'] is not None]
        if total:
            series.setdefault(item['kpi'], {})[item['period']] = total[0]

    needed = ['N21009', 'N21702', 'N21703', 'N21705', 'N23009', 'N23807', 'N23806', 'N01956', 'N01957']
    yearly = {}
    for year in range(2015, 2026):
        if not all(year in series.get(k, {}) for k in needed):
            continue
        v = {k: series[k][year] for k in needed}
        inhabitants65 = v['N01956'] + v['N01957']
        home_per_user = v['N21009'] * inhabitants65 / v['N21702']
        residential_per_user = v['N23009']
        groups = {'65-79': ('N21703', 'N23807', 'N01956'), '80+': ('N21705', 'N23806', 'N01957')}
        yearly[year] = {
            'homeCarePerUser': home_per_user,
            'residentialCarePerUser': residential_per_user,
            **{g: {'homeCareShare': v[h] / v[p], 'residentialShare': v[r] / v[p],
                   'costPerInhabitant': (v[h] * home_per_user + v[r] * residential_per_user) / v[p]}
               for g, (h, r, p) in groups.items()}}

    bases = {}
    for base in range(2017, 2026):
        years = [y for y in (base - 2, base - 1, base) if y in yearly]
        if not years:
            continue
        mean = {g: sum(yearly[y][g]['costPerInhabitant'] for y in years) / len(years) for g in ('65-79', '80+')}
        bases[str(base)] = {'years': years, 'costPerInhabitant': mean, 'ratio80to6579': mean['80+'] / mean['65-79']}

    out = {'source': 'Källa: Kolada (RKA), Socialstyrelsen och SCB', 'archive': str(archive.relative_to(ROOT)),
           'kpis': {k: v for k, v in json.loads((archive / 'kolada-care-kpi-metadata.json').read_text()).items()
                    if k == 'values'},
           'method': __doc__.split('For each year', 1)[1].strip(),
           'yearly': {str(y): yearly[y] for y in sorted(yearly)}, 'baseYears': bases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    for base, b in bases.items():
        print(f'{base}: kr per inhabitant 65-79 {b["costPerInhabitant"]["65-79"]:8.0f}, '
              f'80+ {b["costPerInhabitant"]["80+"]:8.0f}, ratio {b["ratio80to6579"]:.2f} ({b["years"][0]}-{b["years"][-1]})')


if __name__ == '__main__':
    main()
