import {DEFAULT_MUNICIPALITY,municipalities} from './municipalities.js';
import {sum,validateRevenuePath,holdRegulation,extendPlanning,workingCapitalDays,rateFixing} from './scenario-inputs.js';
import {MAX_YEARS} from './omc-session.js';
import {createWorkerEngine,ENGINE} from './jit-engine.js';
import {modelicaSource} from './modelica-adapter.js';
import {openScenarioReport} from './pdf-report.js';
import {createModelView} from './model-view.js';
import {connect as connectAi,isLoopback} from './ai-link.js';
const $=id=>document.getElementById(id),nf=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:0}),nf1=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:1}),
  unsignedZero=text=>/^[−-]0(,0+)?$/.test(text)?text.slice(1):text,  // a stock that is paid off is 0, not −0
  fmt=x=>unsignedZero(nf.format(x)),decimal=x=>unsignedZero(nf1.format(x));
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const definitions=[
  ['taxGrowth','Skatteunderlag, årlig tillväxt',0,7,.1,'%', 'Illustrativ nationell referens'],
  ['wageGrowth','Löner, årlig ökning',0,7,.1,'%', 'Bas: 2 288 mnkr exklusive pensioner'],
  ['pensionGrowth','Pensionskostnad, årlig ökning',-30,30,.5,'%', 'Separat från löner. Bas: 190 mnkr'],
  ['priceGrowth','Övriga priser, årlig ökning',0,6,.1,'%', 'Årlig prisförändring'],
  ['migrationDelta','Förändrat årligt flyttnetto',-400,600,10,'pers.', 'Förändring mot kalibrerat restflöde'],
  ['interestRate','Genomsnittlig låneränta',0,7,.1,'%', 'På banklåneskulden'],
  ['investment','Årliga investeringar',0,800,1,'mnkr', 'Bokslut 2025: 413 mnkr'],
  ['productivity','Årlig produktivitetsökning',0,2,.1,'%', 'Scenario, ej belagd effektivisering'],
  ['costDrift','Kostnadsökning utöver demografi och pris',-2,3,.05,'%', 'Standard 0; historiskt -0,3 till 0,4 %/år'],
  ['grantIncrease','Statens bidragshöjning per år, utöver SKR',-10,20,.5,'mdkr', 'I riket, från andra prognosåret']
];
const advanced=[['inflationShock','Extra inflation första prognosåret',0,8,.25,'p.e.', 'Priser samma år; löner, pensioner och ränta åren efter'],['inflationPersistence','Andel av den extra inflationen kvar året därpå',0,1,.05,'', '0,5 = halveras varje år'],['inflationWagePassThrough','Löner och skatteunderlag: andel av inflationen',0,1,.05,'', '2022–2025 cirka 0,4'],['inflationPensionPassThrough','Pensionskostnadens svar på inflationen',0,15,.5,'', 'Procent högre pensionskostnad per procentenhet; 2023–2025 cirka 7–10'],['inflationRateResponse','Räntans svar på extra inflation',0,1.5,.05,'', 'Procentenheter högre marknadsränta per procentenhet inflation, åren efter'],['inflationGrantCompensation','Statlig kompensation i bidragen',0,100,5,'%', 'Andel av förra årets extra inflation; 0 = bidragen fasta i kronor'],['rateShock','Räntehöjning på marknadsräntan',0,8,.25,'p.e.', 'Nya och omsatta lån, från vald månad första prognosåret'],['rateShockMonth','Räntehöjningens första månad',1,12,1,'mån', '1 = januari första prognosåret'],['rateFixingYears','Genomsnittlig räntebindning',0,8,.1,'år', 'Hur snabbt en räntehöjning slår igenom'],['grantGrowth','Bidrag, årlig referenstillväxt',0,6,.1,'%', 'Förenklad intäktsbana'],['operatingRevenueGrowth','Verksamhetsintäkter, årlig ökning',-5,8,.1,'%', '751 mnkr i basåret, volymjusterat'],['birthChange','Förändring i födelsetal',-30,30,1,'%', 'Mot basårets födelseexponering'],['taxRate','Kommunal skattesats',19,24,.1,'%', 'Bokslut: 21,70 %'],['adjustment','Årlig kapacitetsanpassning',0,1,.05,'', '0 = låst kapacitet; 1 = direkt anpassning'],['equalisationOffset','Utjämning av lokal skatteavvikelse',0,1,.05,'', 'Känslighet, ej exakt lagberäkning']];
// The assumptions in the panel, grouped. Every key of `definitions` and `advanced` is in exactly one group.
const assumptionGroups=[
  ['population','Befolkning','Flyttnetto och födda',['migrationDelta','birthChange']],
  ['revenue','Intäkter','Skattesats, skatteunderlag och bidrag',['taxRate','taxGrowth','grantIncrease','grantGrowth','equalisationOffset']],
  ['costs','Kostnader och verksamhet','Löner, priser, pensioner och anpassning',['wageGrowth','priceGrowth','pensionGrowth','costDrift','productivity','operatingRevenueGrowth','adjustment']],
  ['capital','Investeringar och lån','Investeringar, ränta och räntebindning',['investment','interestRate','rateFixingYears']],
  ['shocks','Ränte- och inflationschock','Plötslig höjning av räntan eller inflationen',['rateShock','rateShockMonth','inflationShock','inflationPersistence','inflationWagePassThrough','inflationPensionPassThrough','inflationRateResponse','inflationGrantCompensation']]
];
// What each assumption means and where its default comes from.
const explanations={
  taxGrowth:'Hur mycket rikets skatteunderlag växer per år. Kommunens skatt följer det, justerat för hur kommunens folkmängd ändras mot rikets. Med planeringsunderlagen anger reglaget avvikelsen från SKR:s årsvisa bana. Låst när SKR:s kommunvisa intäkter används.',
  wageGrowth:'Årlig löneökning. Lönekostnaden följer också verksamhetens volym och produktiviteten. Med planeringsunderlagen anger reglaget avvikelsen från SKR:s index för arbetskraftskostnad.',
  pensionGrowth:'Pensionskostnadens årliga ökning från basårets bokförda kostnad. Kostnaden påverkar resultatet; utbetalningarna antas lika stora när ingen egen bana finns. Standardvärdet är illustrativt.',
  priceGrowth:'Prisökning för övriga kostnader: köpta tjänster, material och lokaler. Med planeringsunderlagen anger reglaget avvikelsen från SKR:s index för övrig förbrukning.',
  migrationDelta:'Fler eller färre inflyttade netto per år än i den kalibrerade banan. Fördelas på åldersgrupperna. Skatt och bidrag följer folkmängden den 1 november året före, så effekten på intäkterna kommer ett år senare; behoven i skola och omsorg ändras direkt.',
  interestRate:'Räntan på lånen. Med räntebindning är det marknadsräntan för nya och omsatta lån. Standard: basårets genomsnittsränta enligt årsredovisningen när den finns, annars räntekostnaden delad med låneskulden.',
  investment:'Investeringsutgifter per år. Kassaflödet betalar först; resten lånas. Investeringarna ger avskrivningar och ränta de följande åren. Standard: basårets investeringar enligt bokslutet.',
  costDrift:'Hur mycket kostnaderna växer per år utöver det demografin och priserna förklarar: höjd standard, nya uppgifter, sådant som varken är volym eller pris. Standard 0. Historiskt (2011–2025) låg den i länets kommuner mellan -0,3 och 0,4 procent per år i medel, mätt som modellen använder den: den ökning av löner och övriga kostnader som får modellens nettokostnad att växa som SCB:s, med SKR:s prisindex för kommunal verksamhet och modellens verksamhetsvolym. Enskilda år varierar med 2–3 procent. I ett bakåttest åtta år framåt från 2017–2019 gav historikens medel för höga kostnader; utan den träffade resultatet bättre.',
  grantIncrease:'Statens höjning av de generella statsbidragen, utöver SKR:s bana: så många miljarder kronor mer i riket för varje år från det andra prognosåret. Det första året är redan beslutat i budgetpropositionen. Höjningen fördelas lika per invånare, som regleringsbidraget. I riket ökade generella statsbidrag och utjämning från 130,8 till 146,1 miljarder kronor 2021–2025 (SCB), i snitt cirka 3,8 miljarder per år.',
  productivity:'Minskar lönekostnaden för samma verksamhetsvolym. Ett antagande, ingen belagd effektivisering. Standard 0.',
  inflationShock:'Extra inflation utöver prisbanan första prognosåret. Priserna på övriga kostnader stiger samma år. Löner, skatteunderlag, pensionskostnad och ränta följer åren efter, med medelvärdet av de två föregående årens extra inflation. Scenariot Högre inflation använder 3 procentenheter.',
  inflationWagePassThrough:'Hur stor del av den fördröjda inflationen som når lönerna och skatteunderlaget. 2022–2025 blev det cirka 0,4 i riket: avtalen ersatte inte hela prisökningen.',
  inflationPensionPassThrough:'Hur många procent pensionskostnaden stiger över sin bana per procentenhet fördröjd inflation. Pensionsskulden räknas upp med prisbasbeloppet, så kostnaden stiger kraftigt och går tillbaka när inflationen är över. 2023–2025 cirka 7–10 i länets kommuner; i det talet ligger även 2023 års pensionsavtal.',
  inflationPersistence:'Hur stor del av den extra inflationen som finns kvar året därpå. 0,5 betyder att den halveras varje år.',
  inflationRateResponse:'Hur många procentenheter marknadsräntan stiger per procentenhet fördröjd inflation (medel av de två föregående åren). Den ränta länets kommuner betalade steg 2023–2024 cirka 0,4 per procentenhet.',
  inflationGrantCompensation:'Andel av förra årets extra inflation som staten kompenserar i de generella bidragen. Bidragen är belopp i kronor som riksdagen beslutar; 0 betyder att de inte räknas upp.',
  rateShock:'Plötslig höjning av marknadsräntan för nya och omsatta lån. Slår igenom gradvis med räntebindningen. Scenariot Högre ränta använder 3 procentenheter från januari.',
  rateShockMonth:'Månad under första prognosåret då räntehöjningen börjar gälla. Resten av året räknas med den högre räntan.',
  rateFixingYears:'Genomsnittlig räntebindningstid för lån och derivat. Kortare bindning gör att en höjning slår igenom snabbare. Motala: årsredovisningen; övriga kommuner 3 år som antagande.',
  grantGrowth:'Årlig tillväxt för de generella bidragen i riket när ingen SKR-bana används. Kommunens del följer folkmängden mot rikets. Låst när SKR:s kommunvisa intäkter används.',
  operatingRevenueGrowth:'Taxor, avgifter, försäljning och riktade bidrag. Växer med vald takt och med folkmängden.',
  birthChange:'Fler eller färre födda än i modellens bana, i procent. Påverkar förskola och skola de följande åren.',
  taxRate:'Kommunal skattesats. Skatteintäkterna ändras i proportion till skattesatsen; bidragen och utjämningen ändras inte. Låst när SKR:s publicerade bana används rakt av.',
  adjustment:'Hur stor del av glappet mellan behov och kapacitet i verksamheten som stängs varje år. 0 = kapaciteten ligger still, 1 = följer behovet direkt. Illustrativt.',
  equalisationOffset:'Hur stor del av en lokal avvikelse i skatteunderlaget, till exempel en ändrad andel i arbetsför ålder, som utjämningen tar tillbaka via bidragen. Förenklad känslighet, inte lagens beräkning.'
};
let engine,b,history,planning,current,replay,regional,periodPlanning,experiments,ageIncome,overrides={},path=null,customPath,run,base,version=0,modelSource=null,modelView=null;
let rateFixingTable,lastScenarioKey,previousRun,outcomeBudgetMotala,activeMunicipality=DEFAULT_MUNICIPALITY;
const scenarioMunicipality=item=>item.settings.municipality??DEFAULT_MUNICIPALITY;
const presets={
  base:{},
  adverse:{taxGrowth:2.5,wageGrowth:4,priceGrowth:3,interestRate:4,migrationDelta:-100},
  migration:{migrationDelta:300},
  investment:{investment:250},
  // Marknadsräntan tre procentenheter högre från första prognosårets början; slår igenom med räntebindningen.
  higherInterest:{rateShock:3,rateShockMonth:1},
  // Tre procentenheter extra inflation första året, hälften kvar varje år därefter; lönerna, skatteunderlaget, pensionerna och räntan följer åren efter.
  higherInflation:{inflationShock:3,inflationPersistence:0.5}
};
// The presets are written for Motala. Elsewhere, migration scales with the population
// (Motala 43 131 at the end of 2025) and the investment preset with the municipality's own level.
const MOTALA_POPULATION=43131;
const presetOverrides=choice=>{
  if(b.municipality===DEFAULT_MUNICIPALITY) return presets[choice];
  if(choice==='investment') return {investment:Math.round(b.assumptions.investment*.6)};
  const preset={...presets[choice]};
  const population=b.reportedPopulation??b.population.reduce((x,y)=>x+y,0);
  if('migrationDelta' in preset) preset.migrationDelta=Math.round(preset.migrationDelta*population/MOTALA_POPULATION);
  return preset;
};
const skrSources={
  'skr-2021':{circular:'21:35',url:'https://extra.skr.se/download/18.4c5da23117c02359242545dc/1633090430755/21035.pdf'},
  'skr-2026':{circular:'26:28',url:'https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html'}
};
const comparisonSelectors=[$('comparison-scenario'),$('comparison-preset')];
const scenarioStorageKey='motala.saved-scenarios.v1';
const savedControlIds=['planning-enabled','regulation-held','time-model','revenue-mode','demography-mode','split-payroll',
  'employer-rate','construction-years','construction-share','liquidity-policy','cash-reserve','defer-investment-share',
  'prefinance-share','working-capital-enabled','collection-days','payment-days','grant-advance',
  'migration-profile','age-tax','project-choice'];
let savedScenarios=[],latestSettings,explanationRuns;

function renderSavedScenarios() {
  const list=$('saved-scenario'),previous=list.value;
  const localScenarios=savedScenarios.filter(item=>scenarioMunicipality(item)===activeMunicipality);
  list.replaceChildren(new Option('Välj sparad körning',''));
  for(const saved of localScenarios) list.add(new Option(saved.name,saved.id));
  if(localScenarios.some(saved=>saved.id===previous)) list.value=previous;
  for(const select of comparisonSelectors) {
    const value=select.value;
    select.querySelector('optgroup[data-saved]')?.remove();
    const group=document.createElement('optgroup');
    group.label='Sparade scenarier';
    group.dataset.saved='';
    for(const saved of localScenarios) group.append(new Option(saved.name,saved.id));
    select.append(group);
    if([...select.options].some(option=>option.value===value)) select.value=value;
  }
  for(const id of ['open-scenario','copy-scenario','delete-scenario']) $(id).disabled=!list.value;
}
function persistScenarios(next) {
  localStorage.setItem(scenarioStorageKey,JSON.stringify(next));
  savedScenarios=next;
  renderSavedScenarios();
}
function snapshotSettings() {
  return structuredClone({
    municipality:activeMunicipality,firstYear:b.baseYear+1,endYear:b.baseYear+b.assumptions.years,overrides,preset:$('preset').value,
    customPath,controls:Object.fromEntries(savedControlIds.filter($).map(id=>[id,$(id).type==='checkbox'?$(id).checked:$(id).value]))
  });
}
function setupSavedScenarios() {
  try {
    const items=JSON.parse(localStorage.getItem(scenarioStorageKey)??'[]');
    if(Array.isArray(items)) savedScenarios=items.filter(item=>item?.id?.startsWith('saved-')&&typeof item.name==='string'&&item.run?.rows?.length&&item.settings);
  }catch(e){$('save-status').textContent='Kunde inte läsa sparade scenarier.';}
  renderSavedScenarios();
  $('saved-scenario').onchange=()=>{for(const id of ['open-scenario','copy-scenario','delete-scenario']) $(id).disabled=!$('saved-scenario').value;};
  $('save-scenario').onclick=async()=>{
    try {
      const name=$('scenario-name').value.trim();
      if(!name||!run||drawing) throw Error('Ange ett namn och invänta beräkningen.');
      const item={id:'saved-'+crypto.randomUUID(),name,settings:latestSettings,run};
      item.modelSource=await modelSource;
      persistScenarios([...savedScenarios,item]);
      $('saved-scenario').value=item.id;
      $('saved-scenario').onchange();
      $('save-status').textContent=`Sparade ${name}.`;
    }catch(e){$('save-status').textContent=e.message;}
  };
  for(const id of ['open-scenario','copy-scenario']) $(id).onclick=async()=>{
    const saved=savedScenarios.find(item=>item.id===$('saved-scenario').value&&scenarioMunicipality(item)===activeMunicipality);
    if(!saved) return;
    const source=await modelSource;
    if(saved.modelSource&&JSON.stringify(saved.modelSource)!==JSON.stringify(source)) {
      $('save-status').textContent='Den sparade körningen är från en annan modellversion. Scenariolabbet räknar om med den aktuella versionen.';
    }
    for(const [key,value] of Object.entries(saved.settings.controls)) {
      const control=$(key);
      if(control) {if(control.type==='checkbox') control.checked=value; else control.value=value;}
    }
    $('start-year').value=saved.settings.firstYear;
    $('scenario-name').value=id==='copy-scenario'?`Kopia av ${saved.name}`.slice(0,80):saved.name;
    selectPeriod(saved.settings.firstYear,saved.settings);
    document.querySelector('.tab[data-tab="scenario"]').click();
  };
  $('delete-scenario').onclick=()=>{
    try {
      persistScenarios(savedScenarios.filter(item=>item.id!==$('saved-scenario').value));
      $('save-status').textContent='Den sparade körningen har tagits bort.';
      draw();
    }catch(e){$('save-status').textContent=e.message;}
  };
}
const sourcedRates={taxGrowth:['Skatteunderlag, avvikelse mot SKR','taxBaseGrowth'],wageGrowth:['Arbetskraft, avvikelse mot SKR','labourCostGrowth'],priceGrowth:['Övriga priser, avvikelse mot SKR','otherPriceGrowth']};
const sourcedRate=key=>b.planningInputs&&sourcedRates[key]&&!(key==='wageGrowth'&&b.assumptions.splitPayroll);
function controlDefinitions(defs){return defs.map(d=>sourcedRate(d[0])?[d[0],sourcedRates[d[0]][0],-3,3,.1,'pp','Procentenheter mot SKR:s årsvisa bana']:d);}
// The imported SKR path, with the regulation grant held per inhabitant after the decided budget year unless unchecked.
function selectPath(enabled){
  const source=b.planningInputs;
  if(!enabled||!source?.revenuePath) return null;
  const skr=validateRevenuePath(source.revenuePath,b.baseYear,b.municipality);
  return $('regulation-held').checked&&source.regulationRule?holdRegulation(skr,source.regulationRule.heldFrom):skr;
}
function planningControls(){
  const controls=definitions.map(d=>{
    if(d[0]==='wageGrowth') {
      const o=b.operatingAccounts;
      const value=b.assumptions.splitPayroll?o.payrollExcludingPensions*b.experiments.wages/(b.experiments.wages+b.experiments.employerContributions):o.payrollExcludingPensions;
      return [...d.slice(0,6),`Bas: ${fmt(value)} mnkr${b.assumptions.splitPayroll?' i löner':' exklusive pensioner'}`];
    }
    if(d[0]==='pensionGrowth') return [...d.slice(0,6),`Bas: ${fmt(b.operatingAccounts.pensionExpense)} mnkr`];
    if(d[0]==='interestRate') return [d[0],d[1],d[2],Math.max(d[3],Math.ceil(b.assumptions.interestRate)),...d.slice(4)];
    if(d[0]==='investment') return [d[0],d[1],d[2],Math.max(d[3],Math.ceil(2*b.investment/100)*100),...d.slice(4,6),`Bokslut ${b.baseYear}: ${fmt(b.investment)} mnkr`];
    return d;
  });
  const fixing=rateFixing(rateFixingTable,b.municipality,b.baseYear);
  const localAdvanced=advanced.map(d=>d[0]==='rateFixingYears'?[...d.slice(0,6),fixing.note]:d[0]==='operatingRevenueGrowth'?[...d.slice(0,6),`Bas: ${fmt(b.operatingAccounts.operatingRevenue)} mnkr. Volymjusteras.`]:d[0]==='taxRate'?[...d.slice(0,6),`Bokslut: ${decimal(b.taxRate??b.assumptions.taxRate)} %`]:d);
  makeGroups(controlDefinitions([...controls,...localAdvanced]));
  syncControls();
}
function updatePeriod() {
  const endYear=Number($('end-year').value);
  const source=periodPlanning;
  $('planning-enabled').disabled=!source;
  const enabled=!!source&&$('planning-enabled').checked;
  b={...b,assumptions:{...b.assumptions,years:endYear-b.baseYear},
    planningInputs:enabled?extendPlanning(source,endYear):null};
  path=customPath===undefined?selectPath(enabled):customPath;
  $('revenue-mode').disabled=!path;
  $('revenue-mode').options[2].disabled=!b.experiments?.novemberPopulation||(customPath!==undefined&&customPath!==null);
  if($('revenue-mode').selectedOptions[0].disabled) $('revenue-mode').value='0';
  updateModelOptions();
  $('base-year').textContent=b.baseYear;
  $('forecast-years').textContent=`${b.baseYear+1}–${endYear}`;
  $('regulation-control').hidden=!source?.regulationRule;
  $('regulation-held').disabled=!enabled||!source?.regulationRule;
  $('planning-older-panel').hidden=b.municipality!==DEFAULT_MUNICIPALITY||b.baseYear!==2025;
  const last=source?.rows.at(-1).year;
  const vintage=b.baseYear===2021?'SKR 21:35 från september 2021 och bokslut 2021. ':b.baseYear===2024?'Bokslut 2024 och daterade riksantaganden från SKR 24:56. Bokslut 2025 finns i fliken Jämförelser. ':'';
  $('period-status').textContent=vintage+(enabled&&endYear>last
    ?`Från ${last+1} används sista årets prisantaganden och kalibrerade flyttflöden.${source.revenuePath?' Importerade intäkter förlängs med den sista årsförändringen.':''}`
    :'');
  planningControls();
  draw();
}
function updateModelOptions() {
  const splitPayroll=$('split-payroll').checked;
  const employerContributionRate=$('employer-rate').value===''?-1:Number($('employer-rate').value);
  $('construction-years').disabled=!Number.isFinite(b.workInProgress);
  const constructionYears=$('construction-years').disabled?0:Number($('construction-years').value);
  const constructionShare=Number($('construction-share').value)/100;
  const liquidityPolicy=$('liquidity-policy').checked;
  const workingCapitalEnabled=$('working-capital-enabled').checked;
  const enteredDays=id=>workingCapitalEnabled&&$(id).value!==''?Number($(id).value):null;
  const revenueMode=path?Number($('revenue-mode').value):0;
  const demography=$('demography-mode');
  for(const option of demography.options) option.disabled=option.value.includes('observed')&&!b.experiments?.netMigration;
  $('age-tax').disabled=!b.ageIncome||!path||revenueMode!==2;
  $('project-controls').hidden=!b.project;
  b.assumptions={...b.assumptions,revenueMode,timeModel:$('time-model').value,
    ageTax:!$('age-tax').disabled&&$('age-tax').checked,migrationProfile:$('migration-profile').value,
    projectChoice:b.project?$('project-choice').value:'none',
    demographyMode:demography.selectedOptions[0].disabled?'legacy':demography.value,splitPayroll,employerContributionRate,constructionYears,constructionShare,liquidityPolicy,
    cashReserve:liquidityPolicy?Number($('cash-reserve').value):0,
    deferInvestmentShare:liquidityPolicy?Number($('defer-investment-share').value)/100:0,
    prefinanceShare:liquidityPolicy?Number($('prefinance-share').value)/100:0,
    workingCapitalEnabled,collectionDays:enteredDays('collection-days'),paymentDays:enteredDays('payment-days'),
    firstYearGrantAdvance:workingCapitalEnabled?Number($('grant-advance').value):0};
  $('employer-rate-control').hidden=!splitPayroll;
  $('construction-share-control').hidden=constructionYears===0;
  $('liquidity-controls').hidden=!liquidityPolicy;
  $('working-capital-controls').hidden=!workingCapitalEnabled;
  const days=workingCapitalDays(b);
  $('collection-days').placeholder=`Basåret, ${decimal(days.collectionDays)} dagar`;
  $('payment-days').placeholder=`Basåret, ${decimal(days.paymentDays)} dagar`;
  const advanceNote=b.workingCapital?.grantAdvances==null
    ?'Basåret saknar separat uppgift om bidragsförskott. Modellen räknar med noll i ingående förskott.'
    :`Ingående förskott på ${decimal(b.workingCapital.grantAdvances)} mnkr räknas som intäkt första prognosåret i den befintliga intäktsbanan.`;
  $('working-capital-note').textContent=`Tomma dagfält använder basårets förhållanden. Ett nytt bidragsförskott gäller en intäkt som redan ingår i nästa års scenario. ${advanceNote}`;
  const notes=[];
  if(splitPayroll) {
    const {employerContributions,wages}=b.experiments;
    notes.push(`Basårets sociala avgifter är ${decimal(100*employerContributions/wages)} % av lönen. Löneökningen anges separat från SKR:s arbetskraftsindex.`);
  }
  if(b.assumptions.demographyMode.includes('observed')) {
    notes.push(`Flyttnetto och inflyttarnas åldersfördelning bygger på SCB ${b.experiments.years[0]}–${b.experiments.years.at(-1)}.`);
  }
  if(b.assumptions.demographyMode!=='legacy') notes.push('Befolkningen räknas från födslar, dödsfall och flyttflöden i den valda modellen.');
  if(path&&b.assumptions.revenueMode===2) notes.push('Skatt före avräkning, inkomstutjämning och regleringspost justeras med folkmängden den 1 november. Övriga delposter följer referensen.');
  if(b.assumptions.ageTax) notes.push(`Åldersprofil från SCB ${b.ageIncome.year}. Inkomstutjämningen reagerar på förändrat skatteunderlag.`);
  if(path&&b.assumptions.revenueMode===1) notes.push('Skatter och bidrag följer SKR:s referensvärden.');
  if(constructionYears) notes.push(`Investeringar belastar kassan när de betalas. Byggandelen börjar skrivas av efter ${constructionYears} år.`);
  $('experiment-note').textContent=notes.join(' ');
}
function selectPeriod(firstYear,settings={}) {
  const motala=activeMunicipality===DEFAULT_MUNICIPALITY;
  const period=firstYear===2025?regional[activeMunicipality].historical:motala?(firstYear===2022?replay:current):regional[activeMunicipality].current;
  const year=period.baseline.baseYear;
  const incomeYear=year===2021?'2019':'2024';
  periodPlanning=period.planning??(motala&&year===2025?planning:null);
  b=motala&&year!==2024?{...period.baseline,name:municipalities[activeMunicipality].name,ageIncome:{year:incomeYear,weights:ageIncome.municipalities['0583'][incomeYear],countyRate:ageIncome.countyRate},experiments:{...experiments[year],
    novemberPopulation:replay.novemberPopulation.rows.find(row=>row.year===year)?.population}}:period.baseline;
  b={...b,municipality:activeMunicipality,assumptions:{costDrift:0,grantIncrease:0,inflationShock:0,inflationPersistence:0.5,inflationWagePassThrough:0.4,inflationPensionPassThrough:8,inflationRateResponse:0.5,inflationGrantCompensation:0,rateShock:0,rateShockMonth:1,rateFixingYears:rateFixing(rateFixingTable,activeMunicipality,year).years,...b.assumptions}};
  history=period.history;
  overrides={...settings.overrides};
  customPath=settings.customPath;
  $('preset').value=settings.preset??'base';
  $('start-year').value=firstYear;
  $('end-year').innerHTML=Array.from({length:MAX_YEARS},(_,i)=>{
    const year=firstYear+i;
    return `<option value="${year}">${year}</option>`;
  }).join('');
  $('end-year').value=settings.endYear??b.baseYear+b.assumptions.years;
  if(!motala) renderMunicipalityEvidence(period);
  updatePeriod();
}
function selectMunicipality(code,firstYear=null) {
  if(code!==activeMunicipality) for(const id of savedControlIds) {
    const control=$(id);
    if(control.type==='checkbox') control.checked=control.defaultChecked;
    else if(control.tagName==='SELECT') control.selectedIndex=Math.max(0,[...control.options].findIndex(option=>option.defaultSelected));
    else control.value=control.defaultValue;
  }
  activeMunicipality=code;
  const {name,packageName,firstYears}=municipalities[code],motala=code===DEFAULT_MUNICIPALITY;
  $('municipality').value=code;
  $('municipality-brand').textContent=name;
  $('municipality-footer').textContent=name;
  const lentOn=regional?.[code]?.current?.baseline?.onLending?.loans;
  $('debt-note').textContent=motala?'Investeringar finansieras med kassaflöde och nya lån. Överskott amorterar skuld.'
    :lentOn>1?`Skulden är kommunens egna lån. Därutöver har kommunen lånat ${fmt(lentOn)} mnkr som den har lånat vidare till sina bolag. Den delen ingår inte, och räntan på den är borttagen ur både kostnader och intäkter.`
    :'Skulden är kommunens lån och obligationer med kortfristig del, enligt SCB. Investeringar finansieras med kassaflöde och nya lån.';
  $('municipality-code').textContent=`${code} / Östergötland`;
  $('municipality-title').textContent=`${name}${name.endsWith('s')?'':'s'} framtid?`;
  $('municipality-notice').textContent=motala
    ?'Bokslut, hämtad befolkningsprognos och omräknad SKR-referens för Motala. Intäktsmodellen och flera kostnadssamband är förenklade; bättre prognosprecision är inte visad.'
    :'Basår från SCB:s kommunräkenskaper och befolkningsstatistik. Kostnadsvikter från Kolada.';
  document.title=`${name} ekonomilabb · Budgetens drivkrafter`;
  $('model-package').href=`${packageName}.mo`;
  $('model-package').textContent=`Hämta ${packageName}.mo ↓`;
  $('wasm-status').textContent=`OpenModelica kompilerar Kommunekonomi.mo och ${packageName}.mo i din webbläsare.`;
  for(const panel of $('evidence').children) panel.hidden=panel.id!=='outcome-explanation'&&(panel.id==='municipality-evidence')===motala;
  renderOutcomeExplanation(code).catch(()=>{$('outcome-explanation').hidden=true;});
  const options=$('skr-options');
  options.hidden=!motala&&!regional[code].current.skrRevenue;
  options.disabled=options.hidden;
  options.querySelector('option[value="skr-2021"]').hidden=!motala;
  options.querySelector('option[value="skr-2021"]').disabled=!motala;
  $('comparison-scenario').value='latest';
  $('comparison-preset').value='base';
  run=previousRun=lastScenarioKey=undefined;
  $('metrics').replaceChildren();
  $('comparison-table').hidden=true;
  $('replay-comparison').hidden=true;
  $('scenario-name').value='';
  $('save-status').textContent='';
  renderSavedScenarios();
  const start=$('start-year');
  start.replaceChildren(...firstYears.map(year=>new Option(year===2026?String(year):`${year} · historisk körning`,year)));
  modelSource=Promise.all(['Kommunekonomi.mo',`${packageName}.mo`].map(async file=>{
    const response=await fetch(file);
    if(!response.ok) throw Error(file);
    const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',await response.arrayBuffer()));
    return {file,sha256:[...bytes].map(x=>x.toString(16).padStart(2,'0')).join('')};
  })).catch(()=>null);
  selectPeriod(firstYears.includes(firstYear)?firstYear:firstYears[0]);
}
function report(e){
  // Five age groups with fixed residual flows can empty a group over a long horizon.
  const hint=/tömmer en åldersgrupp/.test(e.message)?' Med fem åldersgrupper ligger restflödena fast och kan till slut tömma en grupp. Välj ett tidigare slutår eller befolkningsmodellen med ettårsåldrar.':'';
  $('error').textContent=e.message+hint;$('error').hidden=false;}
const sliderMarkup=([key,label,min,max,step,unit,help])=>`<div class="slider"><div class="slider-top"><label for="${key}">${label}</label><button type="button" class="info-button" data-info="${key}" aria-expanded="false" aria-controls="${key}-info" aria-label="Vad betyder ${safe(label)}?">?</button><div class="number"><input id="${key}" data-key="${key}" type="number" min="${min}" max="${max}" step="${step}" aria-label="${label}"><span>${unit}</span></div></div><p id="${key}-info" class="slider-info" hidden>${safe(explanations[key]??'')}</p><input id="${key}-range" data-key="${key}" type="range" min="${min}" max="${max}" step="${step}" aria-label="${label}, reglage"><div class="slider-help"><span>${help}</span></div></div>`;
// Rebuilding the panel keeps the groups the user has opened.
function makeGroups(defs){
  const container=$('assumption-groups');
  const open=new Set([...container.querySelectorAll('details[open]')].map(el=>el.dataset.group));
  const byKey=new Map(defs.map(d=>[d[0],d]));
  container.innerHTML=assumptionGroups.map(([id,title,sub,keys])=>`<details class="assumption-group" data-group="${id}"${open.has(id)?' open':''}><summary><span class="group-title">${title}<small>${sub}</small></span><span class="group-changes" data-changes="${id}"></span><button type="button" class="text-button group-reset" data-reset="${id}" hidden aria-label="Återställ ${title.toLowerCase()}">↺</button></summary>${keys.filter(k=>byKey.has(k)).map(k=>sliderMarkup(byKey.get(k))).join('')}</details>`).join('');
}
const changedKey=k=>overrides[k]!==undefined&&Math.abs(overrides[k]-b.assumptions[k])>1e-9;
function syncGroups(){
  for(const [id,,,keys] of assumptionGroups){
    const n=keys.filter(changedKey).length,label=document.querySelector(`[data-changes="${id}"]`);
    if(!label) continue;
    label.textContent=n?`${n} ändrad${n>1?'e':''}`:'';
    document.querySelector(`[data-reset="${id}"]`).hidden=!n;
  }
  const value=$('preset').value;
  for(const button of $('preset-buttons').children) button.setAttribute('aria-pressed',String(button.dataset.preset===value));
  $('preset-status').textContent=value==='custom'?'Eget scenario: du har ändrat antagandena.':'';
}
// `editing` is the field the user is typing in. Rewriting its value mid-edit drops a trailing decimal point ("2." → "2").
function syncControls(editing=null){for(const [k] of [...definitions,...advanced]){const value=(overrides[k]??b.assumptions[k])-(sourcedRate(k)?b.assumptions[k]:0);if($(k)!==editing)$(k).value=Number(value.toFixed(2));$(k).step='any';if($(k+'-range')!==editing)$(k+'-range').value=value;}syncGroups();}
// Y-axis with round steps (1, 2 or 5 times a power of ten). It starts at zero when the values are
// all on one side of it and not far from it; otherwise it hugs the data.
export function niceAxis(low,high) {
  if(low===high){low-=1;high+=1;}
  if(low>=0&&low<=0.3*high) low=0;
  if(high<=0&&high>=0.3*low) high=0;
  const raw=(high-low)/5, magnitude=10**Math.floor(Math.log10(raw)), norm=raw/magnitude;
  const step=(norm<1.5?1:norm<3?2:norm<7?5:10)*magnitude;
  return {low:Math.floor(low/step+1e-9)*step,high:Math.ceil(high/step-1e-9)*step,step};
}
const scales={},chartArgs={};
function scaleControl(id) {
  if($(id+'-scale')) return;
  const box=document.createElement('div');box.id=id+'-scale';box.className='scale-control';
  box.innerHTML=`<span>Skala</span><input type="number" step="any" aria-label="Y-axelns minsta värde" placeholder="auto" data-end="min"><span>till</span><input type="number" step="any" aria-label="Y-axelns största värde" placeholder="auto" data-end="max"><button type="button" class="text-button">Auto</button>`;
  $(id).after(box);
  const apply=()=>{
    const [lo,hi]=[...box.querySelectorAll('input')].map(el=>el.value===''?null:Number(el.value));
    if(lo===null&&hi===null) delete scales[id];
    else scales[id]={min:lo,max:hi};
    if(chartArgs[id]) chart(id,...chartArgs[id]);
  };
  box.addEventListener('change',apply);
  box.querySelector('button').onclick=()=>{box.querySelectorAll('input').forEach(el=>el.value='');apply();};
}
function chart(id,series,options={}) {
  if(!run) return;
  chartArgs[id]=[series,options];scaleControl(id);
  const {unit='',height=255,bands=[]}=options;
  const width=760,left=62,right=22,top=20,bottom=38,values=series.flatMap(s=>s.values).filter(Number.isFinite);
  const auto=niceAxis(Math.min(...values),Math.max(...values)),manual=scales[id];
  // A chosen end replaces the automatic one; round steps are kept between them.
  let low=manual?.min??auto.low,high=manual?.max??auto.high;
  if(!(high>low)){low=auto.low;high=auto.high;}
  const {step}=niceAxis(low,high);
  const x=i=>left+i*(width-left-right)/(run.rows.length-1),y=v=>top+(high-v)*(height-top-bottom)/(high-low);
  const ticks=[];for(let v=Math.ceil(low/step-1e-9)*step;v<=high+1e-9*step;v+=step) ticks.push(Math.abs(v)<1e-9*step?0:v);
  const lines=ticks.map(v=>`<line x1="${left}" y1="${y(v)}" x2="${width-right}" y2="${y(v)}" stroke="#e8ede5"/><text x="${left-11}" y="${y(v)+4}" text-anchor="end" fill="#78837d" font-size="11">${fmt(v)}</text>`).join('');
  const zero=low<0&&high>0?`<line x1="${left}" x2="${width-right}" y1="${y(0)}" y2="${y(0)}" stroke="#aab7a2" stroke-dasharray="3 4"/>`:'';
  const clip=`clip-${id}`;
  // Shaded columns for flagged years, for example years with a deficit.
  const half=(width-left-right)/(run.rows.length-1)/2;
  const shaded=bands.map(i=>`<rect class="band" x="${(x(i)-half).toFixed(2)}" y="${top}" width="${(2*half).toFixed(2)}" height="${height-top-bottom}" fill="#f6dcd6"><title>Underskott ${run.rows[i].year}</title></rect>`).join('');
  const paths=series.map(s=>`<path d="${s.values.map((v,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ')}" fill="none" stroke="${s.color}" stroke-width="${s.thin?1.3:2.8}" ${s.dash?'stroke-dasharray="5 5"':''}/>${s.thin?'':s.values.map((v,i)=>v<low||v>high?'':`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${s.color}"><title>${safe(s.name)} ${run.rows[i].year}: ${fmt(v)} ${unit}</title></circle>`).join('')}`).join('');
  const labelStep=Math.ceil((run.rows.length-1)/8);
  const labels=run.rows.map((r,i)=>i%labelStep===0||i===run.rows.length-1?`<text x="${x(i)}" y="${height-10}" text-anchor="middle" fill="#78837d" font-size="11">${r.year}</text>`:'').join('');
  $(id).innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${safe(series.map(s=>s.name).join(', '))}, ${run.rows[0].year}–${run.rows.at(-1).year}. Se tabeller för värden."><title>${safe(series.map(s=>s.name).join(', '))}</title><defs><clipPath id="${clip}"><rect x="${left}" y="${top-4}" width="${width-left-right}" height="${height-top-bottom+8}"/></clipPath></defs>${shaded}${lines}${zero}<g clip-path="url(#${clip})">${paths}</g>${labels}</svg>`;
}
function ledger() {
  const cols=[['year','År'],['tax','Skatt'],['grants','Bidrag & utj.'],['cost','Nettodrift'],['depreciation','Avskr.'],['interest','Ränta'],['result','Resultat'],['investment','Invest.'],['debt','Låneskuld'],['cash','Kassa']];
  $('ledger').innerHTML=`<caption>Bokslut ${b.baseYear}. Scenario ${b.baseYear+1}–${run.rows.at(-1).year}. Alla belopp i mnkr.</caption><thead><tr>${cols.map(c=>`<th scope="col">${c[1]}</th>`).join('')}</tr></thead><tbody>${run.rows.map(r=>`<tr>${cols.map(([k],i)=>`<${i?'td':'th scope="row"'} ${r[k]<0?'class="negative"':''}>${k==='year'?r[k]:fmt(r[k])}</${i?'td':'th'}>`).join('')}</tr>`).join('')}</tbody>`;
  $('cohort-table').innerHTML=`<thead><tr><th scope="col">År</th>${b.ageGroups.map(x=>`<th scope="col">${x}</th>`).join('')}<th scope="col">Totalt</th></tr></thead><tbody>${run.rows.map(r=>`<tr><th scope="row">${r.year}</th>${r.cohorts.map(x=>`<td>${fmt(x)}</td>`).join('')}<td>${fmt(r.population)}</td></tr>`).join('')}</tbody>`;
  const staff=run.assumptions.splitPayroll?[['wages','Löner'],['employerContributions','Sociala avgifter']]:[['payroll','Personal exkl. pension']];
  const components=[...staff,['pensionExpense','Pensionskostnad'],['otherOperatingExpense','Övriga kostnader'],['operatingRevenue','Verksamhetsintäkter'],['cost','Nettodrift'],['pensionCashPayments','Pensionsbetalning'],['operatingCash','Operativt kassaflöde']];
  $('operating-ledger').innerHTML=`<caption>Mnkr. Basår är bokslut; framtida pensionsbetalningar antas motsvara kostnaden om ingen separat betalningsbana anges.</caption><thead><tr><th scope="col">År</th>${components.map(c=>`<th scope="col">${c[1]}</th>`).join('')}</tr></thead><tbody>${run.rows.map(r=>`<tr><th scope="row">${r.year}</th>${components.map(([k])=>`<td>${r[k]==null?'—':fmt(r[k])}</td>`).join('')}</tr>`).join('')}</tbody>`;
  const showAdjustments=path&&run.assumptions.revenueMode===2;
  $('revenue-adjustments').hidden=!showAdjustments;
  if(showAdjustments) {
    const headers=['År','Skatt före avräkning','Inkomstutjämning','Regleringspost'];
    const rows=run.rows.slice(1).map(r=>[r.year,...[
      r.recurringTaxAdjustment,r.incomeEqualisationAdjustment,r.regulationPopulationAdjustment
    ].map(x=>signedMoney.format(x))]);
    $('revenue-adjustments').innerHTML=comparisonTable('revenue-adjustment-ledger','Justeringar av SKR:s intäktsbana',headers,rows,
      'Förändring i mnkr från scenariots intäktsreferens. Skatt påverkas av folkmängd och skattesats. Utjämning och regleringspost påverkas av folkmängd.');
  }
  const withConstruction=run.assumptions.constructionYears>0;
  $('capital-stocks').hidden=!withConstruction;
  if(withConstruction) {
    const headers=['År','Utbetald investering','Taget i bruk','Pågående arbeten','Tillgångar i bruk','Avskrivningar','Låneskuld'];
    const keys=['investment','commissioned','workInProgress','assets','depreciation','debt'];
    const rows=run.rows.map(r=>[r.year,...keys.map(key=>r[key]==null?'—':decimal(r[key]))]);
    const source=b.workInProgressSource;
    const link=source?` <a href="${safe(source.url)}">Källa för basårets pågående arbeten</a>.`:'';
    $('capital-stocks').innerHTML=comparisonTable('capital-stock-ledger','Investeringar och byggtid',headers,rows,
      `Belopp i mnkr. Ingående pågående arbeten fördelas jämnt över byggtiden.${link}`);
  }
  $('liquidity-ledger').hidden=!run.assumptions.liquidityPolicy;
  if(run.assumptions.liquidityPolicy) {
    const headers=['År','Investering betald','Kvar att betala','Nya lån','Varav förfinansiering','Amortering','Ränta','Kassa','Skuld'];
    const keys=['investment','outstandingDeferredInvestment','borrowing','prefinancing','repayment','interest','cash','debt'];
    const rows=run.rows.map(r=>[r.year,...keys.map(key=>r[key]==null?'—':decimal(r[key]))]);
    $('liquidity-ledger').innerHTML=comparisonTable('liquidity-table','Kassa och förfinansiering',headers,rows,
      'Belopp i mnkr. Kvar att betala gäller beloppet som flyttats från första till andra året.');
  }
  $('working-capital-ledger').hidden=!run.assumptions.workingCapitalEnabled;
  if(run.assumptions.workingCapitalEnabled) {
    const headers=['År','Kundfordringar','Leverantörsskulder','Förutbetalda bidrag','Effekt på kassaflödet','Kassaflöde från driften'];
    const keys=['tradeReceivables','tradePayables','deferredGrants','workingCapitalCash','operatingCash'];
    const rows=run.rows.map(r=>[r.year,...keys.map(key=>r[key]==null?'—':(key==='workingCapitalCash'?signedMoney.format(r[key]):decimal(r[key])))]);
    const source=b.workingCapital;
    const tradeLink=source.tradeSource?` <a href="${safe(source.tradeSource)}">Kundfordringar och leverantörsskulder i SCB</a>.`:'';
    const advanceLink=source.advanceSource?` <a href="${safe(source.advanceSource)}">Basårets bidragsförskott</a>.`:'';
    $('working-capital-ledger').innerHTML=comparisonTable('working-capital-table','Rörelsekapital',headers,rows,
      `Belopp i mnkr. Växande kundfordringar binder kassa. Växande leverantörsskulder och bidragsförskott frigör kassa.${tradeLink}${advanceLink}`);
  }
  const showProject=run.assumptions.projectChoice&&run.assumptions.projectChoice!=='none';
  $('project-ledger').hidden=!showProject;
  if(showProject) {
    const project=b.project;
    const headers=['År','Projektutbetalning (mnkr)','Pågående projekt (mnkr)','Driftsatt värde (mnkr)','Platser i bruk','Platser som saknas mot plan','Nya lån för hela kommunen (mnkr)'];
    const rows=run.rows.slice(1).map(r=>[r.year,...['projectPaid','projectWorkInProgress','projectCommissioned',
      'projectPlacesInUse','missingProjectPlaces','borrowing'].map(key=>decimal(r[key]))]);
    const note=`Resterande budgetbelopp räknas som en utbetalning utöver reglagets övriga investeringar. Platserna avser förskolan. <a href="${safe(project.accountsSource)}">Årsredovisning, s. 64–65</a>. <a href="${safe(project.capacitySource)}">Förskolans kapacitet</a>.`;
    $('project-ledger').innerHTML=comparisonTable('project-table',safe(project.name),headers,rows,note);
  }
}
function forecastPeriod(rows) {
  const first=rows[0].year,last=rows.at(-1).year;
  return first===last?String(first):`${first}–${last}`;
}
const signedMoney=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:1,signDisplay:'exceptZero'});
const signedPeople=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:0,signDisplay:'exceptZero'});
const change=(value,reference,formatter=signedMoney)=>value==null||reference==null?'—':formatter.format(value-reference);
const linkAmount=(value,url,format=decimal)=>value==null?'—':`<a href="${safe(url)}">${format(value)}</a>`;
function comparisonTable(id,title,headers,rows,caption) {
  return `<section class="panel">
    <h4 id="${id}-heading">${title}</h4>
    <div class="table-wrap" tabindex="0" role="region" aria-labelledby="${id}-heading">
      <table id="${id}">
        <caption>${caption}</caption>
        <thead><tr>${headers.map(label=>`<th scope="col">${safe(label)}</th>`).join('')}</tr></thead>
        <tbody>${rows.map(([year,...cells])=>`<tr><th scope="row">${year}</th>${cells.map(value=>`<td>${value}</td>`).join('')}</tr>`).join('')}</tbody>
      </table>
    </div>
  </section>`;
}
function renderScenarioComparison(scenario,comparison) {
  const scenarioRows=scenario.run.rows.slice(1);
  const referenceRows=comparison.run.rows.slice(1);
  const referencesByYear=new Map(referenceRows.map(row=>[row.year,row]));
  const sharedYears=scenarioRows.filter(row=>referencesByYear.has(row.year));
  $('comparison-table').hidden=!sharedYears.length;
  $('comparison-status').textContent=sharedYears.length
    ?`Gemensamma prognosår ${forecastPeriod(sharedYears)}.`
    :`Prognosåren överlappar inte. ${scenario.label} omfattar ${forecastPeriod(scenarioRows)} och ${comparison.label.toLowerCase()} ${forecastPeriod(referenceRows)}.`;
  if(!sharedYears.length) return;
  const groups=[
    ['comparison-revenue','Skatt och bidrag',[['tax','Skatt'],['grants','Bidrag och utjämning']]],
    ['comparison-result','Drift och resultat',[['cost','Nettodrift'],['result','Årets resultat']]],
    ['comparison-debt','Låneskuld',[['debt']]],
    ['comparison-population','Befolkning och flyttnetto',[['population','Invånare vid årets slut'],['population80Plus','Invånare 80+ vid årets slut'],['migration','Flyttnetto under året']]],
    ['comparison-services','Verksamhetsbehov',[['educationIndex','Utbildning'],['careIndex','Äldreomsorg']]]
  ];
  if(scenario.run.assumptions.constructionYears||comparison.run.assumptions.constructionYears) {
    groups.splice(2,0,['comparison-capital','Investeringar och byggtid',[
      ['investment','Utbetald investering'],['commissioned','Taget i bruk'],
      ['workInProgress','Pågående arbeten'],['depreciation','Avskrivningar']
    ]]);
  }
  if(scenario.run.assumptions.liquidityPolicy||comparison.run.assumptions.liquidityPolicy||
      scenario.run.assumptions.workingCapitalEnabled||comparison.run.assumptions.workingCapitalEnabled||
      [scenario,comparison].some(item=>['planned','delay'].includes(item.run.assumptions.projectChoice))) {
    const debtGroup=groups.find(([id])=>id==='comparison-debt');
    debtGroup[1]='Kassa och upplåning';
    debtGroup[2]=[['cash','Kassa'],['debt','Låneskuld'],['borrowing','Nya lån'],['repayment','Amortering'],['interest','Ränta']];
  }
  if(scenario.run.assumptions.workingCapitalEnabled||comparison.run.assumptions.workingCapitalEnabled) {
    groups.push(['comparison-working-capital','Rörelsekapital',[
      ['workingCapitalCash','Effekt på kassaflödet'],['operatingCash','Kassaflöde från driften']
    ]]);
  }
  if([scenario,comparison].some(item=>['planned','delay'].includes(item.run.assumptions.projectChoice))) {
    groups.push(['comparison-project','Bråta Hagar',[['projectPaid','Projektutbetalning (mnkr)'],['projectCommissioned','Driftsatt värde (mnkr)'],
      ['projectPlacesInUse','Platser i bruk'],['missingProjectPlaces','Platser som saknas mot plan']]]);
  }
  $('comparison-table').innerHTML=groups.map(([id,title,metrics])=>{
    const people=id==='comparison-population';
    const format=people?fmt:decimal;
    const formatter=people?signedPeople:signedMoney;
    const headers=['År',...(metrics.length>1?['Mått']:[]),scenario.label,comparison.label,'Skillnad'];
    const rows=sharedYears.flatMap(row=>metrics.map(([key,label])=>{
      const reference=referencesByYear.get(row.year)[key];
      const scale=id==='comparison-services'?100:1;
      return [row.year,...(label?[label]:[]),format(scale*row[key]),format(scale*reference),change(scale*row[key],scale*reference,formatter)];
    }));
    const unit=id==='comparison-project'?'Poster i mnkr eller antal platser enligt respektive rad.'
      :people?'Antal personer. Flyttnettot i ordinarie modell omfattar även restflöden.'
      :id==='comparison-services'?'Behovsindex, basår = 100.':'Belopp i mnkr.';
    return comparisonTable(id,title,headers,rows,`${unit} Skillnad = ${safe(scenario.label.toLowerCase())} minus ${safe(comparison.label.toLowerCase())}.`);
  }).join('');
}
function skrPopulationTable(scenario,path,source) {
  const modelByYear=new Map(scenario.run.rows.map(row=>[row.year,row.population]));
  const code=scenario.run.context?.municipality??activeMunicipality;
  const outcomes=code===DEFAULT_MUNICIPALITY?replay.novemberPopulation:regional[code].current.novemberPopulation;
  const outcomeByYear=new Map(outcomes?.rows.map(row=>[row.year,row.population]));
  const rows=path.rows.filter(row=>modelByYear.has(row.year-1)).map(row=>{
    const year=row.year-1;
    const before=modelByYear.get(year-1),after=modelByYear.get(year);
    const estimate=before==null?null:Math.round(before+(after-before)*10/12);
    const actual=outcomeByYear.get(year);
    return [year,estimate==null?'—':fmt(estimate),fmt(row.population),
      change(estimate,row.population,signedPeople),linkAmount(actual,outcomes?.source,fmt),
      change(estimate,actual,signedPeople)];
  });
  if(!rows.length) return '';
  const headers=['År',scenario.label,`SKR ${source.circular}`,'Skillnad mot SKR','SCB:s utfall','Skillnad mot utfall'];
  return comparisonTable('skr-population','Befolkning',headers,rows,
    'Invånare den 1 november. SKR använder den dagen för nästa års intäkter. Modellens novembervärde uppskattas med 10/12 av förändringen mellan två årsskiften.');
}
function renderSkrComparison(scenario,choice,selected) {
  const source=skrSources[choice];
  const code=scenario.run.context?.municipality??activeMunicipality;
  const path=code===DEFAULT_MUNICIPALITY?(choice==='skr-2021'?replay.planning.revenuePath:planning.revenuePath):regional[code].current.skrRevenue;
  const referenceByYear=new Map(path.rows.map(row=>[row.year,row]));
  const historical=code===DEFAULT_MUNICIPALITY&&scenario.run.rows[0].year===2021;
  const benchmarks=new Map(replay.comparisons.map(row=>[row.year,row]));
  const scenarioRows=scenario.run.rows.slice(1);
  const sharedRows=scenarioRows.filter(row=>referenceByYear.has(row.year));
  const population=skrPopulationTable(scenario,path,source);
  if(selected) {
    $('comparison-table').hidden=true;
    const period=forecastPeriod(path.rows);
    $('comparison-status').textContent=sharedRows.length
      ?`SKR ${source.circular} täcker intäktsåren ${period}. Gemensamma intäktsår ${forecastPeriod(sharedRows)}.`
      :`SKR ${source.circular} täcker intäktsåren ${period}. Banorna har inga gemensamma intäktsår.`;
  }
  $('replay-comparison').hidden=!sharedRows.length&&!population;
  if($('replay-comparison').hidden) return;
  $('replay-ledger-heading').textContent=`Jämförelse med SKR ${source.circular}`;
  const outcomeHeaders=['Bokslut','Skillnad mot bokslut'];
  const caption='Belopp i mnkr. Skillnad = vald modellbana minus respektive jämförelsevärde.';
  const revenues=[['skr-tax','Skatt','tax'],['skr-grants','Bidrag och utjämning','grants']];
  const tables=sharedRows.length?revenues.map(([id,title,key])=>{
    const headers=['År',scenario.label,`SKR ${source.circular}`,'Skillnad mot SKR',...(historical?outcomeHeaders:[])];
    const rows=sharedRows.map(row=>{
      const skr=referenceByYear.get(row.year)[key];
      const benchmark=benchmarks.get(row.year);
      const actual=benchmark?.outcome?.[key];
      return [row.year,decimal(row[key]),decimal(skr),change(row[key],skr),
        ...(historical?[linkAmount(actual,benchmark?.outcomeSource),change(row[key],actual)]:[])];
    });
    return comparisonTable(id,title,headers,rows,caption);
  }):[];
  if(historical&&sharedRows.length) {
    const headers=['År',scenario.label,...outcomeHeaders,'SCB','Budget'];
    const rows=sharedRows.map(row=>{
      const benchmark=benchmarks.get(row.year);
      const actual=benchmark?.outcome?.result;
      return [row.year,decimal(row.result),linkAmount(actual,benchmark?.outcomeSource),change(row.result,actual),
        linkAmount(benchmark?.scb?.result,replay.baseline.source),linkAmount(benchmark?.budgetResult,benchmark?.budgetSource)];
    });
    tables.push(comparisonTable('skr-result','Årets resultat',headers,rows,caption));
    if(scenario.run.assumptions.workingCapitalEnabled) {
      const cashRows=sharedRows.map(row=>{
        const benchmark=benchmarks.get(row.year);
        const actual=benchmark?.cashFlow;
        return [row.year,signedMoney.format(row.workingCapitalCash),
          linkAmount(actual?.workingCapitalCash,benchmark?.outcomeSource),decimal(row.operatingCash),
          linkAmount(actual?.operatingCash,benchmark?.outcomeSource)];
      });
      tables.push(comparisonTable('historical-working-capital','Rörelsekapital och kassaflöde mot bokslut',
        ['År','Effekt av modellens rörelsekapital','Effekt av hela rörelsekapitalet i bokslutet','Modellens driftkassa','Driftkassa i bokslutet'],
        cashRows,'Belopp i mnkr. Bokslutets rörelsekapital omfattar även poster som lager, exploateringsfastigheter och andra kortfristiga fordringar och skulder.'));
    }
    if(scenario.run.assumptions.constructionYears>0) {
      const fields=[['workInProgress','Pågående arbeten'],['depreciation','Avskrivningar'],['debt','Låneskuld']];
      const capitalRows=sharedRows.flatMap(row=>fields.map(([key,label])=>{
        const benchmark=benchmarks.get(row.year);
        const actual=benchmark?.capital?.[key];
        return [row.year,label,decimal(row[key]),linkAmount(actual,key==='workInProgress'?benchmark?.capitalSource:benchmark?.outcomeSource),
          change(row[key],actual)];
      }));
      tables.push(comparisonTable('historical-capital','Kapital och skuld mot bokslut',
        ['År','Mått',scenario.label,'Bokslut','Skillnad mot bokslut'],capitalRows,
        'Belopp i mnkr. Bokslutets avskrivningar kan även innehålla nedskrivningar.'));
    }
  }
  $('replay-tables').innerHTML=tables.join('')+population;
  const sourceLink=`<a href="${source.url}">SKR:s underlag till cirkulär ${source.circular}</a>.`;
  $('replay-notes').innerHTML=historical
    ?`Modellen utgår från bokslutet för 2021, som publicerades 2022. ${sourceLink}`
    :sourceLink;
}
function renderActualComparison(scenario) {
  const code=scenario.run.context?.municipality??activeMunicipality;
  const actual=regional[code].current.baseline;
  const forecast=scenario.run.rows.slice(1).find(row=>row.year===actual.baseYear);
  $('comparison-table').hidden=!forecast;
  $('comparison-status').textContent=forecast?'Modellvärden och utfall för 2025.':'Den valda modellbanan har inget prognosvärde för 2025.';
  if(!forecast) return;
  const finance=[
    ['Skatteintäkter',forecast.tax,actual.tax],['Bidrag och utjämning',forecast.grants,actual.grants],
    ['Nettokostnad inklusive avskrivningar',forecast.cost+forecast.depreciation,actual.cashCost+actual.depreciation],
    ['Årets resultat',forecast.result,actual.publishedResult]
  ];
  const budget=code===DEFAULT_MUNICIPALITY?outcomeBudgetMotala:regional[code].current.budgetResult;
  const title=['Mått',scenario.label,'Bokslut 2025','Skillnad mot bokslut',...(budget!=null?['Kommunbudget']:[])];
  $('comparison-table').innerHTML=comparisonTable('outcome-finances','Ekonomi',title,
    finance.map(([label,value,outcome])=>[label,decimal(value),linkAmount(outcome,actual.source),change(value,outcome),
      ...(budget!=null?[label==='Årets resultat'?decimal(budget):'—']:[])]),'Belopp i mnkr.')+
    comparisonTable('outcome-population','Befolkning',['Mått',scenario.label,'Utfall 2025','Skillnad mot utfall'],
      [['Invånare 31 december',fmt(forecast.population),linkAmount(actual.reportedPopulation,regional[code].current.sources.population,fmt),
        change(forecast.population,actual.reportedPopulation,signedPeople)]],'Antal invånare vid årets slut.');
}
function renderComparisons(scenario,reference) {
  $('replay-comparison').hidden=true;
  $('comparison-explanation').hidden=true;
  $('comparison-context').replaceChildren();
  if(scenario.run&&reference.choice==='actual-2025') {
    renderComparisonContext(scenario);
    renderActualComparison(scenario);
    return;
  }
  if(!scenario.run||(!reference.run&&!(reference.choice in skrSources))) {
    $('comparison-table').hidden=true;
    const failed=scenario.run?reference:scenario;
    $('comparison-status').textContent=failed.error
      ?`Kunde inte beräkna ${failed.label.toLowerCase()}. ${failed.error}`
      :'Gör en ändring i scenariot för att få en föregående körning att jämföra med.';
    return;
  }
  if(reference.choice in skrSources) {
    renderComparisonContext(scenario);
    renderSkrComparison(scenario,reference.choice,true);
    return;
  }
  renderComparisonContext(scenario,reference);
  renderScenarioComparison(scenario,reference);
  prepareExplanation(scenario,reference);
  if(activeMunicipality===DEFAULT_MUNICIPALITY&&scenario.run.rows[0].year===2021) renderSkrComparison(scenario,'skr-2021',false);
}
function renderComparisonContext(scenario,reference) {
  const describe=({label,run})=>{
    const rows=run.rows.slice(1),p=document.createElement('p');
    p.className='small muted';
    p.textContent=`${label} · ${forecastPeriod(rows)} · ${run.context?.basis??'Sparad historisk körning'}`;
    $('comparison-context').append(p);
  };
  describe(scenario);
  if(!reference) return;
  describe(reference);
  const keys={...Object.fromEntries([...definitions,...advanced].map(([key,label])=>[key,label])),
    timeModel:'Tid i modellen',revenueMode:'Intäktsmodell',demographyMode:'Demografi',migrationProfile:'Flyttprofil',ageTax:'Åldersviktad skatt',
    splitPayroll:'Delad lönebana',constructionYears:'Byggtid',constructionShare:'Andel med byggtid',
    liquidityPolicy:'Kassapolicy',cashReserve:'Kassareserv',deferInvestmentShare:'Flyttad betalning',
    prefinanceShare:'Förfinansiering',workingCapitalEnabled:'Rörelsekapital',firstYearGrantAdvance:'Bidragsförskott',
    collectionDays:'Kundfordringar, dagar',paymentDays:'Leverantörsskulder, dagar',employerContributionRate:'Sociala avgifter',
    projectChoice:'Projekt'};
  const diffs=Object.entries(keys).filter(([key])=>scenario.run.assumptions[key]!==reference.run.assumptions[key]);
  if(!diffs.length) return;
  const options={timeModel:'time-model',revenueMode:'revenue-mode',demographyMode:'demography-mode',migrationProfile:'migration-profile',projectChoice:'project-choice'};
  const shares=['constructionShare','deferInvestmentShare','prefinanceShare'];
  const format=(key,x)=>{
    if(x==null) return 'Basvärde';
    if(options[key]) return [...$(options[key]).options].find(o=>o.value===String(x))?.text??String(x);
    if(shares.includes(key)) return `${decimal(x*100)} %`;
    return typeof x==='boolean'?(x?'På':'Av'):typeof x==='number'?decimal(x):String(x);
  };
  const rows=diffs.map(([key,label])=>[label,safe(format(key,scenario.run.assumptions[key])),safe(format(key,reference.run.assumptions[key]))]);
  $('comparison-context').insertAdjacentHTML('beforeend',comparisonTable('different-assumptions','Ändrade antaganden',
    ['Antagande',scenario.label,reference.label],rows,'Värden som modellen använder eller tolkar för respektive bana.'));
}
function prepareExplanation(scenario,reference) {
  const refs=new Map(reference.run.rows.slice(1).map(row=>[row.year,row]));
  const common=scenario.run.rows.slice(1).filter(row=>refs.has(row.year));
  if(!common.length) return;
  explanationRuns={scenario,reference,common,refs};
  const select=$('explanation-year'),selected=Number(select.value);
  select.replaceChildren(...common.map(row=>new Option(row.year,row.year)));
  select.value=common.some(row=>row.year===selected)?selected:common[0].year;
  $('comparison-explanation').hidden=false;
  renderExplanation();
}
function renderExplanation() {
  const {scenario,reference,common,refs}=explanationRuns;
  const year=Number($('explanation-year').value);
  const a=common.find(row=>row.year===year),b=refs.get(year);
  const metrics=[['population','Invånare',fmt,signedPeople],['population80Plus','Invånare 80+',fmt,signedPeople],
    ['educationIndex','Utbildningsbehov (bas = 100)',x=>decimal(x*100),{format:x=>signedMoney.format(x*100)}],
    ['careIndex','Omsorgsbehov (bas = 100)',x=>decimal(x*100),{format:x=>signedMoney.format(x*100)}],
    ['operatingCash','Driftkassa (mnkr)',decimal,signedMoney],['debt','Skuld (mnkr)',decimal,signedMoney]];
  const rows=metrics.map(([key,label,format,formatter])=>[label,a[key]==null?'—':format(a[key]),b[key]==null?'—':format(b[key]),change(a[key],b[key],formatter)]);
  const parts=[['tax','Skatt',1],['grants','Bidrag och utjämning',1],['cost','Nettodrift',-1],
    ['depreciation','Avskrivningar',-1],['interest','Ränta',-1],['otherFinancialExpense','Övriga finansiella kostnader',-1]];
  const bridge=parts.map(([key,label,sign])=>[label,change(sign*a[key],sign*b[key])]);
  const residual=a.result-b.result-parts.reduce((total,[key,,sign])=>total+sign*(a[key]-b[key]),0);
  if(Math.abs(residual)>1e-7) bridge.push(['Finansiella intäkter och övrigt',signedMoney.format(residual)]);
  bridge.push(['Skillnad i årets resultat',change(a.result,b.result)]);
  $('explanation-tables').innerHTML=comparisonTable('explanation-needs','Befolkning, behov och finansiering',['Mått',scenario.label,reference.label,'Skillnad'],rows,`Prognosår ${year}.`)+
    comparisonTable('explanation-result','Vad bygger upp resultatskillnaden?',['Post','Bidrag till skillnaden (mnkr)'],bridge,'En kostnadsökning ger ett negativt bidrag till resultatskillnaden.');
}
// Each draw asks the OpenModelica worker for every scenario it shows in one batch.
// While a batch runs, further input only marks the view dirty; the latest state is drawn next.
let drawing=false,dirty=false;
async function draw() {
  if(drawing){dirty=true;return;}
  drawing=true;
  try {do {dirty=false;await drawOnce();} while(dirty);}
  finally {drawing=false;}
}
const stressOverrides=(a,direction)=>({...overrides,taxGrowth:a.taxGrowth+direction*.7,wageGrowth:Math.max(0,a.wageGrowth-direction*.7),priceGrowth:Math.max(0,a.priceGrowth-direction*.4),migrationDelta:a.migrationDelta+direction*100,birthChange:a.birthChange+direction*5,interestRate:Math.max(0,a.interestRate-direction*.75)});
const sensitivityCases=[['wageGrowth',1,'Löneökning +1 procentenhet'],['interestRate',1,'Låneränta +1 procentenhet'],['migrationDelta',100,'Flyttnetto +100 personer/år'],['investment',100,'Investeringar +100 mnkr/år']];
// Consecutive years as ranges: [2028,2029,2030,2032] -> "2028–2030 och 2032".
function yearRanges(years){
  const parts=[];
  for(const year of years){const last=parts.at(-1);if(last&&year===last[1]+1)last[1]=year;else parts.push([year,year]);}
  const text=parts.map(([a,z])=>a===z?String(a):`${a}–${z}`);
  return text.length>1?`${text.slice(0,-1).join(', ')} och ${text.at(-1)}`:text[0];
}
function resultTarget(){
  const el=$('result-target');
  return el.value===''||!el.validity.valid?null:Number(el.value);
}
function renderBalanceFlag(deficits,belowTarget,target,rows){
  const period=forecastPeriod(rows),parts=[];
  parts.push(deficits.length
    ?`<strong>Underskott ${yearRanges(deficits)}.</strong> Kommunallagen kräver att budgeten har ett överskott (11 kap. 5 §) och att ett negativt balanskravsresultat regleras inom tre år (11 kap. 12 §).`
    :`<strong>Inget underskott ${period}.</strong>`);
  if(target!=null) parts.push(belowTarget.length
    ?`Under resultatmålet ${decimal(target)} % av skatt och bidrag: ${yearRanges(belowTarget)}.`
    :`Resultatmålet ${decimal(target)} % nås ${deficits.length?'de år som inte har underskott':'alla år'}.`);
  parts.push('Modellens resultat är årets resultat. Balanskravsresultatet räknar dessutom bort bland annat realisationsvinster.');
  $('balance-flag').className='balance-flag'+(deficits.length?' warning':'');
  $('balance-flag').innerHTML=parts.join(' ');
}
async function drawOnce() {
  try {
    const a={...b.assumptions,...overrides},stressed=path?[]:[-1,1];
    const scenarioKey=JSON.stringify([b.municipality,b.baseYear,a,!!b.planningInputs,path]);
    const choices=comparisonSelectors.map(select=>select.value);
    const requests=[{overrides,revenuePath:path},{overrides:{},revenuePath:path},
      ...stressed.map(d=>({overrides:stressOverrides(a,d),revenuePath:path})),
      ...sensitivityCases.map(([k,d])=>({overrides:{...overrides,[k]:a[k]+d},revenuePath:path}))];
    const comparisonIndex=requests.length;
    const presetIndexes=new Map([['latest',0],['base',1]]);
    for(const choice of choices) {
      if(choice in presets&&!presetIndexes.has(choice)) {
        presetIndexes.set(choice,requests.length);
        requests.push({overrides:presetOverrides(choice),revenuePath:path});
      }
    }
    const results=await engine.simulateMany(b,history,requests);
    if(dirty) return;
    for(const r of results.slice(0,2)) if(r.error) throw Error(r.error);
    if(run&&scenarioKey!==lastScenarioKey) previousRun=run;
    lastScenarioKey=scenarioKey;
    for(const select of comparisonSelectors) select.querySelector('option[value="previous"]').disabled=!previousRun;
    const circular=path?.provenance?.circular??(path?.vintage==='2026-10-06'?'26:28':null);
    for(const result of results) if(result.run) result.run.context={
      municipality:b.municipality,basis:path?`SKR ${circular?`${circular} · `:''}${path.vintage}`:b.planningInputs?'Nationella SKR-antaganden':'Egna grundantaganden'};
    // The address always describes the scenario on screen, so a reload or a copied address gives the same view.
    if(!document.body.classList.contains('picking')) window.history.replaceState(null,'',shareUrl());
    run=results[0].run;base=results[1].run;latestSettings=snapshotSettings();version++;modelView?.update(run);$('error').hidden=true;$('engine').textContent=ENGINE;
    const stressRuns=results.slice(2,2+stressed.length),sensitivityRuns=results.slice(2+stressed.length,comparisonIndex);
    const end=run.rows.at(-1),initial=run.rows[0],margin=end.result/(end.tax+end.grants)*100;
    $('metrics').innerHTML=[['Resultat '+end.year,fmt(end.result),'mnkr',`${decimal(margin)} % av skatt och bidrag`],['Banklåneskuld '+end.year,fmt(end.debt),'mnkr',`${fmt(end.debt-initial.debt)} mnkr förändring från ${b.baseYear}`],['Invånare '+end.year,fmt(end.population),'pers.',`${fmt(end.population-initial.population)} personer från ${b.baseYear}`]].map(([label,value,unit,detail])=>`<div class="metric"><div class="metric-label">${label}</div><div class="metric-number">${value}<small>${unit}</small></div><div class="metric-detail">${detail}</div></div>`).join('');
    const stresses=stressRuns.map((r,i)=>r.run?{name:'Stress '+(stressed[i]<0?'svag':'stark'),values:r.run.rows.map(x=>x.result),color:'#b4c0ae',thin:true}:null).filter(Boolean);
    const target=resultTarget(),forecastRows=run.rows.slice(1);
    const deficits=forecastRows.filter(r=>r.result<0).map(r=>r.year);
    const belowTarget=target==null?[]:forecastRows.filter(r=>r.result>=0&&100*r.result/(r.tax+r.grants)<target).map(r=>r.year);
    const targetSeries=target==null?[]:[{name:`Resultatmål ${decimal(target)} %`,values:run.rows.map(r=>target/100*(r.tax+r.grants)),color:'#516e9c',dash:true,thin:true}];
    chart('result-chart',[...stresses,...targetSeries,{name:'Grundbana',values:base.rows.map(r=>r.result),color:'#ad8053',dash:true},{name:'Ditt scenario',values:run.rows.map(r=>r.result),color:'#17634e'}],
      {unit:'mnkr',bands:run.rows.map((r,i)=>i>0&&r.result<0?i:-1).filter(i=>i>0)});
    $('target-legend').hidden=target==null;
    renderBalanceFlag(deficits,belowTarget,target,forecastRows);
    document.querySelector('.legend-line.stress').hidden=!!path;
    chart('debt-chart',[{name:'Grundbana',values:base.rows.map(r=>r.debt),color:'#ad8053',dash:true},{name:'Låneskuld',values:run.rows.map(r=>r.debt),color:'#17634e'}],{unit:'mnkr',height:205});
    const sensitivities=sensitivityCases.map(([,,label],i)=>({label,delta:sensitivityRuns[i].run?sensitivityRuns[i].run.rows.at(-1).result-end.result:NaN}));
    const max=Math.max(...sensitivities.filter(s=>Number.isFinite(s.delta)).map(s=>Math.abs(s.delta)),1);$('sensitivity').innerHTML=sensitivities.map(s=>`<div class="sensitivity-row"><div class="sensitivity-label"><span>${s.label}</span><strong>${Number.isFinite(s.delta)?`${s.delta>0?'+':''}${fmt(s.delta)} mnkr`:'—'}</strong></div><div class="sensitivity-track"><div class="sensitivity-fill ${s.delta>0?'positive':''}" style="width:${Number.isFinite(s.delta)?Math.abs(s.delta)/max*100:0}%"></div></div></div>`).join('');
    const colors=['#17634e','#80a979','#c8d779','#ad8053','#516e9c'];chart('population-chart',b.ageGroups.map((name,i)=>({name,values:run.rows.map(r=>r.cohorts[i]),color:colors[i]})),{unit:'personer'});
    $('age-legend').innerHTML=b.ageGroups.map((x,i)=>`<span><span style="color:${colors[i]}">●</span> ${x}</span>`).join('');chart('demand-chart',[{name:'Utbildning',values:run.rows.map(r=>r.educationIndex*100),color:'#17634e'},{name:'Äldreomsorg',values:run.rows.map(r=>r.careIndex*100),color:'#ad8053'}],{unit:'index'});
    $('revenue-status').textContent=path?`SKR-referens för ${b.name} · ${path.vintage}`:(b.planningInputs?'Nationella SKR-antaganden · lokal intäktsbana enligt modellen':'Illustrativ intäktsbana · SKR ej importerad');$('clear-import').hidden=!path;
    for(const k of ['taxGrowth','grantGrowth']){$(k).disabled=!!path;$(k+'-range').disabled=!!path;}
    const exactRevenue=!!path&&a.revenueMode===1;
    $('taxRate').disabled=exactRevenue;
    $('taxRate-range').disabled=exactRevenue;
    $('regulation-held').disabled=exactRevenue||!$('planning-enabled').checked||$('regulation-control').hidden;
    const population=a.demographyMode==='legacy'
      ?b.planningInputs?.demography==='calibrated'?'historiskt kalibrerade flyttflöden':'befolkningsprognos'
      :$('demography-mode').selectedOptions[0].text;
    $('planning-status').textContent=b.planningInputs?(path?`Aktivt: ${population}, SKR:s kommunvisa intäktsbana och årsvisa prisantaganden.`:`Aktivt: ${population} och SKR:s årsvisa prisantaganden.`):
      a.demographyMode!=='legacy'?`Aktiv befolkningsmodell: ${population}.`:
      $('planning-enabled').disabled?'SCB:s historik används för att kalibrera befolkningsmodellen.':'SKR:s planeringsunderlag är avstängda.';
    ledger();
    const comparisons=choices.map((choice,index)=>({
      choice,label:comparisonSelectors[index].selectedOptions[0].text,
      ...(choice==='previous'?{run:previousRun}:savedScenarios.find(item=>item.id===choice&&scenarioMunicipality(item)===activeMunicipality)??results[presetIndexes.get(choice)])
    }));
    renderComparisons(...comparisons);
  }catch(e){report(e);}
}
function download(name,text,type='text/plain'){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function renderEvidence(sources,backtest){$('sources').innerHTML=sources.map(s=>`<div class="source-row"><div><a href="${safe(s.url)}" target="_blank" rel="noopener">${safe(s.title)} ↗</a><p>${safe(s.publisher)} · ${safe(s.use)}</p></div><span class="source-status">${safe(s.status)}</span></div>`).join('');if(backtest){$('backtest').innerHTML=`<p class="score">${decimal(backtest.scores.cohort)} <small>personer, modellens genomsnittliga absoluta fel</small></p><div class="table-wrap"><table><thead><tr><th>Metod</th><th>MAE, personer</th></tr></thead><tbody>${Object.entries(backtest.scores).map(([k,v])=>`<tr><td>${({cohort:'Åldersmodell',persistence:'Oförändrad befolkning',trend:'Senaste förändring'})[k]}</td><td>${decimal(v)}</td></tr>`).join('')}</tbody></table></div><p class="muted" style="margin-top:15px">${safe(backtest.conclusion)}</p>`;}else $('backtest').textContent='Kör projektets backtest för att skapa utvärderingsresultat.';}
function renderPlanning(){
  $('planning-revenue-note').textContent=planning.revenueImport.message;
  const revenue=planning.revenuePath;
  $('planning-revenues').innerHTML=revenue?`<caption>Omräknad SKR-referens för Motala. Mnkr; befolkning avser 1 november året före intäktsåret. Scenariots justerade belopp visas i resultat-tabellen.</caption><thead><tr><th scope="col">År</th><th scope="col">Skatt inkl. avräkningar</th><th scope="col">Bidrag, utjämning &amp; fastighetsavgift</th><th scope="col">Summa</th><th scope="col">Referensbefolkning</th></tr></thead><tbody>${revenue.rows.map(r=>`<tr><th scope="row">${r.year}</th><td>${decimal(r.tax)}</td><td>${decimal(r.grants)}</td><td>${decimal(r.tax+r.grants)}</td><td>${fmt(r.population)}</td></tr>`).join('')}</tbody>`:'';
  $('planning-rates').innerHTML=`<caption>Årsvisa SKR-antaganden. Procentuell förändring, inte prognoser för kommunens intäktsbelopp.</caption><thead><tr><th scope="col">År</th><th scope="col">Skatteunderlag</th><th scope="col">Arbetskraft</th><th scope="col">Övrig förbrukning</th></tr></thead><tbody>${planning.rows.map(r=>`<tr><th scope="row">${r.year}</th><td>${decimal(r.taxBaseGrowth)} %</td><td>${decimal(r.labourCostGrowth)} %</td><td>${decimal(r.otherPriceGrowth)} %</td></tr>`).join('')}</tbody>`;
  $('planning-older').innerHTML=`<caption>Källprognos, personer. Dessa grupper summeras till modellens 65+; separata omsorgsintensiteter är ännu inte skattade.</caption><thead><tr><th scope="col">År</th><th scope="col">65–79 år</th><th scope="col">80–89 år</th><th scope="col">90+ år</th><th scope="col">Totalt, alla åldrar</th></tr></thead><tbody>${planning.rows.map(r=>`<tr><th scope="row">${r.year}</th>${r.olderGroups.map(v=>`<td>${fmt(v)}</td>`).join('')}<td>${fmt(r.sourceTotal)}</td></tr>`).join('')}</tbody>`;
  $('planning-kolada').innerHTML=`<caption>Senaste tillgängliga totalvärde per serie. År och enhet varierar; värdena används som jämförelseunderlag.</caption><thead><tr><th scope="col">Nyckeltal</th><th scope="col">År</th><th scope="col">Värde</th></tr></thead><tbody>${planning.koladaLatest.map(r=>`<tr><th scope="row"><details><summary>${safe(r.title)}</summary><p>${safe(r.description)}</p><p>${safe(r.id)}${r.status?' · '+safe(r.status):''}</p></details></th><td>${r.year}</td><td>${decimal(r.value)}</td></tr>`).join('')}</tbody>`;
  $('planning-documents').innerHTML=planning.documents.map(r=>`<a class="button secondary" href="${safe(r.file)}" download>${safe(r.title)} ↓</a>`).join('');
  $('planning-limitations').innerHTML=planning.limitations.map(x=>`<li>${safe(x)}</li>`).join('');
}
// Why the accounts did not become what was believed: the model from the 2021 accounts with one cause at a time set to
// what happened (scripts/explain_outcome.py, in series.json). Shown for the municipality the page shows.
async function renderOutcomeExplanation(code) {
  seriesData??=await fetch('series.json').then(r=>r.ok?r.json():Promise.reject(Error('series.json saknas')));
  if(code!==activeMunicipality) return;
  const m=seriesData.municipalities[code],e=m.explanation,years=e.years,name=m.name;
  const head=first=>`<thead><tr><th scope="col">${first}</th>${years.map(y=>`<th scope="col">${y}</th>`).join('')}</tr></thead>`;
  const cells=(values,format=fmt)=>values.map(v=>`<td${v<0?' class="negative"':''}>${v==null?'–':format(Math.round(v))}</td>`).join('');
  const signed=v=>signedPeople.format(v);
  $('outcome-explanation').hidden=false;
  $('outcome-explanation-lede').textContent=`${name} från bokslut ${e.baseYear}. Första raden är modellen med det man trodde då. På varje rad därefter är en sak till satt till det som faktiskt hände. Bara indata ändras, inga ekvationer. Sista raden är bokslutet.`;
  const last=e.steps.at(-1).result;
  $('outcome-explanation-steps').innerHTML=`<caption>Årets resultat, mnkr. Stegen läggs på varandra uppifrån och ned.</caption>${head('Resultat')}<tbody>${e.steps.map((s,i)=>`<tr><th scope="row">${i?'+ ':''}${safe(s.label)}</th>${cells(s.result)}</tr>`).join('')}<tr><th scope="row">Kvar att förklara</th>${cells(last.map((v,i)=>v-e.outcome.result[i]),signed)}</tr><tr><th scope="row">Bokslut</th>${cells(e.outcome.result)}</tr></tbody>`;
  const lines=[['otherCosts','Övriga kostnader'],['payroll','Löner och avgifter'],['operatingRevenue','Verksamhetens intäkter'],['tax','Skatt'],['grants','Generella bidrag'],['depreciation','Avskrivningar'],['interest','Räntekostnad'],['otherFinancialNet','Finansiella poster utöver ränta'],['result','Resultat']].filter(([k])=>e.remaining[k]);
  $('outcome-explanation-remaining').innerHTML=`<caption>Modellen med utfallen insatta minus bokslutet, mnkr. Högre kostnader och lägre intäkter i modellen ger lägre resultat.</caption>${head('Rad')}<tbody>${lines.map(([k,label])=>`<tr><th scope="row">${label}</th>${cells(e.remaining[k],signed)}</tr>`).join('')}</tbody>`;
  const believed=e.steps[0].result,against=values=>values.map((v,i)=>v-believed[i]),sc=e.inflationScenario;
  $('outcome-explanation-scenario').innerHTML=`<caption>Resultatet jämfört med raden "Som man trodde då", mnkr. Prisöverraskningen var ${sc.priceSurprise.map(v=>decimal(100*v)).join(', ')} procentenheter ${years[0]}–${years.at(-1)}.</caption>${head('Resultat mot det man trodde')}<tbody><tr><th scope="row">Inflationsscenariot, bara prischocken</th>${cells(against(sc.mechanism),signed)}</tr><tr><th scope="row">+ staten kompenserar bidragen året efter</th>${cells(against(sc.compensated),signed)}</tr><tr><th scope="row">Bokslut</th>${cells(against(e.outcome.result),signed)}</tr></tbody>`;
  const t=e.taxAndGrants,gap=(forecast,i)=>forecast==null?null:forecast-t.outcome[i];
  const skr=t.skr.map(f=>[`SKR ${f.circular} (${f.published})`,years.map((y,i)=>gap(f.rows.find(r=>r.year===y)?.forecast,i))]);
  $('outcome-explanation-revenue').innerHTML=`<caption>Prognos minus utfall för skatt och generella bidrag, mnkr. Minus betyder att prognosen låg under utfallet.</caption>${head('Prognos')}<tbody>${[...skr,[`Modellen från bokslut ${e.baseYear}`,t.believed.map((v,i)=>gap(v,i))]].map(([label,values])=>`<tr><th scope="row">${safe(label)}</th>${cells(values,signed)}</tr>`).join('')}<tr><th scope="row">Utfall</th>${cells(t.outcome)}</tr></tbody>`;
  const b=e.inputs.believed,o=e.inputs.outcome,pct=v=>decimal(100*v);
  $('outcome-explanation-note').textContent=`Trodde då (SKR:s decembercirkulär ${e.baseYear}) och utfall, procent per år: löner ${years.map(y=>`${pct(b[y].wages)}→${pct(o[y].wages)}`).join(', ')}; priser ${years.map(y=>`${pct(b[y].prices)}→${pct(o[y].prices)}`).join(', ')}; rikets skatteunderlag ${years.map(y=>`${pct(b[y].taxBase)}→${pct(o[y].taxBase)}`).join(', ')}. Löner och priser är SKR:s index för riket (PKV); arbetskraftsindexet innehåller även arbetsgivarens pensionspåslag. ${e.inputs.beyondCircular.length?`Cirkuläret når inte ${e.inputs.beyondCircular.join(', ')}; där gäller dess sista takt. `:''}Utfall: ${code===DEFAULT_MUNICIPALITY?'kommunens årsredovisningar':'SCB:s räkenskapssammandrag'}. SKR:s äldre prognoser är lästa ur arbetsböcker återfunna i Internet Archive. Modellens körning utgår från bokslutet och decembercirkuläret, som kom efter SKR 21:35; prognosdatumen är alltså inte desamma. Ordningen på stegen är vald; där orsaker samverkar kan ett stegs andel bli en annan med en annan ordning.`;
}
function renderMunicipalityEvidence(period) {
  const code=period.baseline.municipality,{name,packageName}=municipalities[code];
  $('municipality-evidence-title').textContent=`Källor för ${name}`;
  const links=[
    [`Bokslut ${period.baseline.baseYear}`,period.sources.accounts],
    ...(period.sources.accounts.endsWith('/TAB6777')?[]:[['SCB:s resultaträkning, TAB6777','https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6777']]),
    ['SCB:s balansräkning, TAB6779','https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6779'],
    ['Folkmängd, Kolada N01951',period.sources.population],['Kolada','https://www.kolada.se/'],
    ['SCB:s flyttningar efter ålder och kön, TAB1212','https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB1212'],
    ...(period.planning?[['SKR:s decembercirkulär 2024',period.planning.sources.skr]]:[])
  ];
  $('municipality-sources').innerHTML=links.map(([label,url])=>`<li><a href="${safe(url)}">${safe(label)}</a></li>`).join('');
  $('municipality-skr-download').hidden=!regional[code].current.skrRevenue;
  $('municipality-skr-download').href=`municipalities/${code}/skr-revenue-path.json`;
  $('municipality-backtest-download').hidden=code!=='0562';
  $('municipality-package').href=`${packageName}.mo`;
  $('municipality-package').textContent=`Hämta ${packageName}.mo ↓`;
}
// A scenario as a link: the municipality, period and every changed assumption and model option.
// The page's side of the AI tools (ai-tools.js): values in the units of the controls, as the user sees them.
let seriesData=null;
async function settled(){await draw();while(drawing)await new Promise(r=>setTimeout(r,50));if(!$('error').hidden)throw Error($('error').textContent);}
function assumptionList(){
  return controlDefinitions([...definitions,...advanced]).map(([key,label,min,max,step,unit,help])=>({key,label,unit,min,max,step,
    value:Number(((overrides[key]??b.assumptions[key])-(sourcedRate(key)?b.assumptions[key]:0)).toFixed(4)),
    default:sourcedRate(key)?0:b.assumptions[key],changed:changedKey(key),locked:$(key).disabled,help,explanation:explanations[key]??''}));
}
function toOverrides(values){
  const list=new Map(assumptionList().map(a=>[a.key,a]));
  return Object.fromEntries(Object.entries(values).map(([k,v])=>{
    if(list.get(k)?.locked) throw Error(`${list.get(k).label} är låst i det här läget (till exempel av SKR:s kommunvisa intäkter).`);
    return [k,v+(sourcedRate(k)?b.assumptions[k]:0)];
  }));
}
function logAi(text){$('ai-log-empty').hidden=true;const item=document.createElement('li');item.textContent=`${new Date().toLocaleTimeString('sv-SE')} ${text}`;$('ai-log').prepend(item);while($('ai-log').children.length>30)$('ai-log').lastChild.remove();}
const aiAdapter={
  state:()=>({municipality:activeMunicipality,name:municipalities[activeMunicipality].name,baseYear:b.baseYear,
    forecastYears:[b.baseYear+1,b.baseYear+b.assumptions.years],
    revenue:path?`SKR:s kommunvisa intäkter (${path.vintage})`:b.planningInputs?'SKR:s årsvisa antaganden':'Illustrativa antaganden',
    timeModel:b.assumptions.timeModel==='continuous'?'kontinuerlig tid (Kommunekonomi.Continuous.Economy): flöden under året, årsvärden vid bokslutet':'årssteg (Kommunekonomi.Annual)',
    changed:Object.fromEntries(assumptionList().filter(a=>a.changed).map(a=>[a.key,a.value]))}),
  municipalities:()=>Object.entries(municipalities).map(([code,{name,firstYears}])=>({code,name,startYears:firstYears})),
  assumptions:assumptionList,
  results:()=>run?.rows??null,
  async preview(values){
    const [result]=await engine.simulateMany(b,history,[{overrides:{...overrides,...toOverrides(values)},revenuePath:path}]);
    if(result.error) throw Error(result.error);
    return result.run.rows;
  },
  async apply(values,reason){
    Object.assign(overrides,toOverrides(values));$('preset').value='custom';syncControls();
    logAi(`Ändrade ${Object.entries(values).map(([k,v])=>`${k} = ${v}`).join(', ')}${reason?`: ${reason}`:''}`);
    await settled();return run.rows;
  },
  async reset(reason){overrides={};$('preset').value='base';syncControls();logAi(`Återställde antagandena${reason?`: ${reason}`:''}`);await settled();return run.rows;},
  async select(code,startYear){
    const url=new URL(location.href);url.search='';url.searchParams.set('kommun',code);if(startYear!==2026)url.searchParams.set('start',startYear);
    window.history.pushState(null,'',url);openMunicipality(code,startYear);logAi(`Valde ${municipalities[code].name}, start ${startYear}`);await settled();
  },
  async series(name,code){
    code=code??activeMunicipality;
    if(['skrPlanning','skrRevenue'].includes(name)){
      if(code!==activeMunicipality) throw Error('SKR-serierna gäller kommunen sidan visar; välj den först med select_municipality.');
      if(name==='skrPlanning') return b.planningInputs?{municipality:code,unit:'procent per år',sources:b.planningInputs.sources,rows:b.planningInputs.rows}:{municipality:code,rows:[],note:'Planeringsunderlagen är avstängda eller saknas för perioden.'};
      return path?{municipality:code,unit:'mnkr; befolkning 1 november året före',vintage:path.vintage,source:path.source??path.provenance?.workbook,rows:path.rows}:{municipality:code,rows:[],note:'Ingen SKR-bana för kommunen och perioden.'};
    }
    seriesData??=await fetch('series.json').then(r=>r.ok?r.json():Promise.reject(Error('series.json saknas')));
    if(name in {pkv:1,nationalPopulation:1,hindcast:1,responses:1,explanationSummary:1}) return seriesData.national[name==='nationalPopulation'?'population':name];
    const m=seriesData.municipalities[code];
    if(!m) throw Error(`Okänd kommun ${code}.`);
    return {municipality:code,name:m.name,...m[name]};
  }
};
function setupAiLink(){
  let link=null;
  try{$('ai-address').value=localStorage.getItem('motala.ai-address')||$('ai-address').value;}catch{}
  const status=(state,text='')=>{
    const labels={connected:'Kopplad. Ett AI-program kan nu använda sidan via bryggan.',closed:'Frånkopplad.',error:'Fel: '};
    $('ai-status').textContent=(labels[state]??'')+(state==='error'?text:text&&state!=='connected'?` ${text}`:'');
    $('ai-connect').textContent=state==='connected'?'Koppla från':'Koppla';
    $('ai-toggle').dataset.state=state;
    $('ai-toggle-state').textContent=state==='connected'?'kopplad':state==='error'?'fel':'av';
    if(state!=='connected') link=null;
  };
  // The panel on the right: open or closed is remembered; Escape closes it and gives the button the focus back.
  const show=(open,focus=false)=>{
    $('ai-panel').hidden=!open;
    $('ai-toggle').setAttribute('aria-expanded',String(open));
    document.body.classList.toggle('ai-open',open);
    try{localStorage.setItem('motala.ai-panel',open?'open':'closed');}catch{}
    if(focus)(open?$('ai-address'):$('ai-toggle')).focus();
  };
  $('ai-toggle').onclick=()=>show($('ai-panel').hidden,true);
  $('ai-close').onclick=()=>show(false,true);
  $('ai-panel').onkeydown=e=>{if(e.key==='Escape')show(false,true);};
  let remembered=null;
  try{remembered=localStorage.getItem('motala.ai-panel');}catch{}
  if(remembered==='open')show(true);
  $('ai-address').oninput=()=>{$('ai-remote').hidden=isLoopback($('ai-address').value);};
  $('ai-connect').onclick=()=>{
    if(link){link.close();return;}
    const address=$('ai-address').value.trim();
    try{
      link=connectAi({address,token:$('ai-token').value.trim(),adapter:aiAdapter,onStatus:status,
        onCall:(call,answer)=>{if(!['set_assumptions','reset_assumptions','select_municipality'].includes(call.name))logAi(`${call.name}${answer.error?` (fel: ${answer.error})`:''}`);}});
      try{localStorage.setItem('motala.ai-address',address);}catch{}
      $('ai-status').textContent='Kopplar …';
    }catch(e){status('error',e.message);}
  };
}
const SHARE_VERSION=1;
function shareUrl(){
  const url=new URL(location.href);
  url.search='';url.hash='';
  url.searchParams.set('kommun',activeMunicipality);
  url.searchParams.set('start',b.baseYear+1);
  url.searchParams.set('slut',b.baseYear+b.assumptions.years);
  const controls=Object.fromEntries(savedControlIds.filter($).map(id=>[id,$(id).type==='checkbox'?$(id).checked:$(id).value])
    .filter(([id,value])=>{const el=$(id);return el.type==='checkbox'?value!==el.defaultChecked:el.tagName==='SELECT'?el.selectedIndex!==Math.max(0,[...el.options].findIndex(o=>o.defaultSelected)):value!==el.defaultValue;}));
  const state={v:SHARE_VERSION,p:$('preset').value,o:overrides,c:controls,...(resultTarget()!=null?{t:resultTarget()}:{})};
  if(state.p==='base'&&!Object.keys(overrides).length&&!Object.keys(controls).length&&state.t===undefined) return url;
  url.searchParams.set('s',btoa(JSON.stringify(state)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''));
  return url;
}
// Only known keys and plain values are accepted; anything else in the link is ignored.
function readShared(text){
  try{
    const state=JSON.parse(atob(text.replace(/-/g,'+').replace(/_/g,'/')));
    if(state?.v!==SHARE_VERSION) return null;
    const keys=new Set([...definitions,...advanced].map(d=>d[0]));
    const o=Object.fromEntries(Object.entries(state.o??{}).filter(([k,v])=>keys.has(k)&&Number.isFinite(v)));
    const c=Object.fromEntries(Object.entries(state.c??{}).filter(([k,v])=>savedControlIds.includes(k)&&['string','boolean'].includes(typeof v)));
    const p=state.p in presets||state.p==='custom'?state.p:'base';
    return {o,c,p,t:Number.isFinite(state.t)?state.t:null};
  }catch(e){return null;}
}
function applyShared(state,firstYear,endYear){
  for(const [id,value] of Object.entries(state.c)){const el=$(id);if(el.type==='checkbox')el.checked=value;else el.value=value;}
  if(state.t!=null) $('result-target').value=state.t;
  const ends=Array.from({length:MAX_YEARS},(_,i)=>firstYear+i);
  selectPeriod(firstYear,{overrides:state.o,preset:state.p,...(ends.includes(endYear)?{endYear}:{})});
}
function renderMunicipalityCards(){
  const ordered=Object.entries(municipalities).sort(([,a],[,b])=>a.name.localeCompare(b.name,'sv'));
  $('municipality-cards').innerHTML=ordered.map(([code,{name}])=>{
    const base=regional[code].current.baseline,revenue=base.tax+base.grants,share=100*base.publishedResult/revenue;
    return `<a class="municipality-card" href="?kommun=${code}" data-code="${code}"><span class="card-name">${safe(name)}</span><span class="card-code">${code}</span>
      <dl><div><dt>Invånare</dt><dd>${fmt(base.reportedPopulation)}</dd></div><div><dt>Resultat ${base.baseYear}</dt><dd class="${base.publishedResult<0?'negative':''}">${signedMoney.format(Math.round(base.publishedResult))} mnkr</dd></div>
      <div><dt>Av skatt och bidrag</dt><dd>${decimal(share)} %</dd></div><div><dt>Skattesats</dt><dd>${decimal(base.taxRate)} %</dd></div></dl></a>`;
  }).join('');
  const year=regional[DEFAULT_MUNICIPALITY].current.baseline.baseYear;
  $('cards-note').innerHTML=`Bokslut ${year} för kommunen, inte koncernen: <a href="https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB6777">SCB:s räkenskapssammandrag</a>, för Motala årsredovisningen. Invånare 31 december ${year}.`;
}
function showStart(){
  document.body.classList.add('picking');
  $('start-view').hidden=false;
  $('municipality-brand').textContent='Östergötlands';
  $('municipality-code').textContent='13 kommuner';
  document.title='Ekonomilabb · Östergötlands kommuner';
  window.scrollTo(0,0);
}
function openMunicipality(code,firstYear=null){
  document.body.classList.remove('picking');
  $('start-view').hidden=true;
  selectMunicipality(code,firstYear);
}
// Show what the address says: the cards without a municipality, otherwise the lab.
function route(){
  const query=new URLSearchParams(location.search),code=query.get('kommun');
  if(!Object.hasOwn(municipalities,code)){showStart();return;}
  const firstYear=Number(query.get('start')),endYear=Number(query.get('slut'));
  openMunicipality(code,firstYear);
  const shared=query.get('s')&&readShared(query.get('s'));
  if(shared) applyShared(shared,b.baseYear+1,endYear);
  else if(endYear>b.baseYear&&endYear<=b.baseYear+MAX_YEARS) selectPeriod(b.baseYear+1,{endYear});
}
async function boot(){try{
  $('engine').textContent='Hämtar OpenModelica…';
  const mib=x=>(x/1048576).toFixed(0);
  engine=createWorkerEngine({
    onProgress:(loaded,total)=>{$('engine').textContent=total?`Hämtar OpenModelica ${Math.round(loaded/total*100)} % (${mib(total)} MB)`:`Hämtar OpenModelica ${mib(loaded)} MB`;},
    onCompiling:()=>{$('engine').textContent='Kompilerar modellen…';}});
  engine.ready.catch(report);
  modelView=createModelView($('model-view'),{source:fetch('Kommunekonomi.mo').then(r=>r.ok?r.text():Promise.reject(Error('Kommunekonomi.mo')))});
  const files=await Promise.all(['baseline.json','history.json','sources.json','backtest.json','municipal-benchmarks.json','planning-inputs.json','replay-2022.json','model-experiments.json','age-income.json','municipalities-data.json','rate-fixing.json'].map(async f=>{const r=await fetch(f);if(!r.ok){if(f==='backtest.json')return null;throw Error(`Kunde inte läsa ${f}`);}return r.json();}));
  current={baseline:files[0],history:files[1].rows};
  planning=files[5];
  replay=files[6];
  experiments=files[7].municipalities['0583'];
  ageIncome=files[8];
  regional=files[9];
  rateFixingTable=files[10];
  outcomeBudgetMotala=files[4].rows.find(row=>row.stage==='budget')?.forecast;
  const ordered=Object.entries(municipalities).sort(([,a],[,b])=>a.name.localeCompare(b.name,'sv'));
  for(const [code,{name}] of ordered) $('municipality').add(new Option(name,code));
  $('municipality').onchange=()=>{
    const code=$('municipality').value,url=new URL(location.href);
    const selected=Number($('start-year').value);
    const startYear=municipalities[code].firstYears.includes(selected)?selected:municipalities[code].firstYears[0];
    url.searchParams.set('kommun',code);
    if(startYear===2026) url.searchParams.delete('start');
    else url.searchParams.set('start',startYear);
    window.history.replaceState(null,'',url);
    selectMunicipality(code,startYear);
  };
  setupSavedScenarios();
  setupAiLink();
  $('explanation-year').onchange=renderExplanation;
  renderMunicipalityCards();
  $('municipality-cards').addEventListener('click',event=>{
    const card=event.target.closest('[data-code]');
    if(!card||event.metaKey||event.ctrlKey||event.shiftKey) return;
    event.preventDefault();
    window.history.pushState(null,'',`?kommun=${card.dataset.code}`);
    openMunicipality(card.dataset.code);
  });
  for(const id of ['all-municipalities','brand-link']) $(id).onclick=event=>{
    event.preventDefault();
    window.history.pushState(null,'',location.pathname);
    showStart();
  };
  window.addEventListener('popstate',route);
  route();
  renderEvidence(files[2],files[3]);renderPlanning();
  renderOutcomeExplanation(activeMunicipality).catch(()=>{$('outcome-explanation').hidden=true;});
  $('municipal-benchmarks').innerHTML=`<thead><tr><th scope="col">2025</th><th scope="col">Budget/prognos</th><th scope="col">Utfall</th><th scope="col">Absolut fel</th></tr></thead><tbody>${files[4].rows.map(r=>`<tr><th scope="row">${({budget:'Budget',april:'Aprilprognos',august:'Augustiprognos'})[r.stage]}</th><td>${fmt(r.forecast)}</td><td>${fmt(r.actual)}</td><td>${fmt(Math.abs(r.forecast-r.actual))}</td></tr>`).join('')}</tbody>`;
  document.querySelector('.controls').addEventListener('input',event=>{const el=event.target;if(!el.dataset.key)return;
    // An empty or half-typed number ("", "-", "2,") is not a value yet; wait for more input instead of computing with 0.
    if(el.value===''||el.validity.badInput)return;
    if(!el.validity.valid){report(Error('Värdet ligger utanför reglagets intervall.'));return;}
    const k=el.dataset.key;overrides[k]=Number(el.value)+(sourcedRate(k)?b.assumptions[k]:0);$('preset').value='custom';syncControls(el);draw();});
  // Normalise the number field's text once the user leaves it.
  document.querySelector('.controls').addEventListener('change',event=>{if(event.target.dataset.key)syncControls();});
  $('start-year').onchange=()=>{
    const firstYear=Number($('start-year').value),url=new URL(location.href);
    url.searchParams.set('start',firstYear);
    window.history.replaceState(null,'',url);
    selectPeriod(firstYear);
  };
  $('end-year').onchange=()=>{
    const endYear=Number($('end-year').value);
    if(customPath&&Array.from({length:endYear-b.baseYear},(_,i)=>b.baseYear+i+1).some(year=>!customPath.rows.some(r=>r.year===year))) {
      $('end-year').value=b.baseYear+b.assumptions.years;
      report(Error('Det importerade SKR-underlaget täcker inte det valda slutåret.'));
      return;
    }
    updatePeriod();
  };
  $('planning-enabled').onchange=()=>{customPath=undefined;updatePeriod();};
  for(const id of ['time-model','revenue-mode','demography-mode','split-payroll','employer-rate','construction-years','construction-share','migration-profile','age-tax','project-choice']) {
    $(id).onchange=()=>{
      if(!$('employer-rate').reportValidity()) return;
      if($('construction-years').value!=='0'&&!$('construction-share').reportValidity()) return;
      updateModelOptions();
      planningControls();
      draw();
    };
  }
  for(const id of ['liquidity-policy','cash-reserve','defer-investment-share','prefinance-share']) {
    $(id).onchange=()=>{
      $('liquidity-controls').hidden=!$('liquidity-policy').checked;
      if($('liquidity-policy').checked&&['cash-reserve','defer-investment-share','prefinance-share'].some(key=>!$(key).reportValidity())) return;
      updateModelOptions();
      draw();
    };
  }
  const workingCapitalFields=['collection-days','payment-days','grant-advance'];
  for(const id of ['working-capital-enabled',...workingCapitalFields]) {
    $(id).onchange=()=>{
      const enabled=$('working-capital-enabled').checked;
      $('working-capital-controls').hidden=!enabled;
      if(enabled&&workingCapitalFields.some(key=>!$(key).reportValidity())) return;
      updateModelOptions();
      draw();
    };
  }
  $('regulation-held').onchange=()=>{customPath=undefined;updatePeriod();};
  document.querySelectorAll('.tab').forEach(el=>el.addEventListener('click',()=>{document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!==el.dataset.tab);document.querySelectorAll('.tab').forEach(t=>{t.classList.toggle('active',t===el);t.setAttribute('aria-pressed',String(t===el));});}));
  $('docs-link').onclick=e=>{e.preventDefault();document.querySelector('.tab[data-tab="model"]').click();$('model').scrollIntoView({behavior:'smooth'});};
  $('reset').onclick=()=>{overrides={};$('preset').value='base';syncControls();draw();};
  $('preset').onchange=()=>{overrides={...presetOverrides($('preset').value)};syncControls();draw();};
  $('preset-buttons').innerHTML=[...$('preset').options].filter(o=>o.value!=='custom').map(o=>`<button type="button" class="preset-button" data-preset="${o.value}" aria-pressed="false">${safe(o.text)}</button>`).join('');
  $('preset-buttons').onclick=event=>{
    const button=event.target.closest('[data-preset]');
    if(!button||!b) return;
    $('preset').value=button.dataset.preset;
    $('preset').onchange();
  };
  $('assumption-groups').addEventListener('click',event=>{
    const info=event.target.closest('[data-info]'),reset=event.target.closest('[data-reset]');
    if(info){
      const text=$(info.dataset.info+'-info'),open=text.hidden;
      text.hidden=!open;info.setAttribute('aria-expanded',String(open));
    }
    if(reset){
      // A button inside <summary> would also open or close the group.
      event.preventDefault();
      const keys=assumptionGroups.find(([id])=>id===reset.dataset.reset)[3];
      for(const k of keys) delete overrides[k];
      $('preset').value=Object.keys(overrides).some(changedKey)?'custom':'base';
      syncControls();draw();
    }
  });
  $('result-target').oninput=()=>{if(run&&$('result-target').validity.valid)draw();};
  $('share').onclick=async()=>{
    if(!b) return;
    const url=shareUrl();
    window.history.replaceState(null,'',url);
    const note=customPath?' Ett importerat SKR-underlag följer inte med länken.':'';
    try{await navigator.clipboard.writeText(url.href);$('share-status').textContent='Länken är kopierad.'+note;}
    catch(e){$('share-status').textContent='Länken står i adressfältet.'+note;}
  };
  for(const select of comparisonSelectors) {
    const previous=select.querySelector('option[value="previous"]');
    for(const option of $('preset').options) {
      if(option.value in presets&&option.value!=='base') previous.before(option.cloneNode(true));
    }
    select.onchange=draw;
  }
  $('import').onchange=async e=>{try{const snapshot=b;const next=validateRevenuePath(JSON.parse(await e.target.files[0].text()),snapshot.baseYear,snapshot.municipality);await engine.simulate(snapshot,history,{...overrides,revenueMode:0},next);if(b===snapshot){customPath=next;updatePeriod();}}catch(e){report(e);}finally{$('import').value='';}};
  $('clear-import').onclick=()=>{customPath=null;updatePeriod();};
  $('pdf').onclick=async()=>{
    // Open the tab inside the click, before any await, or the popup blocker stops it.
    const tab=window.open('','_blank');
    if(!tab){report(Error('Tillåt att rapporten öppnas i en ny flik för att exportera PDF.'));return;}
    tab.document.write('<p style="font:14px sans-serif">Förbereder rapporten…</p>');
    try{
      // Recompute now so the report always matches the current controls, even after a rejected draw.
      const snapshot=b,revenuePath=path;
      const [current,reference]=await Promise.all([engine.simulate(snapshot,history,overrides,revenuePath),engine.simulate(snapshot,history,{},revenuePath)]);
      await draw();
      if(b!==snapshot) throw Error('Scenariot ändrades. Öppna exporten igen.');
      openScenarioReport({baseline:structuredClone(snapshot),run:current,referenceRun:reference,revenuePath:structuredClone(revenuePath),charts:Object.fromEntries(['result-chart','debt-chart','population-chart','demand-chart','sensitivity'].map(id=>[id,$(id).innerHTML]))},tab);
    }catch(e){tab.close();report(e);}};
  $('csv').onclick=()=>{if(!run||drawing)return;const keys=['year','population','tax','grants','payroll','pensionExpense','pensionCashPayments','otherOperatingExpense','operatingRevenue','cost','depreciation','interest','otherFinancialExpense','result','operatingCash','investment','debt','cash'];if(run.assumptions.constructionYears>0)keys.push('commissioned','workInProgress','assets');if(run.assumptions.liquidityPolicy)keys.push('outstandingDeferredInvestment','borrowing','prefinancing','repayment');if(run.assumptions.workingCapitalEnabled)keys.push('tradeReceivables','tradePayables','deferredGrants','workingCapitalCash');if(['planned','delay'].includes(run.assumptions.projectChoice))keys.push('projectPaid','projectCommissioned','projectWorkInProgress','projectPlacesInUse','missingProjectPlaces');download(`${municipalities[b.municipality].packageName.toLowerCase()}-scenario.csv`,keys.join(',')+'\n'+run.rows.map(r=>keys.map(k=>r[k]).join(',')).join('\n'),'text/csv');};
  $('json').onclick=$('municipal-json').onclick=async()=>{
    if(!run||drawing)return;
    const filename=`${municipalities[b.municipality].packageName.toLowerCase()}-scenario.json`;
    const scenario={municipality:b.municipality,baseYear:b.baseYear,baseline:b,history,overrides:run.assumptions,revenuePath:path,calibration:run.calibration,annualInputs:run.inputs,planningStatus:run.planningStatus,engine:run.engine,rows:run.rows,status:'Illustrative scenario, not validated forecast'};
    scenario.modelSource=await modelSource;
    download(filename,JSON.stringify(scenario,null,2),'application/json');
  };
  $('modelica').onclick=$('municipal-modelica').onclick=()=>{
    if(run&&!drawing)download('Scenario.mo',modelicaSource(b,history,overrides,path));
  };
  // The compiler is OSMC-PL/AGPL software: name its exact revision, source and licence.
  fetch('omc-web/manifest.json').then(r=>r.ok?r.json():null).then(m=>{if(!m)return;
    const commit=m.commit?`<a href="https://github.com/OpenModelica/OpenModelica/commit/${safe(m.commit)}">${safe(m.revision)}</a>`:safe(m.revision);
    $('omc-version').innerHTML=`Kompilator: OpenModelica ${commit} · <a href="omc-web/LICENSE-OpenModelica.txt">licens (OSMC-PL eller AGPL 3)</a> · <a href="${safe(m.source)}">källkod</a>`;}).catch(()=>{});
}catch(e){report(e);}}
boot();
