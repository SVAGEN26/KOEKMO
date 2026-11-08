// The "Modellen" tab: a flow diagram of Motala.Annual, documentation per component and
// a result-to-debt waterfall, all for one chosen year of the current scenario.
// Assumptions are edited through the scenario lab's own controls, so both views share
// one scenario and one validation path.

const nf=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:0});
const df=new Intl.NumberFormat('sv-SE',{minimumFractionDigits:1,maximumFractionDigits:1});
const fmt=v=>Number.isFinite(v)?nf.format(Math.round(v)||0).replace('-','−'):'—';
const idx=v=>Number.isFinite(v)?df.format(v*100):'—';
const signed=v=>(v>0?'+':'')+fmt(v);
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// Positions follow the Placement annotations in Motala.Annual (same grid, y flipped).
// Colours are the components' Modelica icon colours.
export const COMPONENTS=[
  {id:'demography',model:'Demography',name:'Demografi',sub:'Fem åldersgrupper',x:40,y:40,color:'#285f8c',
    keys:['migrationDelta','birthChange'],
    values:r=>[['Invånare',fmt(r.population)],['Födda / döda',`${fmt(r.births)} / ${fmt(r.deaths)}`],['Flyttnetto',signed(r.migration)]],
    text:`Befolkningen delas i fem grupper: 0–6, 7–15, 16–18, 19–64 och 65+ år. Varje år överlever en andel, en jämnt fördelad del åldras upp till nästa grupp, födda tillkommer i 0–6 och ett restflöde lägger till flyttningar och statistiska justeringar. Restflödet är kalibrerat så att grundscenariot följer kommunens befolkningsprognos; det är inte observerad flyttning per ålder.`,
    eq:['födda = 334 · (19–64 år / 19–64 år 2025) · (1 + förändring i födelsetal)',
      'överlevande = föregående år · (1 − dödsrisk)',
      'uppåldrade = överlevande / gruppens bredd i år (7, 9, 3, 46)',
      'grupp = överlevande − uppåldrade + inflöde + restflöde + flyttnetto · vikt',
      'kontroll: Δbefolkning = födda − döda + flyttnetto'],
    limits:'Breda åldersgrupper. Födslar följer gruppen 19–64 som en grov exponering. Ändrat flyttnetto fördelas med fasta vikter (15, 12, 3, 65 och 5 %).'},
  {id:'services',model:'Services',name:'Verksamhet',sub:'Efterfrågan och kapacitet',x:380,y:40,color:'#237355',
    keys:['adjustment'],
    values:r=>[['Utbildning',idx(r.educationIndex)],['Äldreomsorg',idx(r.careIndex)],['Index','2025 = 100']],
    text:`Åldersgrupperna blir efterfrågan på tre verksamheter: utbildning, äldreomsorg och övrigt. Kapaciteten följer efterfrågan med fördröjning; en fast andel ändras inte alls. Kapaciteten vägs ihop med verksamheternas kostnader till en tjänstevolym som styr driftens kostnader.`,
    eq:['utbildning = 0,25 · (0–6)/bas + 0,60 · (7–15)/bas + 0,15 · (16–18)/bas',
      'äldreomsorg = (65+) / bas',
      'övrigt = befolkning / bas',
      'kapacitet = fg + anpassning · (0,25 + 0,75 · efterfrågan − fg)',
      'tjänstevolym = (1 250 · utbildning + 600 · omsorg + 1 173 · övrigt) / 3 023'],
    limits:'Kostnadsvikterna är illustrativa, inte kommunens verksamhetsbudget. Index för behov, inte antal elever eller brukare.'},
  {id:'operations',model:'OperatingAccounts',name:'Drift',sub:'Löner, pensioner, övrigt',x:720,y:40,color:'#237355',
    keys:['wageGrowth','priceGrowth','pensionGrowth','productivity','operatingRevenueGrowth'],
    values:r=>[['Löner',fmt(r.payroll)],['Övriga kostnader',fmt(r.otherOperatingExpense)],['Nettokostnad',fmt(r.cost)]],
    text:`Driftens nettokostnad byggs från bokslutets delar 2025. Löner följer lönebanan och tjänstevolymen, minus produktivitet. Övriga kostnader följer prisbanan och volymen. Pensionskostnaden har en egen bana. Verksamhetens intäkter, till exempel avgifter, följer befolkningen och dras av.`,
    eq:['löner = 2 288 · löneindex · tjänstevolym / produktivitet',
      'övriga kostnader = 1 297 · prisindex · tjänstevolym',
      'verksamhetsintäkter = 751 · intäktsindex · befolkning / befolkning 2025',
      'nettokostnad = löner + pension + övriga kostnader − verksamhetsintäkter − 1'],
    limits:'Produktivitet sänker bara lönekostnaden. −1 mnkr stämmer av bokslutets avrundning.'},
  {id:'revenues',model:'Revenue',name:'Intäkter',sub:'Skatt och bidrag',x:40,y:330,color:'#285f8c',
    keys:['taxGrowth','grantGrowth','taxRate','equalisationOffset'],
    values:r=>[['Skatt',fmt(r.tax)],['Bidrag',fmt(r.grants)],['Summa',fmt(r.tax+r.grants)]],
    text:`Skatt och generella bidrag utgår från en referensbana: SKR:s beräkning för Motala när planeringsunderlagen är aktiva, annars en illustrativ tillväxt. Banan skalas med föregående års befolkning. Fler eller färre i arbetsför ålder ändrar skatten, och utjämningen tar tillbaka det mesta av den avvikelsen via bidragen. En annan skattesats ändrar bara skatten.`,
    eq:['befolkningsfaktor = befolkning fg år / referensbefolkning',
      'avvikelse = referensskatt · befolkningsfaktor · (andel 19–64 / andel 2025 − 1)',
      'skatt = (referensskatt · befolkningsfaktor + avvikelse) · skattesats / 21,70',
      'bidrag = referensbidrag · befolkningsfaktor − utjämning · avvikelse'],
    limits:'Utjämningen är en förenklad känslighet, inte lagens beräkning av inkomst-, kostnads- och LSS-utjämning.'},
  {id:'capital',model:'Capital',name:'Kapital',sub:'Tillgångar och avskrivning',x:380,y:330,color:'#9b5f23',
    keys:['investment'],
    values:r=>[['Investering',fmt(r.investment)],['Avskrivning',fmt(r.depreciation)],['Tillgångar',fmt(r.assets)]],
    text:`Investeringar tas i bruk samma år. Avskrivningen räknas med en sammanvägd livslängd, härledd ur bokslutet: 2 997 mnkr i tillgångar och 180 mnkr i avskrivning ger knappt 17 år.`,
    eq:['livslängd = 2 997 / 180 ≈ 16,7 år',
      'avskrivning = (tillgångar fg år + ½ · investering) / livslängd',
      'tillgångar = fg år + investering − avskrivning'],
    limits:'Ingen uppdelning på anläggningar, pågående projekt eller försäljningar.'},
  {id:'finance',model:'Finance',name:'Finans',sub:'Resultat, kassa och lån',x:720,y:330,color:'#694b91',
    keys:['interestRate'],
    values:r=>[['Resultat',fmt(r.result)],['Räntor',fmt(r.interest)],['Låneskuld',fmt(r.debt)]],
    text:`Här möts allt. Årets resultat är intäkter minus kostnader. Kassaflödet från driften lägger tillbaka avskrivningen, som inte är en utbetalning. Räcker kassaflödet inte till investeringarna lånar kommunen mellanskillnaden; ett överskott amorterar lån. Räntan betalas på skulden vid årets början.`,
    eq:['ränta = låneskuld fg år · räntesats',
      'resultat = skatt + bidrag − nettokostnad − avskrivning + 15 − ränta − 4',
      'kassaflöde = resultat + avskrivning + pensionskostnad − pensionsutbetalning',
      'behov = investering − kassaflöde → lån om positivt, amortering om negativt',
      'låneskuld = fg år + nya lån − amortering'],
    limits:'15 mnkr finansiella intäkter och 4 mnkr övriga finansiella kostnader hålls fasta. Rörelsekapital, borgen och leasing ingår inte.'}
];
const W=260,H=150,byId=Object.fromEntries(COMPONENTS.map(c=>[c.id,c]));

// Arrows are the connect() statements in Motala.Annual. `value` gives mnkr for money flows (drawn
// to scale) and a label for the others.
export const FLOWS=[
  {from:'demography',to:'services',binding:'connect(demography.cohorts, services.cohorts)',label:'Åldersgrupper',d:'M300,105 L380,105'},
  {from:'demography',to:'operations',binding:'connect(demography.cohorts, operations.cohorts)',label:'Befolkning',d:'M170,40 C170,0 850,0 850,40'},
  {from:'demography',to:'revenues',binding:'connect(demography.cohorts, revenues.cohorts)',label:'Befolkning fg år',d:'M110,190 L110,330'},
  {from:'services',to:'operations',binding:'connect(services.serviceVolume, operations.serviceVolume)',label:'Tjänstevolym',d:'M640,105 L720,105'},
  {from:'operations',to:'finance',binding:'connect(operations.accounts, finance.operations)',label:'Nettokostnad',money:r=>r.cost,d:'M850,190 L850,330'},
  {from:'operations',to:'finance',binding:'connect(operations.accounts, finance.operations)',label:'Pension',money:r=>r.pensionExpense,d:'M930,190 L930,330'},
  {from:'revenues',to:'finance',binding:'connect(revenues.taxAndGrants, finance.taxAndGrants)',label:'Skatt + bidrag',money:r=>r.tax+r.grants,d:'M170,480 C170,530 790,530 790,480'},
  {from:'capital',to:'finance',binding:'connect(capital.depreciation, finance.depreciation)',label:'Avskrivning',money:r=>r.depreciation,d:'M640,405 L720,405'},
  {from:'input',to:'capital',binding:'connect(scenario.investment, capital.investment)',label:'Investering',money:r=>r.investment,d:'M510,280 L510,330'},
  {from:'input',to:'finance',binding:'connect(scenario.investment, finance.investment)',label:'',money:r=>r.investment,d:'M580,266 C690,266 760,286 760,330'}
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
  source.then(text=>{for(const c of COMPONENTS) code[c.id]=modelicaSection(text,c.model);if(run) renderPanel();}).catch(()=>{});

  root.innerHTML=`<div class="model-toolbar"><label for="model-year">År</label><input id="model-year" type="range" min="1" max="1" step="1"><output id="model-year-label"></output></div>
<div class="model-diagram" id="model-diagram"></div>
<p class="chart-note">Klicka på en del för att läsa hur den räknar och ändra dess antaganden. Pilarna är modellens kopplingar; pengaflödenas tjocklek motsvarar beloppet för valt år. Diagrammet följer placeringen i <code>Motala.Annual</code>.</p>
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
    paramSignature=controls.map(x=>x.label+x.unit+x.min+x.max).join('|');
    $('model-detail').innerHTML=`<section class="panel model-panel" style="--node:${c.color}">
<div class="model-panel-text"><p class="eyebrow">${safe(c.model.toUpperCase())} · MOTALA.COMPONENTS</p><h2>${safe(c.name)}</h2><p>${safe(c.text)}</p>
<h3>Ekvationer, ett steg per år</h3><ul class="equations">${c.eq.map(e=>`<li><code>${safe(e)}</code></li>`).join('')}</ul>
<p class="chart-note">${safe(c.limits)}</p>
${code[c.id]?`<details><summary>Visa Modelica-koden</summary><pre class="modelica"><code>${safe(code[c.id])}</code></pre></details>`:''}</div>
<div class="model-panel-params"><p class="eyebrow">ANTAGANDEN</p>${controls.length?controls.map(x=>`<div class="slider"><div class="slider-top"><label for="m-${x.key}">${safe(x.label)}</label><div class="number"><input id="m-${x.key}" data-mkey="${x.key}" type="number" min="${x.min}" max="${x.max}" step="any" value="${safe(x.value)}"><span>${safe(x.unit)}</span></div></div><input data-mkey="${x.key}" type="range" min="${x.min}" max="${x.max}" step="${x.step}" value="${safe(x.value)}" aria-label="${safe(x.label)}, reglage"><div class="slider-help"><span>${safe(x.help)}</span></div></div>`).join(''):'<p class="muted">Inga justerbara antaganden.</p>'}
<p class="small muted">Samma antaganden som i Scenariolabbet. Ändringar gäller från 2026.</p></div></section>`;
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
