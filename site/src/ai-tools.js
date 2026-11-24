// Tools an AI assistant can call to work with the scenario lab: what can be set, try scenarios, read series.
// Written once and used by the page (through the local bridge, mcp/bridge.ts) and by tests.
// The tools only call the adapter the page provides; no model text or code from the assistant reaches the compiler.

const municipalityArg={type:'string',description:'Kommunkod, till exempel 0583 (Motala) eller 0580 (Linköping)'};
const valuesArg={type:'object',description:'Antaganden som nyckel och värde, i samma enheter som reglagen på sidan (list_assumptions). '+
  'Till exempel {"taxRate":22.2,"investment":500}. Skatteunderlag, löner och priser anges som avvikelse i procentenheter mot SKR:s bana när SKR:s underlag är aktivt.',
  additionalProperties:{type:'number'}};

export const TOOLS=[
  {name:'get_state',description:'Vilken kommun och vilket basår sidan visar, prognosåren, vilka antaganden som är ändrade och resultatet sista året.',
    inputSchema:{type:'object',properties:{}}},
  {name:'list_municipalities',description:'Kommunerna som kan väljas och deras möjliga startår.',
    inputSchema:{type:'object',properties:{}}},
  {name:'list_assumptions',description:'Alla antaganden som går att sätta: nyckel, namn, enhet, tillåtet intervall, nuvarande värde, grundvärde och en förklaring av vad det betyder och var grundvärdet kommer ifrån.',
    inputSchema:{type:'object',properties:{}}},
  {name:'preview_scenario',description:'Pröva ett scenario utan att ändra sidan: räknar med sidans nuvarande antaganden plus values och returnerar resultat, skuld, kassa och befolkning år för år, och skillnaden mot sidans nuvarande scenario.',
    inputSchema:{type:'object',properties:{values:valuesArg},required:['values']}},
  {name:'set_assumptions',description:'Ändra antaganden på sidan, så att användaren ser scenariot. Ange ett kort skäl; det visas i sidans logg.',
    inputSchema:{type:'object',properties:{values:valuesArg,reason:{type:'string'}},required:['values']}},
  {name:'reset_assumptions',description:'Återställ sidans antaganden till grundvärdena.',
    inputSchema:{type:'object',properties:{reason:{type:'string'}}}},
  {name:'select_municipality',description:'Byt kommun och startår på sidan. Antagandena återställs.',
    inputSchema:{type:'object',properties:{municipality:municipalityArg,startYear:{type:'integer',description:'Första prognosåret, till exempel 2026'}},required:['municipality']}},
  {name:'get_results',description:'Sidans nuvarande scenario år för år: befolkning, skatt, bidrag, nettokostnad, resultat, resultat i procent av skatt och bidrag, investering, ränta, skuld och kassa.',
    inputSchema:{type:'object',properties:{}}},
  {name:'list_series',description:'Vilka dataserier som finns att läsa: utfall per kommun, SKR:s prognosunderlag, prisindex, rikets folkmängd och modellens bakåttest.',
    inputSchema:{type:'object',properties:{}}},
  {name:'get_series',description:'Läs en dataserie med källa. Utfall efter basåret är facit, inte indata: använd dem för att pröva modellen, inte för att välja antaganden i ett bakåttest.',
    inputSchema:{type:'object',properties:{series:{type:'string',description:'Seriens namn från list_series'},municipality:municipalityArg},required:['series']}}
];

const SERIES={
  accounts:'Bokslut per år för kommunen (SCB:s räkenskapssammandrag): skatt, bidrag, nettokostnad, resultat, skuld, investering, befolkning, skattesats. Kräver municipality.',
  costGrowth:'Kostnadsökning utöver priser och verksamhetsvolym per år, mätt som modellens costDrift. Kräver municipality.',
  skrPlanning:'SKR:s årsvisa antaganden för prognosåren (cirkulär 26:28): skatteunderlag, arbetskraftskostnad och övriga priser, procent per år. Den kommun sidan visar.',
  skrRevenue:'SKR:s beräkning av kommunens skatt och bidrag per prognosår (Prognosunderlag 26:28). Den kommun sidan visar.',
  pkv:'SKR:s prisindex för kommunal verksamhet, utfall per år (PKV): totalt, arbetskraft och övrigt.',
  nationalPopulation:'Rikets folkmängd 31 december: utfall och SCB:s prognos.',
  hindcast:'Modellens bakåttest 2017-2019 till 2025 för 13 kommuner, för årsmodellen och för den kontinuerliga modellen som sidan kör: medelfel per horisont och jämförelsen "basårets resultatandel kvar".'
};

const round=x=>typeof x==='number'?Math.round(x*10)/10:x;
function summary(rows) {
  return rows.map(r=>({year:r.year,population:Math.round(r.population),tax:round(r.tax),grants:round(r.grants),netCost:round(r.cost+r.depreciation),
    result:round(r.result),resultShare:round(100*r.result/(r.tax+r.grants)),investment:round(r.investment),interest:round(r.interest),
    debt:round(r.debt),cash:round(r.cash)}));
}

function checkValues(adapter,values) {
  if(!values||typeof values!=='object'||Array.isArray(values)||!Object.keys(values).length) throw Error('values ska vara ett objekt med minst ett antagande.');
  const known=new Map(adapter.assumptions().map(a=>[a.key,a]));
  for(const [key,value] of Object.entries(values)) {
    const a=known.get(key);
    if(!a) throw Error(`Okänt antagande ${key}; se list_assumptions.`);
    if(typeof value!=='number'||!Number.isFinite(value)) throw Error(`${key} ska vara ett tal.`);
    if(value<a.min||value>a.max) throw Error(`${key} ska ligga mellan ${a.min} och ${a.max} ${a.unit}.`);
  }
  return values;
}

export async function callTool(adapter,name,args={}) {
  switch(name) {
    case 'get_state': {
      const state=adapter.state(),rows=adapter.results();
      const last=rows?.at(-1);
      return {...state,lastYear:last?summary([last])[0]:null};
    }
    case 'list_municipalities': return {municipalities:adapter.municipalities()};
    case 'list_assumptions': return {assumptions:adapter.assumptions(),
      note:'Värden i reglagens enheter. Procent anges som procent (3 = 3 %). Med SKR:s underlag aktivt anges skatteunderlag, löner och priser som avvikelse i procentenheter mot SKR:s årsvisa bana.'};
    case 'preview_scenario': {
      const values=checkValues(adapter,args.values);
      const [scenario,current]=await Promise.all([adapter.preview(values),adapter.results()]);
      const rows=summary(scenario.slice(1));
      const now=current?summary(current.slice(1)):null;
      return {values,years:rows,difference:now?rows.map((r,i)=>({year:r.year,result:round(r.result-now[i].result),debt:round(r.debt-now[i].debt),cash:round(r.cash-now[i].cash)})):null};
    }
    case 'set_assumptions': {
      const values=checkValues(adapter,args.values);
      const rows=await adapter.apply(values,String(args.reason??''));
      return {set:values,years:summary(rows.slice(1))};
    }
    case 'reset_assumptions': return {years:summary((await adapter.reset(String(args.reason??''))).slice(1))};
    case 'select_municipality': {
      const code=String(args.municipality??'');
      const choice=adapter.municipalities().find(m=>m.code===code);
      if(!choice) throw Error(`Okänd kommun ${code}; se list_municipalities.`);
      const startYear=args.startYear==null?choice.startYears[0]:Number(args.startYear);
      if(!choice.startYears.includes(startYear)) throw Error(`${choice.name} kan starta ${choice.startYears.join(', ')}.`);
      await adapter.select(code,startYear);
      return callTool(adapter,'get_state');
    }
    case 'get_results': {
      const rows=adapter.results();
      if(!rows) throw Error('Sidan har inget scenario ännu.');
      return {...adapter.state(),years:summary(rows)};
    }
    case 'list_series': return {series:SERIES};
    case 'get_series': {
      const series=String(args.series??'');
      if(!(series in SERIES)) throw Error(`Okänd serie ${series}; se list_series.`);
      return adapter.series(series,args.municipality==null?null:String(args.municipality));
    }
    default: throw Error(`Okänt verktyg ${name}.`);
  }
}
