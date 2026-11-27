// The "Modellen" tab: a flow diagram of Kommunekonomi.Continuous.Economy (which Kommunekonomi.Municipalities.Motala.Continuous extends), documentation per component and
// a result-to-debt waterfall, all for one chosen year of the current scenario.
// Assumptions are edited through the scenario lab's own controls, so both views share
// one scenario and one validation path.

const nf=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:0});
const df=new Intl.NumberFormat('sv-SE',{minimumFractionDigits:1,maximumFractionDigits:1});
const fmt=v=>Number.isFinite(v)?nf.format(Math.round(v)||0).replace('-','−'):'—';
const idx=v=>Number.isFinite(v)?df.format(v*100):'—';
const signed=v=>(v>0?'+':'')+fmt(v);
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// The layout is drawn by hand for the page; the parts are those of Kommunekonomi.Continuous.Economy.
// Colours are the components' Modelica icon colours.
export const COMPONENTS=[
  {id:'demography',model:'Demography',name:'Demografi',sub:'Fem åldersgrupper',x:40,y:40,color:'#285f8c',
    keys:['migrationDelta','birthChange'],
    values:r=>[['Invånare',fmt(r.population)],['Födda / döda',`${fmt(r.births)} / ${fmt(r.deaths)}`],['Flyttnetto',signed(r.migration)]],
    text:`Befolkningen är sju lager: 0–6, 7–15, 16–18 och 19–64 år, och inom 65+ en åldringskedja 65–79, 80–89 och 90+. Födda, döda, åldrande och flyttningar är flöden som pågår hela året. Hur många som fyller år över en gräns ett visst år kommer ur basårets ettårsåldrar: de som fyller 65 år första prognosåret är basårets 64-åringar. Restflödet är det jämna flöde per år som tar varje åldersgrupp från ett årsskifte till nästa: kalibrerat mot kommunens historik, eller mot den inlästa befolkningsprognosen så att årsskiftenas folkmängd blir prognosens. Med ettårsåldrar är varje födelseår ett lager, och åldern byter etikett vid årsskiftet.`,
    eq:['födda per år = födda i basåret · (19–64 år just nu / 19–64 år i basåret) · (1 + förändring i födelsetal)',
      'döda per år = dödstal · invånare i lagret; i 65+ stiger dödstalet med åldern och sjunker med rikets trend',
      'åldras upp per år = årets andel · invånare i lagret; andelen ur basårets ettårsåldrar',
      'd(grupp)/dt = in från yngre grupp − åldras upp − döda + restflöde + flyttnetto · vikt',
      'kontroll vid årsslutet: Δbefolkning = årets födda − döda + flyttnetto'],
    limits:'Breda åldersgrupper under 65 år. Födslar följer gruppen 19–64 som en grov exponering. Dödstalet för 65+ är basårets döda delat med årets medelfolkmängd, ett enda års utfall. Flyttningarna är jämnt fördelade över året; säsongen (sommarflyttar, terminsstart) finns inte med.'},
  {id:'services',model:'Services',name:'Verksamhet',sub:'Efterfrågan och kapacitet',x:380,y:40,color:'#237355',
    keys:['adjustment'],
    values:r=>[['Utbildning',idx(r.educationIndex)],['Äldreomsorg',idx(r.careIndex)],['Index','basår = 100']],
    text:`Åldersgrupperna blir efterfrågan på tre verksamheter: utbildning, äldreomsorg och övrigt. Efterfrågan följer befolkningen dag för dag, och kapaciteten närmar sig efterfrågan kontinuerligt; en fast andel ändras inte alls. Kostnaderna räknas med kapaciteten under året, inte vid årets slut. När efterfrågan har en jämn trend ligger kapaciteten cirka 1,4 år efter med anpassningen 0,5.`,
    eq:['utbildning = åldersviktat behov för 0–6, 7–15 och 16–18 år',
      'äldreomsorg = åldersviktat behov för 65–79, 80–89 och 90+ år',
      'övrigt = vägarnas andel · vägnätet + resten · befolkning / bas; vägnätet är ett lager som ligger kvar',
      'd(kapacitet)/dt = takt · (fast andel + rörlig andel · efterfrågan − kapacitet)',
      'takt = −ln(1 − anpassning): ett konstant glapp stängs med andelen anpassning på ett år',
      'tjänstevolym = sektorkapacitet vägd med sektorkostnader i basåret'],
    limits:'Kostnadsvikterna fördelar basårets kostnader mellan verksamheterna. Indexet beskriver det beräknade behovet. Läsårets rytm (ändrad kapacitet i augusti) finns inte med.'},
  {id:'operations',model:'OperatingAccounts',name:'Drift',sub:'Löner, pensioner, övrigt',x:720,y:40,color:'#237355',
    keys:['wageGrowth','priceGrowth','pensionGrowth','costDrift','productivity','operatingRevenueGrowth'],
    values:r=>[['Personal exkl. pension',fmt(r.payroll)],['Övriga kostnader',fmt(r.otherOperatingExpense)],['Nettokostnad',fmt(r.cost)]],
    text:`Kostnaderna är flöden i mnkr per år som pågår hela året; årets belopp är summan. Löne- och prisnivån växer varje dag. Banornas årliga ökning (SKR:s arbetskraftskostnad och priser, eller reglagens procent) gäller årsmedlet, och takten inom året är vald så att årsmedlet ökar just så mycket. Pensionskostnaden följer lönesumman. Verksamhetens intäkter följer befolkningen just nu och en del av en extra inflation.`,
    eq:['d(nivå)/dt = takt · nivå, för löner, priser, taxor, produktivitet och standard',
      'takten går linjärt mellan årsskiftena; årsmedlets ökning = banans ökning',
      'löner per år = basårets löner · lönenivå · tjänstevolym · standard / produktivitet',
      'övriga kostnader per år = basårets övriga kostnader · prisnivå · tjänstevolym · standard',
      'pensionskostnad per år = basårets andel av lönesumman · lönesumman just nu (eller en given bana)',
      'verksamhetsintäkter per år = basårets intäkter · taxenivå · befolkning / basårets befolkning',
      'årets nettokostnad = summan under året av löner + sociala avgifter + pension + övriga kostnader − verksamhetsintäkter + avrundning'],
    limits:'Lönerna stiger jämnt; avtalens datum (ofta 1 april) finns inte med. När den årliga ökningen ändras mycket mellan åren svänger takten inom året mer än årsökningarna. Standard är kostnadsökningen utöver demografi och pris; 0 om inget annat väljs.'},
  {id:'revenues',model:'Revenue',name:'Intäkter',sub:'Skatt och bidrag',x:40,y:330,color:'#285f8c',
    keys:['taxGrowth','grantIncrease','grantGrowth','taxRate','equalisationOffset'],
    values:r=>[['Skatt',fmt(r.tax)],['Bidrag',fmt(r.grants)],['Summa',fmt(r.tax+r.grants)]],
    text:`Skatt och generella bidrag beslutas för ett år i taget och betalas ut med en tolftedel i månaden: årets belopp bestäms 1 januari och flyter sedan jämnt in i kassan. Beloppet räknas från referensbanan (SKR:s beräkning för kommunen när planeringsunderlagen är aktiva) och befolkningen. Varianten per delpost justerar skatt före avräkning, inkomstutjämning och regleringspost med folkmängden den 1 november året innan; den läses ur befolkningslagret den dagen. En annan skattesats ändrar bara skatten.`,
    eq:['beslut 1 januari: årets skatt och bidrag ur referensbanan och befolkningen',
      'befolkningsfaktor = (kommunen fg år / kommunen året före basåret) / (riket fg år / riket året före basåret)',
      'med SKR:s bana: befolkningsfaktor = kommunen fg år / SKR:s befolkning',
      'per delpost: folkmängden 1 november året innan / SKR:s folkmängd',
      'statens höjning = bidragshöjning (mdkr i riket) · (år − 1) · kommunen fg år / riket fg år',
      'flöde in i kassan = årets skatt och bidrag / 1 år; kontroll: summan under året = beslutet'],
    limits:'Utjämningen är en förenklad känslighet, inte lagens beräkning av inkomst-, kostnads- och LSS-utjämning. Slutavräkningen av skatten har inget eget flöde inom året.'},
  {id:'capital',model:'Capital',name:'Kapital',sub:'Tillgångar och avskrivning',x:380,y:330,color:'#9b5f23',
    keys:['investment'],
    values:r=>[['Investering',fmt(r.investment)],['Avskrivning',fmt(r.depreciation)],['Tillgångar',fmt(r.assets)]],
    text:`Tre lager: pågående arbeten, projektets pågående arbeten och tillgångar i bruk. Investeringarna betalas jämnt under året. Utan byggtid går de direkt till tillgångar i bruk; med byggtid ligger byggandelen bland pågående arbeten och tas i bruk efter byggtiden. Avskrivningen är ett flöde på de tillgångar som är i bruk just då, så en investering börjar skrivas av när den betalas.`,
    eq:['livslängd = basårets tillgångar i bruk / basårets avskrivningar',
      'd(pågående arbeten)/dt = utbetald byggandel − taget i bruk',
      'avskrivning per år = −ln(1 − 1/livslängd) · tillgångar i bruk just nu',
      'd(tillgångar i bruk)/dt = direkt investering + taget i bruk − avskrivning',
      'kontroll vid årsslutet: Δlager = årets investering − årets avskrivning'],
    limits:'Byggtiden är ett gemensamt antagande för de fördröjda investeringarna. Avskrivningstakten skriver av en andel av beståndet per år som ger den sammanvägda avskrivningstiden. Projektet tas i bruk mitt i sitt öppningsår.'},
  {id:'finance',model:'Finance',name:'Finans',sub:'Resultat, kassa och lån',x:720,y:330,color:'#694b91',
    keys:['interestRate'],
    values:r=>[['Resultat',fmt(r.result)],['Räntor',fmt(r.interest)],['Låneskuld',fmt(r.debt)]],
    text:`Kassa och låneskuld är lager. Skatt, bidrag, löner, inköp, räntor och investeringar är flöden in i och ut ur kassan. När flödena ger underskott lånar kommunen i samma takt, och ett överskott amorterar. Räntan räknas på den skuld som finns just då, så ett lån som tas upp i mars kostar ränta från mars. Kassan styrs mot en likviditetsreserv i dagar av utbetalningarna, minus krediten: den börjar på bokslutets nivå och närmar sig reserven på några år. Kassa utöver basårets ger ränta, låneräntan minus en halv procentenhet. Med rörelsekapital går kundernas betalningar och leverantörernas fakturor genom egna lager med betalningstid i dagar.`,
    eq:['ränta per år = räntesats · låneskuld just nu (med räntebindning: lånens bundna räntor)',
      'finansiella intäkter per år = basårets + (låneränta − 0,5 %) · (kassa − basårets kassa)',
      'netto = driftens kassaflöde + investeringar, mnkr per år',
      'nya lån per år = −netto när netto är negativt; amortering per år = netto när det är positivt',
      'd(skuld)/dt = nya lån − amortering;  d(kassa)/dt = netto + nya lån − amortering',
      'årets resultat = skatt + bidrag − nettokostnad − avskrivning + finansiella intäkter − ränta − övriga finansiella kostnader',
      'kontroll vid årsslutet: förändringen av alla lager = årets resultat'],
    limits:'Standardräntan är basårets räntekostnad delad med årets medelskuld. Kassans ränta är ett antagande. Övriga finansiella poster flyter jämnt. Lönerna betalas jämnt, inte den 27:e. Borgen och ny leasing har inga egna flöden.'}
];
const W=260,H=150,byId=Object.fromEntries(COMPONENTS.map(c=>[c.id,c]));

// Arrows are the connections in Kommunekonomi.Continuous.Economy. `value` gives mnkr for money flows (drawn
// to scale) and a label for the others.
export const FLOWS=[
  {from:'demography',to:'services',binding:'connect(demography.cohorts, services.cohorts)',label:'Åldersgrupper',d:'M300,105 L380,105'},
  {from:'demography',to:'operations',binding:'connect(demography.cohorts, operations.cohorts)',label:'Befolkning',d:'M170,40 C170,0 850,0 850,40'},
  {from:'demography',to:'revenues',binding:'connect(demography.cohorts, revenues.cohorts)',label:'Befolkning fg år',d:'M110,190 L110,330'},
  {from:'services',to:'operations',binding:'connect(services.serviceVolume, operations.serviceVolume)',label:'Tjänstevolym',d:'M640,105 L720,105'},
  {from:'operations',to:'finance',binding:'connect(payments.cash, finance.operating)',label:'Nettokostnad',money:r=>r.cost,d:'M850,190 L850,330'},
  {from:'operations',to:'finance',binding:'payments.pensionExpense = operations.pensionExpenseRate',label:'Pension',money:r=>r.pensionExpense,d:'M930,190 L930,330'},
  {from:'revenues',to:'finance',binding:'connect(revenues.taxAndGrants, finance.taxAndGrants)',label:'Skatt + bidrag',money:r=>r.tax+r.grants,d:'M170,480 C170,530 790,530 790,480'},
  {from:'capital',to:'finance',binding:'depreciation = capital.depreciation.annual',label:'Avskrivning',money:r=>r.depreciation,d:'M640,405 L720,405'},
  {from:'input',to:'capital',binding:'connect(scenario.investment, capital.investment)',label:'Investering',money:r=>r.investment,d:'M510,280 L510,330'},
  {from:'input',to:'finance',binding:'connect(capital.cash, finance.investing)',label:'',money:r=>r.investment,d:'M580,266 C690,266 760,286 760,330'}
];

// Drop every annotation(...) clause (port placements, icons, documentation); strings may hold parentheses.
function stripAnnotations(text) {
  let out='',i=0;
  for(;;) {
    const at=text.indexOf('annotation(',i);
    if(at<0) return out+text.slice(i);
    out+=text.slice(i,at).replace(/[ \t]+$/,'');
    let depth=0,j=at+'annotation'.length,inString=false;
    for(;j<text.length;j++) {
      const c=text[j];
      if(inString){if(c==='\\')j++;else if(c==='"')inString=false;continue;}
      if(c==='"')inString=true;else if(c==='(')depth++;else if(c===')'&&--depth===0){j++;break;}
    }
    i=j;
  }
}

function modelicaSection(source,model) {
  const start=source.search(new RegExp(`\\n\\s*model ${model}\\b`));
  if(start<0) return null;
  const end=source.indexOf(`end ${model};`,start);
  const lines=stripAnnotations(source.slice(start,end<0?undefined:end).replace(/^\s*\n/,'')).replace(/\n\s*;(?=\s*(\n|$))/g,'').replace(/\s+$/,'').split('\n');
  const indent=Math.min(...lines.filter(l=>l.trim()).map(l=>l.match(/^ */)[0].length));
  return lines.map(l=>l.slice(indent)).join('\n')+`\n  …\nend ${model};`;
}
export {modelicaSection};

export function createModelView(root,{source}) {
  let run=null,year=null,selected='finance',paramSignature='';
  const code={};
  // The parts are in the package Kommunekonomi.Continuous; Revenue is Kommunekonomi.Components.Revenue.
  source.then(text=>{
    const continuous=text.slice(text.indexOf('package Continuous '));
    for(const c of COMPONENTS) code[c.id]=c.id==='revenues'?modelicaSection(text,c.model):modelicaSection(continuous,c.model);
    if(run) renderPanel();
  }).catch(()=>{});

  root.innerHTML=`<div class="model-toolbar"><label for="model-year">År</label><input id="model-year" type="range" min="1" max="1" step="1"><output id="model-year-label"></output></div>
<div class="model-diagram" id="model-diagram"></div>
<p class="chart-note">Klicka på en del för att läsa hur den räknar och ändra dess antaganden. Pilarna är modellens kopplingar; pengaflödenas tjocklek motsvarar beloppet för valt år. Diagrammet visar delarna i <code>Kommunekonomi.Continuous.Economy</code>. Beloppen är årets.</p>
<div class="model-detail" id="model-detail" aria-live="polite"></div>
<section class="panel"><p class="eyebrow">FRÅN INTÄKTER TILL LÅN</p><h2 id="waterfall-title">Resultat och finansiering</h2><div id="model-waterfall"></div><p class="chart-note">Samma beräkning som i Finans. Positiva poster ökar, negativa minskar. Kassaflödet räknas från resultatet; investeringar som inte täcks lånas.</p></section>`;
  const $=id=>root.querySelector('#'+id);
  const yearInput=$('model-year');
  yearInput.addEventListener('input',()=>{year=run.rows[Number(yearInput.value)].year;$('model-year-label').textContent=String(year);renderDiagram();renderWaterfall();});

  root.addEventListener('click',e=>{const node=e.target.closest('[data-component]');if(node){select(node.dataset.component);}});
  root.addEventListener('keydown',e=>{const node=e.target.closest('[data-component]');if(node&&(e.key==='Enter'||e.key===' ')){e.preventDefault();select(node.dataset.component);}});
  function select(id){selected=id;paramSignature='';renderDiagram();renderPanel();}

  // Assumption fields mirror the scenario lab's controls and write through them.
  root.addEventListener('input',e=>{
    const key=e.target.dataset.mkey;if(!key)return;
    const el=e.target;if(el.value===''||el.validity.badInput)return;
    const main=document.getElementById(key);if(!main)return;
    main.value=el.value;main.dispatchEvent(new Event('input',{bubbles:true}));
    syncParams(el);
  });
  root.addEventListener('change',e=>{if(e.target.dataset.mkey) syncParams();});

  function control(key){
    const main=document.getElementById(key),range=document.getElementById(key+'-range');
    if(!main||!range) return null;
    return {key,label:document.querySelector(`label[for="${key}"]`)?.textContent??key,unit:main.nextElementSibling?.textContent??'',
      help:range.parentElement.querySelector('.slider-help')?.textContent??'',min:range.min,max:range.max,step:range.step,value:main.value};
  }
  function syncParams(editing=null){
    for(const el of root.querySelectorAll('[data-mkey]')){
      if(el===editing||el===document.activeElement&&el.type==='number') continue;
      const main=document.getElementById(el.dataset.mkey);if(main) el.value=main.value;
    }
  }

  function row(){return run.rows.find(r=>r.year===year)??run.rows.at(-1);}

  function renderDiagram(){
    const r=row(),max=Math.max(...FLOWS.filter(f=>f.money).map(f=>Math.abs(f.money(r))));
    const markers=[];
    const flows=FLOWS.map((f,i)=>{
      const v=f.money?f.money(r):null,width=v==null?1.6:2+14*Math.sqrt(Math.abs(v)/max);
      const color=f.money?(f.from==='revenues'?'#285f8c':f.from==='input'?'#9b5f23':'#a34840'):'#7d8b86';
      // Money arrows get a head sized to their own width.
      if(f.money) markers.push(`<marker id="flow-${i}" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="${(width+10).toFixed(1)}" markerHeight="${(width+10).toFixed(1)}" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="${color}" fill-opacity=".6"/></marker>`);
      const head=f.money?`url(#flow-${i})`:'url(#arrow)';
      return `<path d="${f.d}" fill="none" stroke="${color}" stroke-opacity="${f.money?.45:.9}" stroke-width="${width.toFixed(1)}" marker-end="${head}"><title>${safe(f.label||'Investering')}${v==null?'':`: ${fmt(v)} mnkr`}\n${safe(f.binding)}</title></path>`;
    }).join('');
    const labels=[
      ['Åldersgrupper',340,92],['Befolkning',510,14],['Befolkning fg år',118,262,'start'],['Tjänstevolym',680,92],
      [`Nettokostnad ${fmt(r.cost)}`,840,262,'end'],[`Pension ${fmt(r.pensionExpense)}`,938,262,'start'],
      [`Skatt + bidrag ${fmt(r.tax+r.grants)}`,480,548],['Avskrivning',680,392],[fmt(r.depreciation),680,428]
    ].map(([t,x,y,a='middle'])=>`<text x="${x}" y="${y}" text-anchor="${a}" class="flow-label">${safe(t)}</text>`).join('');
    const nodes=COMPONENTS.map(c=>`<g data-component="${c.id}" class="model-node${c.id===selected?' selected':''}" tabindex="0" role="button" aria-pressed="${c.id===selected}" aria-label="${safe(c.name)}: ${safe(c.sub)}">
<rect x="${c.x}" y="${c.y}" width="${W}" height="${H}" rx="10" fill="#fff" stroke="${c.color}" stroke-width="${c.id===selected?3:1.5}"/>
<rect x="${c.x}" y="${c.y}" width="6" height="${H}" rx="3" fill="${c.color}"/>
<text x="${c.x+22}" y="${c.y+30}" class="node-title" fill="${c.color}">${safe(c.name)}</text>
<text x="${c.x+22}" y="${c.y+49}" class="node-sub">${safe(c.sub)}</text>
${c.values(r).map(([k,v],i)=>`<text x="${c.x+22}" y="${c.y+79+i*22}" class="node-key">${safe(k)}</text><text x="${c.x+W-16}" y="${c.y+79+i*22}" text-anchor="end" class="node-value">${safe(v)}</text>`).join('')}
</g>`).join('');
    const input=`<g class="model-input"><rect x="440" y="252" width="140" height="28" rx="14" fill="#fff6e6" stroke="#9b5f23"/><text x="510" y="271" text-anchor="middle" class="flow-label">Investering ${fmt(r.investment)}</text></g>`;
    $('model-diagram').innerHTML=`<svg viewBox="0 -4 1020 560" role="img" aria-label="Flödesdiagram över modellen ${year}">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7d8b86"/></marker>${markers.join('')}</defs>
${flows}${labels}${input}${nodes}</svg>`;
  }

  function renderPanel(){
    const c=byId[selected],controls=c.keys.map(control).filter(Boolean);
    const shown=code[c.id],library=c.id!=='revenues'?'KOMMUNEKONOMI.CONTINUOUS':'KOMMUNEKONOMI.COMPONENTS';
    paramSignature=controls.map(x=>x.label+x.unit+x.min+x.max).join('|');
    $('model-detail').innerHTML=`<section class="panel model-panel" style="--node:${c.color}">
<div class="model-panel-text"><p class="eyebrow">${safe(c.model.toUpperCase())} · ${library}</p><h2>${safe(c.name)}</h2><p>${safe(c.text)}</p>
<h3>Ekvationer</h3><ul class="equations">${c.eq.map(e=>`<li><code>${safe(e)}</code></li>`).join('')}</ul>
<p class="chart-note">${safe(c.limits)}</p>
${shown?`<details><summary>Visa Modelica-koden</summary><pre class="modelica"><code>${safe(shown)}</code></pre></details>`:''}</div>
<div class="model-panel-params"><p class="eyebrow">ANTAGANDEN</p>${controls.length?controls.map(x=>`<div class="slider"><div class="slider-top"><label for="m-${x.key}">${safe(x.label)}</label><div class="number"><input id="m-${x.key}" data-mkey="${x.key}" type="number" min="${x.min}" max="${x.max}" step="any" value="${safe(x.value)}"><span>${safe(x.unit)}</span></div></div><input data-mkey="${x.key}" type="range" min="${x.min}" max="${x.max}" step="${x.step}" value="${safe(x.value)}" aria-label="${safe(x.label)}, reglage"><div class="slider-help"><span>${safe(x.help)}</span></div></div>`).join(''):'<p class="muted">Inga justerbara antaganden.</p>'}
<p class="small muted">Samma antaganden som i Scenariolabbet. Ändringar gäller från första prognosåret.</p></div></section>`;
  }

  function renderWaterfall(){
    const r=row(),financialIncome=r.result-(r.tax+r.grants-r.cost-r.depreciation-r.interest-r.otherFinancialExpense);
    const steps=[['Skatt',r.tax],['Generella bidrag',r.grants],['Nettokostnad',-r.cost],['Avskrivning',-r.depreciation],
      ['Finansiella intäkter',financialIncome],['Räntor',-r.interest],['Övriga finansiella kostnader',-r.otherFinancialExpense],
      ['Resultat',r.result,'total'],['Avskrivning tillbaka',r.depreciation],['Pension, ej utbetald',r.pensionExpense-r.pensionCashPayments],
      ['Kassaflöde från driften',r.operatingCash,'total'],['Investeringar',-r.investment],['Nya lån',r.borrowing],['Amortering',-r.repayment],
      ['Förändring av kassa',r.operatingCash-r.investment+r.borrowing-r.repayment,'total']];
    // A running total; each total bar is drawn from zero and the next steps continue from it.
    let level=0;const bars=steps.map(([label,v,kind])=>{
      const bar=kind?{label,from:0,to:v,v,kind}:{label,from:level,to:level+v,v};
      level=kind?v:level+v;return bar;});
    const lo=Math.min(0,...bars.flatMap(b=>[b.from,b.to])),hi=Math.max(0,...bars.flatMap(b=>[b.from,b.to]));
    const width=1000,left=230,right=80,rowH=26,height=bars.length*rowH+16;
    const x=v=>left+(v-lo)*(width-left-right)/(hi-lo||1);
    $('waterfall-title').textContent=`Resultat och finansiering ${r.year}`;
    $('model-waterfall').innerHTML=`<div class="model-diagram"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Vattenfall från skatt till kassa ${r.year}">
<line x1="${x(0)}" x2="${x(0)}" y1="0" y2="${height}" stroke="#aab7a2" stroke-dasharray="3 4"/>
${bars.map((b,i)=>{const y=8+i*rowH,a=Math.min(b.from,b.to),w=Math.max(1,Math.abs(x(b.to)-x(b.from)));
  const color=b.kind?'#193835':b.v>=0?'#17634e':'#a34840';
  return `<text x="${left-10}" y="${y+15}" text-anchor="end" class="wf-label${b.kind?' total':''}">${safe(b.label)}</text><rect x="${x(a)}" y="${y+3}" width="${w}" height="${rowH-8}" rx="2" fill="${color}" opacity="${b.kind?1:.8}"/><text x="${Math.max(x(b.from),x(b.to))+6}" y="${y+15}" class="wf-value">${b.kind?fmt(b.v):signed(b.v)}</text>`;}).join('')}
</svg></div>`;
  }

  return {
    update(next){
      run=next;
      const n=run.rows.length-1;yearInput.max=String(n);
      if(year==null||!run.rows.some(r=>r.year===year)) year=run.rows[n].year;
      const i=run.rows.findIndex(r=>r.year===year);yearInput.min='1';yearInput.value=String(i);
      $('model-year-label').textContent=String(year);
      renderDiagram();renderWaterfall();
      const signature=byId[selected].keys.map(control).filter(Boolean).map(x=>x.label+x.unit+x.min+x.max).join('|');
      if(signature!==paramSignature||!$('model-detail').firstChild) renderPanel(); else syncParams();
    },
    show(id){select(id);}
  };
}
