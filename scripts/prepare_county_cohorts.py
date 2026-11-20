"""Prepare the shared cohort model's municipal input records from archived SCB data."""
import json
from pathlib import Path

from prepare_demography import ROOT, by_age, calibrate, fertility_profiles, load
from write_demography_modelica import cohort_records


def county_cohorts(code, population_archive, years, base_years=(2024, 2025)):
    sources = json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())
    if 'cohortArchive' not in sources:
        return {}
    archive = ROOT / sources['cohortArchive']
    manifest = json.loads((archive / 'manifest.json').read_text())
    if code not in manifest['municipalities']:
        return {}

    def vital_counts(name):
        result = {}
        for suffix in ('2015-2024', '2025'):
            rows, _ = load(archive, name + '-' + suffix, manifest)
            for row in rows:
                if row['Region'] == code:
                    result.setdefault(int(row['Tid']), {})[row['Kon']] = float(row['value'])
        return result

    pop_manifest = json.loads((population_archive / 'manifest.json').read_text())
    population = {}
    for name in ('population-2017-2024', 'population-2025'):
        rows, _ = load(population_archive, name, pop_manifest)
        population.update(by_age(rows))
    for year, book in years.items():
        total = sum(sum(ages) for ages in population[year].values())
        factor = book['reportedPopulation'][-1] / total
        population[year] = {sex: [count * factor for count in ages]
                            for sex, ages in population[year].items()}

    national = json.loads((ROOT / 'data/demography-inputs.json').read_text())
    q = {int(y): rows for y, rows in national['lifeTableDeathRisk'].items()}
    profiles = fertility_profiles(national)
    births, deaths = vital_counts('births'), vital_counts('deaths')
    rows, _ = load(archive, 'total-fertility', manifest)
    tfr = {int(row['Tid']): float(row['value']) for row in rows
           if row['Region'] == code and row['value'] not in ('..', '')}
    for year in range(min(base_years) - 4, max(base_years) + 1):
        if year not in tfr:
            # Estimate a rate from births and local exposure when SCB suppresses TFR.
            exposure = sum(weight * (before + after) / 2 for weight, before, after in
                           zip(profiles[year], population[year - 1]['2'], population[year]['2'], strict=True))
            tfr[year] = sum(births[year].values()) / exposure
    return calibrate(population, deaths, births, tfr, q, base_years)


def modelica_cohorts(code, package, name, archive, years):
    records = county_cohorts(code, ROOT / archive, years)
    if not records:
        return ''
    constants = '\n'.join(cohort_records(name, package.lower(), records))
    indented = '\n'.join('  ' + line for line in constants.splitlines())
    return f"""    package SCB "{name}s demografi per ettårsålder och kön"
      extends Kommunekonomi.Data.SCB;
{indented}
    end SCB;
"""
