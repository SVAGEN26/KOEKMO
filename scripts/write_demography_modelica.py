#!/usr/bin/env python3
"""Write data/demography-inputs.json into the two SCB packages.

    python3 scripts/write_demography_modelica.py

Kommunekonomi.Data.SCB (modelica/Kommunekonomi.mo) gets what is the same for every
municipality: the record type, Sweden's population, fertility and mortality, and the
helper functions. Motala.Data.SCB (modelica/Motala.mo) extends it with Motala's base
years. Each package is replaced in place. Run it after scripts/prepare_demography.py;
tests/test_demography.py checks that the files and the JSON agree.
"""
import json
import re
from pathlib import Path

from prepare_demography import fertility_profiles

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'modelica/Kommunekonomi.mo'
MUNICIPALITY = ROOT / 'modelica/Motala.mo'
NAME, PREFIX = 'Motala', 'motala'
HORIZON = 30  # years of projected fertility to carry, from the first projection year


def num(x, digits):
    text = f'{x:.{digits}g}'
    return '0' if text in ('0', '-0') else text


def vector(values, digits, per_line=None, indent=''):
    items = [num(v, digits) for v in values]
    if not per_line:
        return '{' + ', '.join(items) + '}'
    lines = [', '.join(items[i:i + per_line]) for i in range(0, len(items), per_line)]
    return '{' + (',\n' + indent).join(lines) + '}'


def by_sex(table, digits, indent):
    inner = indent + '  '
    return ('{' + vector(table['1'], digits, 17, inner) + ',\n' + indent + ' '
            + vector(table['2'], digits, 17, inner) + '}')


def cohort_records(name, prefix, calibration):
    pad = '      '
    years = []
    for base, c in sorted(calibration.items()):
        years.append(f'''    constant DemographyYear {prefix}{base} = DemographyYear(
      year = {base},
      population = {by_sex(c['population'], 6, pad + '  ')},
      deathRisk = {by_sex(c['deathRisk'], 6, pad + '  ')},
      mortalityImprovement = {by_sex(c['mortalityImprovement'], 4, pad + '  ')},
      mortalityRatio = {vector(c['mortalityRatio'], 6)},
      residualMigration = {by_sex(c['residualMigration'], 4, pad + '  ')},
      shareBoys = {num(c['shareBoys'], 6)},
      totalFertility = {num(c['totalFertility'], 4)},
      totalFertilityMean5 = {num(c['totalFertilityMean5'], 4)},
      births = {num(c['births'], 6)},
      deaths = {num(c['deaths'], 6)})
      "{name} vid slutet av {base}; dödlighetskvot {c['mortalityWindow'][0]}-{c['mortalityWindow'][1]}, restflöden {c['migrationTransitions'][0]}-{c['migrationTransitions'][1]}";''')
    return years


def packages(d, national, years, chain, first_base, last_base, first, tfr, improve, nat_years, nat_values, pad):
    fertility_years = sorted(int(y) for y in d['totalFertility']['Sweden'])
    fertility_values = [d['totalFertility']['Sweden'][str(y)] for y in fertility_years]
    """The national package for the library and the municipality's package that extends it."""
    profiles = fertility_profiles(d)
    historical_profiles = ',\n        '.join(vector(profiles[year], 8) for year in range(2021, 2025))
    tables = ', '.join(sorted(set(u.rsplit('/', 1)[1] for u in d['tables'].values())))
    library = f'''  package SCB "Rikets demografiska data från SCB och posttypen för en kommuns ettårsdata. Genereras av scripts/write_demography_modelica.py; redigera inte för hand"
    record DemographyYear "En kommun vid ett basårs slut, ettårsåldrar 0-100+ (index 1-101) per kön (1 män, 2 kvinnor)"
      Integer year "Basår";
      Units.Persons population[2, 101] "Befolkning vid årets slut";
      Real deathRisk[2, 101] "Rikets dödsrisk vid basåret: fem livslängdstabeller flyttade längs trenden och medelvärdesbildade, andel";
      Real mortalityImprovement[2, 101] "Årlig minskning av dödsrisken, rikets trend de tio åren fram till basåret";
      Real mortalityRatio[2] "Kommunens dödlighet i förhållande till rikets livslängdstabell, de fem åren fram till basåret";
      Real residualMigration[2, 101] "Genomsnittlig årlig förändring som inte förklaras av döda, åldrande och födda, de tre åren fram till basåret";
      Real shareBoys "Andel pojkar bland de födda, de tio åren fram till basåret";
      Real totalFertility "Kommunens summerade fruktsamhet basåret";
      Real totalFertilityMean5 "Kommunens genomsnittliga summerade fruktsamhet de fem åren fram till basåret";
      Units.Persons births "Födda under basåret";
      Units.Persons deaths "Döda under basåret";
      annotation(Icon(coordinateSystem(extent = {{{{-100, -100}}, {{100, 100}}}}), graphics = {{Rectangle(lineColor = {{40, 95, 140}}, fillColor = {{255, 255, 255}}, fillPattern = FillPattern.Solid, extent = {{{{-100, -100}}, {{100, 100}}}}), Rectangle(lineColor = {{40, 95, 140}}, fillColor = {{40, 95, 140}}, fillPattern = FillPattern.Solid, extent = {{{{-100, 50}}, {{100, 100}}}}), Text(textColor = {{255, 255, 255}}, extent = {{{{-92, 55}}, {{92, 95}}}}, textString = "SCB-år"), Line(points = {{{{-100, 0}}, {{100, 0}}}}, color = {{40, 95, 140}}), Line(points = {{{{-100, -50}}, {{100, -50}}}}, color = {{40, 95, 140}}), Line(points = {{{{0, 50}}, {{0, -100}}}}, color = {{40, 95, 140}})}}));
    end DemographyYear;

    constant Real fertilityProfile[101] = {vector(d['fertilityProfile']['shares'], 6, 12, pad + '  ')}
      "Andel av en kvinnas barn som föds vid varje ålder, SCB:s framskrivning {first}; summerar till 1";
    constant Real historicalFertilityProfile[4, 101] = {{{historical_profiles}}}
      "SCB:s historiska fruktsamhetstal för riket 2021–2024, jämnt fördelade inom moderns åldersgrupp och normaliserade";
    constant Integer projectionFirstYear = {first} "Första året i SCB:s framskrivning";
    constant Real projectedTotalFertility[{HORIZON}] = {vector(tfr, 5, 10, pad + '  ')}
      "Rikets summerade fruktsamhet enligt SCB:s antagande, {first}-{first + HORIZON - 1}";
    constant Real mortalityImprovement[2, 101] = {by_sex(improve['bySex'], 4, pad)}
      "Årlig minskning av dödsrisken per ålder och kön i SCB:s framskrivning {improve['from'][0]}-{improve['from'][1]}; ett alternativ till basårets historiska trend";
    constant Real deathRisk[2, 101] = {by_sex(d['baseYears'][str(last_base)]['deathRisk'], 6, pad)}
      "Rikets dödsrisk per ålder och kön {last_base}: fem livslängdstabeller flyttade längs trenden och medelvärdesbildade";
    constant Integer fertilityFirstYear = {fertility_years[0]} "Första året i tabellen över rikets summerade fruktsamhet";
    constant Real totalFertility[{len(fertility_years)}] = {vector(fertility_values, 4, 13, pad + '  ')}
      "Rikets summerade fruktsamhet {fertility_years[0]}-{fertility_years[-1]} (SCB)";

    function totalFertilityAt "Rikets summerade fruktsamhet ett år; det senaste kända året om året ligger efter tabellen"
      input Integer year "Kalenderår";
      output Real level "Barn per kvinna";
    algorithm
      level := totalFertility[min(max(year, fertilityFirstYear), fertilityFirstYear + size(totalFertility, 1) - 1) - fertilityFirstYear + 1];
    end totalFertilityAt;

    function totalFertilityMean5 "Rikets genomsnittliga summerade fruktsamhet de fem åren fram till ett år"
      input Integer year "Sista året";
      output Real mean "Medel av fem år";
    protected
      Integer last = min(max(year, fertilityFirstYear + 4), fertilityFirstYear + size(totalFertility, 1) - 1) - fertilityFirstYear + 1;
    algorithm
      // En slinga: OpenModelicas kodgenerering klarar inte ett snitt med dynamiska index ur en konstant tabell.
      mean := 0;
      for i in 0:4 loop
        mean := mean + totalFertility[last - i]/5;
      end for;
    end totalFertilityMean5;

    function combinedDeathRisk "Dödsrisk (rad 1) och dess årliga minskning (rad 2) per ålder för båda könen tillsammans"
      output Real combined[2, 101];
    protected
      Real alive[2] "Kvar i livet av lika många födda pojkar och flickor";
      Real weight "Männens andel vid åldern";
    algorithm
      alive := {{1, 1}};
      for a in 1:101 loop
        weight := alive[1]/(alive[1] + alive[2]);
        combined[1, a] := weight*deathRisk[1, a] + (1 - weight)*deathRisk[2, a];
        combined[2, a] := (weight*deathRisk[1, a]*mortalityImprovement[1, a] + (1 - weight)*deathRisk[2, a]*mortalityImprovement[2, a])/max(1e-12, combined[1, a]);
        alive := {{alive[1]*(1 - deathRisk[1, a]), alive[2]*(1 - deathRisk[2, a])}};
      end for;
    end combinedDeathRisk;

    function ages "Invånare per ettårsålder, båda könen"
      input Real population[2, 101] "Befolkning per ettårsålder och kön";
      output Real total[101];
    algorithm
      total := population[1, :] + population[2, :];
    end ages;

    function groups "Ettårsåldrar summerade till 0-6, 7-15, 16-18, 19-64 och 65+, båda könen"
      input Real population[2, 101] "Befolkning per ettårsålder och kön";
      output Real cohorts[5] "Invånare per åldersgrupp";
    algorithm
      cohorts := {{sum(population[:, 1:7]), sum(population[:, 8:16]), sum(population[:, 17:19]), sum(population[:, 20:65]), sum(population[:, 66:101])}};
    end groups;

    constant Integer nationalFirstYear = {nat_years[0]} "Första året i tabellen över rikets folkmängd";
    constant Real nationalPopulation[{len(nat_years)}] = {vector(nat_values, 9, 8, pad + '  ')}
      "Rikets folkmängd 31 december {nat_years[0]}-{nat_years[-1]}: utfall till {national['lastOutcome']}, sedan SCB:s framskrivning ({national['archive']})";

    constant Integer nationalLastOutcome = {national['lastOutcome']} "Sista året med utfall i tabellen över rikets folkmängd";

    function nationalPopulationAt "Rikets folkmängd 31 december ett visst år, som den var känd ett givet år"
      input Integer year "Kalenderår";
      input Integer knownAt = nationalLastOutcome "Året då uppgiften ska vara känd: ett basår före sista utfallsåret ser inte senare utfall";
      output Real population "Folkmängd";
    protected
      Integer known = min(max(knownAt, nationalFirstYear + 1), nationalLastOutcome);
    algorithm
      assert(year >= nationalFirstYear and year < nationalFirstYear + size(nationalPopulation, 1), "Data.SCB.nationalPopulation saknar år " + String(year));
      if year <= known or known >= nationalLastOutcome then
        population := nationalPopulation[year - nationalFirstYear + 1];
      else
        // Efter det kända året: folkmängden fortsätter växa som det senast kända året. Senare utfall och den senaste
        // framskrivningen fanns inte då.
        population := nationalPopulation[known - nationalFirstYear + 1]*(nationalPopulation[known - nationalFirstYear + 1]/nationalPopulation[known - nationalFirstYear])^(year - known);
      end if;
    end nationalPopulationAt;

    function olderShares "Andelar av 65+ som är 65-79, 80-89 och 90+"
      input Real population[2, 101] "Befolkning per ettårsålder och kön";
      output Real shares[3] "Andel av 65+ som är 65-79, 80-89 och 90+";
    algorithm
      shares := {{sum(population[:, 66:80]), sum(population[:, 81:90]), sum(population[:, 91:101])}}/sum(population[:, 66:101]);
      annotation(Icon(coordinateSystem(extent = {{{{-100, -100}}, {{100, 100}}}}), graphics = {{Ellipse(lineColor = {{90, 110, 130}}, fillColor = {{255, 255, 255}}, fillPattern = FillPattern.Solid, extent = {{{{-100, -100}}, {{100, 100}}}}), Text(textColor = {{90, 110, 130}}, extent = {{{{-92, -50}}, {{92, 50}}}}, textString = "f(x)")}}));
    end olderShares;
    annotation(Icon(coordinateSystem(extent = {{{{-100, -100}}, {{100, 100}}}}), graphics = {{Rectangle(lineColor = {{90, 110, 130}}, fillColor = {{245, 248, 250}}, fillPattern = FillPattern.Solid, extent = {{{{-100, -100}}, {{100, 100}}}}, radius = 25), Text(textColor = {{35, 50, 65}}, extent = {{{{-92, -30}}, {{92, 40}}}}, textString = "SCB"), Text(textColor = {{90, 110, 130}}, extent = {{{{-92, -80}}, {{92, -35}}}}, textString = "demografi")}}), Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0). Tabeller: {tables}.
Arkiv {d['archive']}; bearbetat av scripts/prepare_demography.py till data/demography-inputs.json.</p>
<p>Rikets folkmängd, fruktsamhet och dödlighet är desamma för alla kommuner. En kommuns paket ärver det här paketet och
lägger till sina basår som <code>DemographyYear</code>. SCB:s framskrivna dödlighet och fruktsamhet kommer från
framskrivningen {first}.</p></html>"));
  end SCB;
'''
    municipality = f'''  package SCB "{NAME}s demografiska data från SCB. Genereras av scripts/write_demography_modelica.py; redigera inte för hand"
    extends Kommunekonomi.Data.SCB;

{chr(10).join(years)}

    function forYear "SCB-data för ett basår"
      input Integer year "Basår";
      output DemographyYear data "{NAME} vid basårets slut";
    algorithm
      assert(year >= {first_base} and year <= {last_base}, "{NAME}.Data.SCB har basåren {first_base}-{last_base}, inte " + String(year));
      data := {chain};
    end forYear;

    function populationForYear "Befolkning per ettårsålder och kön vid ett basårs slut"
      input Integer year "Basår";
      output Real population[2, 101] "Befolkning per ettårsålder och kön";
    protected
      DemographyYear data;
    algorithm
      data := forYear(year);
      population := data.population;
    end populationForYear;

    annotation(Icon(coordinateSystem(extent = {{{{-100, -100}}, {{100, 100}}}}), graphics = {{Rectangle(lineColor = {{90, 110, 130}}, fillColor = {{245, 248, 250}}, fillPattern = FillPattern.Solid, extent = {{{{-100, -100}}, {{100, 100}}}}, radius = 25), Text(textColor = {{35, 50, 65}}, extent = {{{{-92, -30}}, {{92, 40}}}}, textString = "SCB"), Text(textColor = {{90, 110, 130}}, extent = {{{{-92, -80}}, {{92, -35}}}}, textString = "demografi")}}), Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0). Tabeller: {tables}.
Arkiv {d['archive']}; bearbetat av scripts/prepare_demography.py till data/demography-inputs.json.</p>
<p>Varje basår använder bara data fram till det året, så att en prognos från det kan jämföras med det som hände sedan.
Varje basår har en egen dödlighetstrend, skattad ur rikets livslängdstabeller de tio åren fram till basåret.
SCB:s framskrivna dödlighet och fruktsamhet kommer från framskrivningen {first} och är bara rättvisa för basåret {last_base}.</p></html>"));
  end SCB;
'''
    return library, municipality


def main():
    d = json.loads((ROOT / 'data/demography-inputs.json').read_text())
    national = json.loads((ROOT / 'data/national-population.json').read_text())
    nat_years = sorted(int(y) for y in national['population'])
    nat_values = [national['population'][str(y)] for y in nat_years]
    pad = '      '
    years = cohort_records(NAME, PREFIX, d['baseYears'])
    bases = sorted(d['baseYears'])
    chain = ' elseif '.join(f'if year == {b} then {PREFIX}{b}' if i == 0 else f'year == {b} then {PREFIX}{b}' for i, b in enumerate(bases[:-1]))
    chain = f'{chain} else {PREFIX}{bases[-1]}'
    first_base, last_base = bases[0], bases[-1]
    first = d['fertilityProfile']['year']
    tfr = [d['projectedTotalFertility'][str(first + i)] for i in range(HORIZON)]
    improve = d['mortalityImprovement']
    library, municipality = packages(d, national, years, chain, first_base, last_base, first, tfr, improve, nat_years, nat_values, pad)
    for path, package in ((LIBRARY, library), (MUNICIPALITY, municipality)):
        package = ''.join('  ' + line if line.strip() else line for line in package.splitlines(keepends=True))  # nested in Data
        text = path.read_text()
        existing = re.compile(r'^    package SCB\b.*?^    end SCB;\n', re.S | re.M)
        if not existing.search(text):
            raise SystemExit(f'{path}: no package SCB inside Data')
        path.write_text(existing.sub(lambda m: package, text, count=1))
    print(f'{NAME}.Data.SCB: base years {", ".join(sorted(d["baseYears"]))}; national data in Kommunekonomi.Data.SCB')


if __name__ == '__main__':
    main()
