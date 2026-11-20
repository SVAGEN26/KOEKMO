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
  const record=`${packageName}.Data.SCB.${packageName.toLowerCase()}${year}`;
  const profile=year>=2021&&year<=2024
    ?`, profile=Kommunekonomi.Data.SCB.historicalFertilityProfile[${year-2020},:]`:'';
  return `data=${record}, reportedTotal=sum(p0), migrationWeights=migrationWeights,
          redeclare Kommunekonomi.Components.Fertility.Constant fertility(totalFertility=${record}.totalFertilityMean5${profile})`;
}
