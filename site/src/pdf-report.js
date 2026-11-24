// A self-contained, printable snapshot of the current scenario. No remote services.
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=value=>value==null?'—':new Intl.NumberFormat('sv-SE',{maximumFractionDigits:2}).format(value);
const table=(headers,rows,caption='')=>`<table>${caption?`<caption>${escape(caption)}</caption>`:''}<thead><tr>${headers.map(h=>`<th scope="col">${escape(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map((v,i)=>i?`<td>${escape(v)}</td>`:`<th scope="row">${escape(v)}</th>`).join('')}</tr>`).join('')}</tbody></table>`;
const parameters=rows=>`<dl class="parameters">${rows.map(([name,value])=>`<div><dt>${escape(name)}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl>`;
const percent=x=>number(x)+' %';
const vector=(values,unit='')=>values.map(number).join(' / ')+(unit?' '+unit:'');
export function buildScenarioReport({baseline:b,run,referenceRun,revenuePath=null,charts={},generatedAt=new Date()}) {
  const name=b.name??'Motala';
  if(!run?.rows?.length||!run.inputs?.length||!referenceRun?.rows?.length)throw Error('Ett beräknat scenario behövs för PDF-export.');
  const a=run.assumptions,rows=run.rows,future=rows.slice(1),planning=b.planningInputs;
  const date=new Intl.DateTimeFormat('sv-SE',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Stockholm'}).format(new Date(generatedAt));
  const first=rows[0].year,last=rows.at(-1).year;
  const revenueLabel=revenuePath?`Importerad ${name}-referens, version ${revenuePath.vintage}`:planning?'Nationell SKR-trend med förenklad intäktsmodell':'Illustrativ intäktsbana';
  const populationVariants={
    observed:'Fem åldersgrupper med SCB:s flyttnetto',
    cohort:'Ettårsåldrar med kalibrerade restflöden',
    'cohort-observed':'Ettårsåldrar med SCB:s flyttnetto'
  };
  const populationLabel=populationVariants[a.demographyMode]??(planning&&planning.demography!=='calibrated'?'Källprognos, förankrad i bokslutets kohorter':'Historiskt kalibrerade restflöden');
  const revenueMode=revenuePath?['Proportionell justering','SKR:s publicerade bana','Justering per delpost'][a.revenueMode??0]:null;
  const firstProjected=planning?.rows.find(r=>r.projected)?.year;
  const extension=firstProjected?`Från ${firstProjected} används sista årets prisantaganden och kalibrerade flyttflöden. Importerade intäkter förlängs med den sista årsförändringen.`:'';
  const planningSource=planning?`SKR-underlag: ${escape(planning.sources.workbook)}, cirkulär ${escape(planning.sources.skrCircular)}.`:'';
  const populationSource=a.demographyMode?.includes('observed')
    ?'<a href="https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB1212">SCB:s in- och utflyttningar efter ålder och kön</a>.'
    :planning?.sources.population&&!run.cohort?`Befolkningskälla: <a href="${escape(planning.sources.population)}">regional statistikdatabas</a>.`:'';
  const flow=a.timeModel==='continuous';
  const common=[['Basår / horisont',`${first} / ${first+1}–${last}`],['Tid i modellen',flow?'Kontinuerlig tid: flöden under året':'Årssteg: ett steg per år'],['Intäktsunderlag',revenueLabel],['Befolkningsunderlag',populationLabel],
    ...(revenueMode?[['Intäktsmodell',revenueMode]]:[]),
    ...(a.splitPayroll?[['Personalkostnader','Löner, sociala avgifter och pensioner i separata banor']]:[])];
  const pages=[];
  const page=(title,content)=>pages.push({title,content});
  const graph=(id,legend)=>`<figure>${charts[id]||'<p>Grafen kunde inte hämtas. Se årstabellen.</p>'}<figcaption>${escape(legend)}</figcaption></figure>`;
  page('Årets resultat',graph('result-chart','Scenariot: grön linje. Grundbana: brun streckad linje, samma aktiva källor utan parameterändringar. Eventuella tunna linjer är illustrativa stresscenarier, inte sannolikhetsintervall.')+parameters([
    ...common,['Kommunal skattesats',percent(a.taxRate)],['Produktivitet / verksamhetsintäkter, årlig ökning',`${percent(a.productivity)} / ${percent(a.operatingRevenueGrowth)}`],['Utjämningskänslighet',percent(a.equalisationOffset*100)],['Låneränta / investeringar',`${percent(a.interestRate)} / ${number(a.investment)} mnkr per år`],['Skattetrend / bidragstillväxt utan import',revenuePath?'Ersatta av importerade årsbelopp':`${vector(run.inputs.map(r=>r.taxGrowth),'%')} / ${percent(a.grantGrowth)}`]
  ])+table(['År',a.splitPayroll?'Lön %':'Arbetskraft %','Övriga priser %','Pensionskostnad','Skatt, scenario','Bidrag, scenario','Nettodrift','Avskrivning','Resultat'],future.map((r,i)=>[r.year,number(run.inputs[i].wageGrowth),number(run.inputs[i].priceGrowth),number(r.pensionExpense),number(r.tax),number(r.grants),number(r.cost),number(r.depreciation),number(r.result)]),'Effektiva årsvisa antaganden och scenariobelopp. Pengar i mnkr, löpande priser.')+`<p>Resultat = skatt + bidrag − nettodrift − avskrivning + finansiella intäkter − ränta − övrig finansiell kostnad. Finansiella intäkter: ${escape(number(b.financialIncome))} mnkr; övrig finansiell kostnad: ${escape(number(b.otherFinancialExpense))} mnkr. Basår ${first}: observerat resultat ${escape(number(rows[0].result))} mnkr. Låneränta och investeringar redovisas vid skuldgrafen.</p>`);
  page('Banklåneskuld',graph('debt-chart','Grön linje: scenariot. Brun streckad linje: grundbana med samma aktiva underlag.')+parameters([
    ['Ingående skuld / kassa',`${number(b.debt)} / ${number(b.cash)} mnkr`],[flow?'Låneränta på aktuell skuld':'Låneränta på ingående skuld',percent(a.interestRate)],['Investeringar per år',`${number(a.investment)} mnkr`],['Ingående avskrivningsbara tillgångar',`${number(b.assets)} mnkr`],['Härledd tillgångslivslängd',`${number(b.assets/b.depreciation)} år`],['Finansiering','Underskott lånas; överskott amorterar skuld, därefter ökar kassan.']
  ])+table(['År','Investering','Operativt kassaflöde','Pensionskostnad','Pensionsbetalning','Ränta','Nyupplåning','Amortering','Skuld','Kassa'],future.map(r=>[r.year,...['investment','operatingCash','pensionExpense','pensionCashPayments','interest','borrowing','repayment','debt','cash'].map(k=>number(r[k]))]),'Mnkr. I driftkassan återläggs avskrivning och skillnaden mellan pensionskostnad och pensionsbetalning. Modellerat rörelsekapital påverkar kassaflödet när det är aktivt.')+'<p>Resultatets intäkts-, kostnads- och befolkningsantaganden påverkar också finansieringsbehovet och finns vid övriga grafer. Kassaflödet saknar bland annat fullständig rörelsekapitalmodell.</p>');
  if(a.workingCapitalEnabled) {
    page('Rörelsekapital',table(['År','Kundfordringar','Leverantörsskulder','Förutbetalda bidrag','Kassaflödeseffekt','Driftkassa'],
      rows.map(r=>[r.year,...['tradeReceivables','tradePayables','deferredGrants','workingCapitalCash','operatingCash'].map(key=>number(r[key]))]),
      'Mnkr. Kassaflödet påverkas av förändrade saldon för kundfordringar, leverantörsskulder och förutbetalda bidrag.'));
  }
  if(a.liquidityPolicy) {
    page('Kassa och förfinansiering',parameters([
      ['Kassareserv',`${number(a.cashReserve??0)} mnkr`],
      ['Uppskjuten del av första årets investering',percent(100*(a.deferInvestmentShare??0))],
      ['Förfinansierad del av uppskjuten betalning',percent(100*(a.prefinanceShare??0))]
    ])+table(['År','Investering betald','Kvar att betala','Nya lån','Varav förfinansiering','Amortering','Kassa','Skuld'],
      rows.map(r=>[r.year,...['investment','outstandingDeferredInvestment','borrowing','prefinancing','repayment','cash','debt'].map(key=>number(r[key]))]),
      flow?'Mnkr. Ränta beräknas på den skuld som finns under året.':'Mnkr. Ränta beräknas på ingående skuld.'));
  }
  if(['planned','delay'].includes(a.projectChoice)&&b.project) {
    page(b.project.name,table(['År','Projektutbetalning','Pågående projekt','Driftsatt värde','Platser i bruk','Nya lån i kommunen'],
      future.map(r=>[r.year,...['projectPaid','projectWorkInProgress','projectCommissioned','projectPlacesInUse','borrowing'].map(key=>number(r[key]))]),
      'Belopp i mnkr. Platserna avser denna förskola. Lånen avser hela kommunen.')+
      `<p><a href="${escape(b.project.accountsSource)}">Årsredovisning 2025, s. 64–65</a> · <a href="${escape(b.project.capacitySource)}">Förskolans kapacitet</a></p>`);
  }
  if(a.constructionYears>0) {
    page('Investeringar och byggtid',parameters([
      ['Byggtid',`${a.constructionYears} år`],['Andel investeringar med byggtid',percent(100*(a.constructionShare??0.5))]
    ])+table(['År','Utbetald investering','Taget i bruk','Pågående arbeten','Tillgångar i bruk','Avskrivningar'],
      rows.map(r=>[r.year,...['investment','commissioned','workInProgress','assets','depreciation'].map(key=>number(r[key]))]),
      'Mnkr. Ingående pågående arbeten fördelas jämnt över byggtiden.'));
  }
  page('Befolkning och åldersgrupper',graph('population-chart',b.ageGroups.join(' · '))+parameters([
    ['Befolkningsunderlag',populationLabel],['Förändrat årligt flyttnetto',`${number(a.migrationDelta)} personer`],['Förändrat födelsetal',percent(a.birthChange)],['Basårets födda / döda',`${number(b.births)} / ${number(b.deaths)} personer`],['Årliga dödsrisker',run.cohort?'Per ålder och kön i kohortmodellen':vector(run.calibration.deathRates.map(v=>v*100),'%')],['Fördelning av förändrat flyttnetto',a.demographyMode?.includes('observed')?'SCB:s tidigare inflyttare':vector(a.migrationWeights.map(v=>v*100),'%')]
  ])+table(['År',...b.ageGroups,'Totalt','Födda','Döda','Flyttnetto / restflöde'],rows.map(r=>[r.year,...r.cohorts.map(number),number(r.population),number(r.births),number(r.deaths),number(r.migration)]),'Personer. Basåret är observerat; framtida värden är modellberäknade.')+'<p>Grundmodellens restflöde kan också innehålla statistiska justeringar. Varianten med historiskt flyttnetto använder SCB:s in- och utflyttningar. Befolkningsförändring = födda − döda + restflöde.</p>');
  page('Efterfrågan på verksamhet',graph('demand-chart','Grön linje: utbildning. Brun linje: äldreomsorg. Index, basåret = 100.')+parameters([
    ['Utbildningsvikter för 0–6 / 7–15 / 16–18',vector(a.educationWeights.map(v=>v*100),'%')],['Äldreomsorgens behovsproxy',run.cohort?'65–79, 80–89 och 90+ viktade efter omsorgskostnad':'Hela gruppen 65+, relativt basåret'],['Årlig kapacitetsanpassning',percent(a.adjustment*100)],['Fast kostnadsandel',percent(a.fixedShare*100)],['Kostnadsvikter utbildning / omsorg / övrigt',vector(a.sectorCosts,'mnkr')],['Befolkningsscenario',`Flyttnetto ${number(a.migrationDelta)} personer/år; födelsetal ${percent(a.birthChange)}`]
  ])+table(['År','Utbildning, index','Äldreomsorg, index','Invånare','Personal exkl. pension','Övriga driftkostnader','Verksamhetsintäkter'],rows.map(r=>[r.year,number(r.educationIndex*100),number(r.careIndex*100),number(r.population),number(r.payroll),number(r.otherOperatingExpense),number(r.operatingRevenue)]),'Behovsindex är inte elevantal eller omsorgstagare. Finansiella belopp i mnkr.')+'<p>Behovsindex styr gradvis anpassad kapacitet. Kostnadsvikter och anpassningshastighet är illustrativa. Separata omsorgsintensiteter för äldregrupper är ännu inte skattade. Arbetskrafts- och prisbanor finns vid resultatgrafen.</p>');
  page('Känslighet i slutåret',graph('sensitivity',`Resultatförändring ${last}, mnkr, jämfört med det exporterade scenariot.`)+parameters([
    ['Utgångspunkt',`Aktuellt scenario, resultat ${number(rows.at(-1).result)} mnkr år ${last}`],['Arbetskraftskostnad','+1 procentenhet varje prognosår'],['Låneränta','+1 procentenhet varje prognosår'],['Flyttnetto','+100 personer varje prognosår'],['Investeringar','+100 mnkr varje prognosår'],['Metod','En parameter ändras åt gången; övriga värden och aktiva underlag hålls fasta.']
  ])+'<p>Staplarna återger känslighetsberäkningen i scenariolabbet. Positivt värde betyder högre resultat. Detta är scenarier och inga skattade sannolikheter eller konfidensintervall.</p>');
  page('Förhållandet till SKR och källor',`<p>Jämförelsen avser <a href="https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoser/modellverktygetskatterochbidrag.10928.html">SKR:s modellverktyg Skatter och bidrag</a>. Det beräknar skatte- och bidragsintäkter samt utjämning. KOEKMO använder en importerad referens när den är aktiverad och beräknar även drift, investeringar, resultat, kassaflöde och skuld.</p><p><strong>Scenariobeloppen i KOEKMO kan avvika från SKR-referensen.</strong> ${a.revenueMode===1&&revenuePath?'Vald intäktsmodell använder SKR:s referensbelopp.':a.revenueMode===2&&revenuePath?'Skatt före avräkning, inkomstutjämning och regleringspost justeras med folkmängden per 1 november. Skattesatsen påverkar skatten före avräkning.':'Förenklade justeringar av befolkning, skattesats och utjämning kan ge andra intäktsbelopp än referensbanan.'} Bättre prognosprecision än SKR är inte visad.</p>`+parameters(common)+table(['År','Referens: skatt','Referens: bidrag','Referens: summa','Scenario: summa','Skillnad'],future.map(r=>{
    const ref=revenuePath?.rows.find(p=>p.year===r.year);
    return [ref?.projected?`${r.year} (förlängt)`:r.year,number(ref?.tax),number(ref?.grants),number(ref?ref.tax+ref.grants:null),number(r.tax+r.grants),number(ref?r.tax+r.grants-ref.tax-ref.grants:null)];
  }),'Mnkr. Streck betyder att ingen importerad kommunal intäktsreferens är aktiv.')+`<p>${escape(extension)}</p><p>SKR-import: ${escape(revenuePath?.populationReference??'Ingen kommunal intäktsimport aktiv.')} ${revenuePath?'Skatt inkluderar slutavräkningar; bidrag inkluderar utjämning, LSS och fastighetsavgift enligt den importerade mappningen.':''}</p><p><a href="${escape(b.source)}">Bokslutskälla ${first}</a>. ${populationSource} ${planningSource}</p><p>Basår och framtidsuppgifter har olika källdatum. Underlagen innebär inte oberoende prognosvalidering. Detaljerad maskinläsbar spårbarhet finns i scenariots JSON-export.</p>`);
  const html=pages.map((p,i)=>`<section class="report-page"><header><span>KOEKMO · ${escape(name)} · Scenario ${first+1}–${last}</span><span>${escape(date)} · Stockholm</span></header><h1>${escape(p.title)}</h1>${p.content}<footer>Oberoende forskningsprototyp · Ingen officiell kommunprognos <span>${i+1} / ${pages.length}</span></footer></section>`).join('');
  return `<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(name)}-scenario-${first+1}-${last}</title><style>
@page{size:A4 landscape;margin:10mm 12mm}*{box-sizing:border-box}body{margin:0;color:#193835;background:#edf0eb;font:10pt Arial,sans-serif}a{color:#17634e;overflow-wrap:anywhere}h1{font-size:21pt;margin:5mm 0 3mm}p{font-size:9pt;line-height:1.4;margin:3mm 0}header,footer{font-size:8pt;color:#647671;display:flex;justify-content:space-between;border-bottom:1px solid #ccd6ce;padding-bottom:2mm}footer{border:0;border-top:1px solid #ccd6ce;padding:2mm 0 0;margin-top:auto}.report-page{background:white;width:273mm;min-height:190mm;margin:8mm auto;padding:0 0 3mm;display:flex;flex-direction:column;break-after:page}.report-page:last-child{break-after:auto}figure{margin:0 0 2mm}figure>svg{width:100%;height:40mm;display:block}figcaption{font-size:8pt;line-height:1.3;color:#647671;margin-top:1mm}.parameters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2mm 5mm;margin:2mm 0 3mm}.parameters>div{border-top:1px solid #dde4dc;padding-top:1mm}dt{font-size:8pt;color:#647671}dd{margin:1mm 0;font-size:9pt;line-height:1.3;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:8pt;table-layout:fixed;margin:1mm 0}caption{text-align:left;font-size:8pt;line-height:1.35;margin-bottom:2mm;color:#647671}th,td{border-bottom:1px solid #dde4dc;padding:1mm 1mm;text-align:right;overflow-wrap:anywhere}th:first-child{text-align:left;width:13mm}thead th{background:#edf3e7;font-weight:600}thead{display:table-header-group}tr{break-inside:avoid}.sensitivity-row{margin:5mm 0}.sensitivity-label{display:flex;justify-content:space-between;font-size:11pt;margin-bottom:2mm}.sensitivity-track{height:3mm;background:#edf0eb}.sensitivity-fill{height:3mm;background:#ad8053}.sensitivity-fill.positive{background:#17634e}.report-actions{max-width:273mm;margin:8mm auto;font:12pt Arial}.report-actions button{padding:3mm 5mm;cursor:pointer}.report-actions p{font-size:11pt}@media print{body{background:white}.report-page{width:auto;margin:0;min-height:0;display:block;padding:0}footer{margin-top:2mm;break-inside:avoid}.report-actions{display:none}*{print-color-adjust:exact;-webkit-print-color-adjust:exact}}@media screen and (max-width:900px){.report-page{width:100%;padding:5mm}.report-actions{padding:0 5mm}}
</style></head><body><div class="report-actions"><button id="report-print" type="button">Spara som PDF / skriv ut</button><p>Välj ”Spara som PDF” i utskriftsdialogen. Rapporten är en ögonblicksbild av scenariot vid exporttillfället.</p></div>${html}</body></html>`;
}
// `tab` may be opened by the caller inside the click handler, before an await.
export function openScenarioReport(snapshot,tab=null) {
  const html=buildScenarioReport(snapshot);
  const report=tab??window.open('','_blank');
  if(!report)throw Error('Tillåt att rapporten öppnas i en ny flik för att exportera PDF.');
  report.opener=null;
  report.document.open();report.document.write(html);report.document.close();
  const print=()=>{report.focus();report.print();};
  const ready=()=>{
    report.document.getElementById('report-print').onclick=print;
    (report.document.fonts?.ready??Promise.resolve()).then(()=>report.requestAnimationFrame(()=>report.requestAnimationFrame(print)));
  };
  if(report.document.readyState==='complete')ready();else report.addEventListener('load',ready,{once:true});
  return report;
}
