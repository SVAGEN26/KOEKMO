export const DEFAULT_MUNICIPALITY='0583';

const names={
  '0509':['Ödeshög','Odeshog'],
  '0512':['Ydre','Ydre'],
  '0513':['Kinda','Kinda'],
  '0560':['Boxholm','Boxholm'],
  '0561':['Åtvidaberg','Atvidaberg'],
  '0562':['Finspång','Finspang'],
  '0563':['Valdemarsvik','Valdemarsvik'],
  '0580':['Linköping','Linkoping'],
  '0581':['Norrköping','Norrkoping'],
  '0582':['Söderköping','Soderkoping'],
  '0583':['Motala','Motala'],
  '0584':['Vadstena','Vadstena'],
  '0586':['Mjölby','Mjolby']
};

export const municipalities=Object.fromEntries(Object.entries(names).map(([code,[name,packageName]])=>[
  code,{name,packageName,firstYears:code===DEFAULT_MUNICIPALITY?[2026,2025,2022]:[2026,2025]}
]));

export function cohortModifiers(packageName, year) {
  const record=`Kommunekonomi.Municipalities.${packageName}.Data.SCB.${packageName.toLowerCase()}${year}`;
  // The level is the library's default: Sweden's fertility in the base year times the municipality's relation to Sweden
  // over five years. Only the age profile is set here, for the years SCB's historical profiles cover.
  const profile=year>=2021&&year<=2024
    ?`,
          redeclare Kommunekonomi.Components.Fertility.Constant fertility(totalFertility=Kommunekonomi.Data.SCB.totalFertilityAt(${year})*${record}.totalFertilityMean5/Kommunekonomi.Data.SCB.totalFertilityMean5(${year}), profile=Kommunekonomi.Data.SCB.historicalFertilityProfile[${year-2020},:])`:'';
  return `data=${record}, reportedTotal=sum(p0), migrationWeights=migrationWeights${profile}`;
}
