#!/usr/bin/env python3
"""Turn the archived SCB tables into the demography inputs the Modelica model uses.

    python3 scripts/prepare_demography.py data/downloads/<archive>

Reads an archive written by fetch_mortality_data.py, checks every file against its
manifest, and writes data/demography-inputs.json. Källa: SCB (CC BY 4.0); the output
names each table it uses.

Ages are single years 0..100, where 100 means 100 and older. Sex 1 = men, 2 = women.

Derived quantities, and how:
- Death risk q(age, sex) per year from SCB's national life table (per mille -> fraction).
  The open group 100+ uses 1/e(100), the death rate of a stationary open age group.
- One calibration per base year 2020-2025, using data up to that year only, so a forecast
  from an earlier base year can be checked against what happened next:
  - Motala's mortality ratio: observed deaths / expected deaths, where expected deaths apply
    the national q of the same year to Motala's population at the start of the year. Pooled
    over the five years ending in the base year, per sex.
  - Residual migration by age and sex: population change not explained by deaths, ageing
    and births, averaged over the three transitions ending in the base year. Like the
    five-cohort model's, it includes statistical adjustments; it is not observed migration.
  - Share of boys at birth: Motala births over the ten years ending in the base year.
  - Mortality trend: the annual decline in national log death risk over the ten years ending
    in the base year, per sex and age band (0-14, 15-49, 50-64, 65-79, 80-89, 90+).
  - Death risk at the base year: each of the five latest life tables moved along that trend
    to the base year, then averaged, so one unusual year (2020, 2022) does not set the level.
- SCB's projected mortality improvement: the annual rate at which SCB's projected death rates
  decline over the projection's first nine years, by age and sex. From the 2025 projection,
  so only a 2025 base year may use it; an alternative to the historical trend.
- Fertility profile: SCB's projected age-specific fertility for the first projection year,
  normalised to sum to one. Births = TFR * profile * women at each age.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGES = 101
SEXES = ('1', '2')


def load(archive, name, manifest):
    path = archive / f'{name}.json'
    entry = next(f for f in manifest['files'] if f['file'] == path.name)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise SystemExit(f'{path} does not match its manifest')
    table = json.loads(data)
    keys = [c['code'] for c in table['columns'] if c['type'] != 'c']
    contents = [c for c in table['columns'] if c['type'] == 'c']
    rows = []
    for row in table['data']:
        key = dict(zip(keys, row['key']))
        for column, value in zip(contents, row['values']):
            rows.append({**key, 'content': column['text'], 'value': value})
    return rows, entry['url']


def age_index(code):
    """'0'..'99' -> 0..99; '100+', '100+1', '105+' and the like -> 100; totals and ranges -> None."""
    if code.startswith('100+') or code == '105+':
        return 100
    return min(int(code), 100) if code.isdigit() else None


def number(value):
    try:
        return float(value)
    except ValueError:
        return None


def by_age(rows):
    """{year: {sex: [AGES values]}}, summed over any other variables (e.g. civil status)."""
    result = {}
    for r in rows:
        a, v = age_index(r['Alder']), number(r['value'])
        if a is None or v is None:
            continue
        result.setdefault(int(r['Tid']), {s: [0.0] * AGES for s in SEXES})[r['Kon']][a] += v
    return result


def natural_step(pop, q_year, births_total, boys):
    """One year of survival and ageing; births enter age 0. Matches Motala.Components.CohortDemography."""
    nxt = {s: [0.0] * AGES for s in SEXES}
    for s in SEXES:
        survivors = [pop[s][a] * (1 - q_year[s][a]) for a in range(AGES)]
        for a in range(AGES - 1):
            nxt[s][a + 1] += survivors[a]
        nxt[s][100] += survivors[100]
    nxt['1'][0] += births_total * boys
    nxt['2'][0] += births_total * (1 - boys)
    return nxt


def fertility_profiles(national):
    """Use the observed Swedish age-specific rates available at each earlier base year."""
    archive = ROOT / national['archive']
    manifest = json.loads((archive / 'manifest.json').read_text())
    rows, _ = load(archive, 'fertility-rates-sweden', manifest)
    values = {}
    for row in rows:
        ages = row['AlderModer'].split('-')
        if len(ages) != 2 or not all(a.isdigit() for a in ages):
            continue
        profile = values.setdefault(int(row['Tid']), [0.] * 101)
        for age in range(int(ages[0]), int(ages[1]) + 1):
            profile[age] = float(row['value'])
    return {year: [v / sum(values[year]) for v in values[year]] for year in values}


def calibrate(population, deaths, births, tfr, q, base_years):
    """Prepare one cohort record per base year, using only observations through that year."""
    # Mortality trend from the life tables: annual decline in log death risk over the ten years
    # ending in the base year, per sex and age band (single ages are too noisy at young ages).
    bands = [(0, 15), (15, 50), (50, 65), (65, 80), (80, 90), (90, 101)]

    def trend(base, sex):
        years = list(range(base - 9, base + 1))
        rate = [0.0] * AGES
        for lo, hi in bands:
            logs = [math.log(sum(q[y][sex][lo:hi]) / (hi - lo)) for y in years]
            mean_t, mean_l = sum(years) / len(years), sum(logs) / len(logs)
            slope = (sum((t - mean_t) * (l - mean_l) for t, l in zip(years, logs))
                     / sum((t - mean_t) ** 2 for t in years))
            for a in range(lo, hi):
                rate[a] = -slope
        return rate

    # One calibration per base year, from data up to and including that year only.
    calibration = {}
    for base in base_years:
        window = range(base - 4, base + 1)
        improvement_base = {s: trend(base, s) for s in SEXES}
        # Death risk at the base year: the last five years moved along the trend and averaged,
        # so a single unusual year (2020, 2022) does not set the level.
        level = {s: [min(1.0, sum(q[y][s][a] * math.exp(-improvement_base[s][a] * (base - y)) for y in window) / 5)
                     for a in range(AGES)] for s in SEXES}
        ratio = {}
        for sex in SEXES:
            observed = sum(deaths[y][sex] for y in window)
            expected = sum(population[y - 1][sex][a] * q[y][sex][a] for y in window for a in range(AGES))
            ratio[sex] = observed / expected
        past = [y for y in births if base - 9 <= y <= base]
        boys = sum(births[y]['1'] for y in past) / sum(births[y]['1'] + births[y]['2'] for y in past)
        residuals = []
        for y in range(base - 2, base + 1):
            scaled = {s: [min(1.0, q[y][s][a] * ratio[s]) for a in range(AGES)] for s in SEXES}
            expected = natural_step(population[y - 1], scaled, births[y]['1'] + births[y]['2'], boys)
            residuals.append({s: [population[y][s][a] - expected[s][a] for a in range(AGES)] for s in SEXES})
        calibration[str(base)] = {
            'population': population[base],
            'deathRisk': level,
            'mortalityImprovement': improvement_base,
            'mortalityRatio': [ratio['1'], ratio['2']],
            'mortalityWindow': [window[0], window[-1]],
            'residualMigration': {s: [sum(r[s][a] for r in residuals) / 3 for a in range(AGES)] for s in SEXES},
            'migrationTransitions': [base - 2, base],
            'shareBoys': boys,
            'totalFertility': tfr[base],
            'totalFertilityMean5': sum(tfr[y] for y in window) / 5,
            'births': births[base]['1'] + births[base]['2'],
            'deaths': sum(deaths[base].values()),
        }

    return calibration


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    manifest = json.loads((archive / 'manifest.json').read_text())
    sources = {}

    def table(name):
        rows, url = load(archive, name, manifest)
        sources[name] = url
        return rows

    # Population at the end of each year and deaths during it, single ages by sex.
    population = by_age(table('motala-population-2015-2024'))
    population.update(by_age(table('motala-population-2025')))
    deaths = by_age(table('motala-deaths-2015-2024'))
    deaths.update(by_age(table('motala-deaths-2025')))

    # National life table: q per mille and remaining life expectancy, ages 0..110.
    q, e100 = {}, {}
    for r in table('life-table'):
        year, sex, v = int(r['Tid']), r['Kon'], number(r['value'])
        a = int(r['Alder'].split()[0])
        if r['content'].startswith('Dödsrisker') and a < 100:
            q.setdefault(year, {s: [0.0] * AGES for s in SEXES})[sex][a] = v / 1000
        elif r['content'].startswith('Återstående') and a == 100:
            e100.setdefault(year, {})[sex] = v
    for year in q:
        for sex in SEXES:
            q[year][sex][100] = min(1.0, 1 / e100[year][sex])

    births = {}
    for name in ('motala-births-2015-2024', 'motala-births-2025'):
        for r in table(name):
            if r['AlderModer'] in ('tot', 'TotSA') and r['Kon'] in SEXES:
                births.setdefault(int(r['Tid']), {})[r['Kon']] = number(r['value'])

    tfr = {}
    for r in table('total-fertility'):
        if r['Kon'] == '2' and number(r['value']) is not None:
            tfr.setdefault(r['Region'], {})[int(r['Tid'])] = number(r['value'])

    # SCB's latest projection: mortality trend and fertility. Published 2025, so only the
    # 2025 base year may use them; earlier base years would see the future.
    projected = by_age(table('projected-death-rates'))
    first = min(projected)
    later = first + 9
    improvement = {s: [(-math.log(projected[later][s][a] / projected[first][s][a]) / (later - first))
                       if projected[first][s][a] > 0 and projected[later][s][a] > 0 else 0.0
                       for a in range(AGES)] for s in SEXES}
    profile = [0.0] * AGES
    projected_tfr = {}
    for r in table('projected-fertility'):
        code, year, v = r['Alder'], int(r['Tid']), number(r['value'])
        if code == 'tot' or v is None:
            continue
        projected_tfr[year] = projected_tfr.get(year, 0) + v  # births per woman at each age
        if year == first:
            profile[15 if code.startswith('-') else 49 if code.endswith('+') else int(code)] += v
    profile = [x / sum(profile) for x in profile]

    death_totals = {year: {sex: sum(counts) for sex, counts in row.items()} for year, row in deaths.items()}
    calibration = calibrate(population, death_totals, births, tfr['0583'], q, range(2020, 2026))

    # SCB's regional projection for Motala, as a benchmark.
    projection = {}
    for r in table('scb-projection-motala'):
        v = number(r['value'])
        if v is not None:
            item = projection.setdefault(int(r['Tid']), {})
            item[r['content']] = item.get(r['content'], 0) + v

    result = {
        'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0)',
        'archive': str(archive.relative_to(ROOT)),
        'tables': sources,
        'ages': 'single years 0..100, where 100 is 100 and older; sex 1 = men, 2 = women',
        'baseYears': calibration,
        'mortalityImprovement': {'from': [first, later], 'note': 'annual rate of decline in SCB projected death rates',
                                 'bySex': improvement},
        'fertilityProfile': {'year': first, 'shares': profile},
        'projectedTotalFertility': {str(y): projected_tfr[y] for y in sorted(projected_tfr)},
        'totalFertility': {'Sweden': tfr['00'], 'Motala': tfr['0583']},
        'observed': {'population': {str(y): population[y] for y in sorted(population)},
                     'deaths': {str(y): deaths[y] for y in sorted(deaths)},
                     'births': {str(y): births[y] for y in sorted(births)}},
        'lifeTableDeathRisk': {str(y): q[y] for y in sorted(q)},
        'scbProjectionMotala': {str(y): projection[y] for y in sorted(projection)},
    }
    target = ROOT / 'data/demography-inputs.json'
    target.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
    for base, c in calibration.items():
        print(f'{base}: mortality ratio men {c["mortalityRatio"][0]:.3f} women {c["mortalityRatio"][1]:.3f}, '
              f'residual migration {sum(c["residualMigration"]["1"]) + sum(c["residualMigration"]["2"]):7.1f}/yr, '
              f'TFR {c["totalFertility"]:.2f} (5-yr {c["totalFertilityMean5"]:.2f}), boys {c["shareBoys"]:.3f}')
    print(f'projected TFR {first}: {projected_tfr[first]:.3f}; wrote {target.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
