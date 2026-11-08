import {sum,validateRevenuePath} from './scenario-inputs.js';
import {createWorkerEngine,ENGINE} from './jit-engine.js';
import {modelicaSource} from './modelica-adapter.js';
import {openScenarioReport} from './pdf-report.js';
import {createModelView} from './model-view.js';
const $=id=>document.getElementById(id),nf=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:0}),fmt=x=>nf.format(x),decimal=x=>new Intl.NumberFormat('sv-SE',{maximumFractionDigits:1}).format(x);
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const definitions=[
  ['taxGrowth','Skatteunderlag, årlig tillväxt',0,7,.1,'%', 'Illustrativ nationell referens'],
  ['wageGrowth','Löner, årlig ökning',0,7,.1,'%', 'Bas: 2 288 mnkr exklusive pensioner'],
  ['pensionGrowth','Pensionskostnad, årlig ökning',-30,30,.5,'%', 'Separat från löner. Bas: 190 mnkr'],
  ['priceGrowth','Övriga priser, årlig ökning',0,6,.1,'%', 'Årlig prisförändring'],
  ['migrationDelta','Förändrat årligt flyttnetto',-400,600,10,'pers.', 'Förändring mot kalibrerat restflöde'],
  ['interestRate','Genomsnittlig låneränta',0,7,.1,'%', 'På ingående banklåneskuld'],
  ['investment','Årliga investeringar',0,800,1,'mnkr', 'Bokslut 2025: 413 mnkr'],
  ['productivity','Årlig produktivitetsökning',0,2,.1,'%', 'Scenario, ej belagd effektivisering']
];
const advanced=[['grantGrowth','Bidrag, årlig referenstillväxt',0,6,.1,'%', 'Förenklad intäktsbana'],['operatingRevenueGrowth','Verksamhetsintäkter, årlig ökning',-5,8,.1,'%', '751 mnkr i basåret, volymjusterat'],['birthChange','Förändring i födelsetal',-30,30,1,'%', 'Mot basårets födelseexponering'],['taxRate','Kommunal skattesats',19,24,.1,'%', 'Bokslut: 21,70 %'],['adjustment','Årlig kapacitetsanpassning',0,1,.05,'', '0 = låst kapacitet; 1 = direkt anpassning'],['equalisationOffset','Utjämning av lokal skatteavvikelse',0,1,.05,'', 'Känslighet, ej exakt lagberäkning']];
let engine,b,history,planning,overrides={},path=null,run,base,version=0,modelSource=null,modelView=null;
const sourcedRates={taxGrowth:['Skatteunderlag, avvikelse mot SKR','taxBaseGrowth'],wageGrowth:['Arbetskraft, avvikelse mot SKR','labourCostGrowth'],priceGrowth:['Övriga priser, avvikelse mot SKR','otherPriceGrowth']};
function controlDefinitions(defs){return defs.map(d=>b.planningInputs&&sourcedRates[d[0]]?[d[0],sourcedRates[d[0]][0],-3,3,.1,'pp','Procentenheter mot SKR:s årsvisa bana']:d);}
function planningControls(){makeControls(controlDefinitions(definitions),'sliders');makeControls(controlDefinitions(advanced),'advanced');syncControls();}
function report(e){$('error').textContent=e.message;$('error').hidden=false;}
function makeControls(defs,id){$(id).innerHTML=defs.map(([key,label,min,max,step,unit,help])=>`<div class="slider"><div class="slider-top"><label for="${key}">${label}</label><div class="number"><input id="${key}" data-key="${key}" type="number" min="${min}" max="${max}" step="${step}" aria-label="${label}"><span>${unit}</span></div></div><input id="${key}-range" data-key="${key}" type="range" min="${min}" max="${max}" step="${step}" aria-label="${label}, reglage"><div class="slider-help"><span>${help}</span></div></div>`).join('');}
// `editing` is the field the user is typing in. Rewriting its value mid-edit drops a trailing decimal point ("2." → "2").
function syncControls(editing=null){for(const [k] of [...definitions,...advanced]){const value=(overrides[k]??b.assumptions[k])-(b.planningInputs&&sourcedRates[k]?b.assumptions[k]:0);if($(k)!==editing)$(k).value=Number(value.toFixed(2));$(k).step='any';if($(k+'-range')!==editing)$(k+'-range').value=value;}}
function chart(id,series,{unit='',height=255}={}) {
  const width=760,left=62,right=22,top=20,bottom=38,values=series.flatMap(s=>s.values).filter(Number.isFinite);
  let low=Math.min(...values),high=Math.max(...values);if(low===high){low-=1;high+=1;}const pad=(high-low)*.15;low-=pad;high+=pad;
  const x=i=>left+i*(width-left-right)/(run.rows.length-1),y=v=>top+(high-v)*(height-top-bottom)/(high-low);
  const lines=Array.from({length:5},(_,i)=>{const v=low+(high-low)*i/4;return `<line x1="${left}" y1="${y(v)}" x2="${width-right}" y2="${y(v)}" stroke="#e8ede5"/><text x="${left-11}" y="${y(v)+4}" text-anchor="end" fill="#78837d" font-size="11">${fmt(v)}</text>`;}).join('');
  const zero=low<0&&high>0?`<line x1="${left}" x2="${width-right}" y1="${y(0)}" y2="${y(0)}" stroke="#aab7a2" stroke-dasharray="3 4"/>`:'';
  const paths=series.map(s=>`<path d="${s.values.map((v,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ')}" fill="none" stroke="${s.color}" stroke-width="${s.thin?1.3:2.8}" ${s.dash?'stroke-dasharray="5 5"':''}/>${s.thin?'':s.values.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${s.color}"><title>${safe(s.name)} ${run.rows[i].year}: ${fmt(v)} ${unit}</title></circle>`).join('')}`).join('');
  const labels=run.rows.map((r,i)=>`<text x="${x(i)}" y="${height-10}" text-anchor="middle" fill="#78837d" font-size="11">${r.year}</text>`).join('');
  $(id).innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${safe(series.map(s=>s.name).join(', '))}, ${run.rows[0].year}–${run.rows.at(-1).year}. Se tabeller för värden."><title>${safe(series.map(s=>s.name).join(', '))}</title>${lines}${zero}${paths}${labels}</svg>`;
}
function ledger() {
  const cols=[['year','År'],['tax','Skatt'],['grants','Bidrag & utj.'],['cost','Nettodrift'],['depreciation','Avskr.'],['interest','Ränta'],['result','Resultat'],['investment','Invest.'],['debt','Låneskuld'],['cash','Kassa']];
  $('ledger').innerHTML=`<caption>Observerat 2025. Scenarier 2026–2033. Alla belopp i mnkr.</caption><thead><tr>${cols.map(c=>`<th scope="col">${c[1]}</th>`).join('')}</tr></thead><tbody>${run.rows.map(r=>`<tr>${cols.map(([k],i)=>`<${i?'td':'th scope="row"'} ${r[k]<0?'class="negative"':''}>${k==='year'?r[k]:fmt(r[k])}</${i?'td':'th'}>`).join('')}</tr>`).join('')}</tbody>`;
  $('cohort-table').innerHTML=`<thead><tr><th scope="col">År</th>${b.ageGroups.map(x=>`<th scope="col">${x}</th>`).join('')}<th scope="col">Totalt</th></tr></thead><tbody>${run.rows.map(r=>`<tr><th scope="row">${r.year}</th>${r.cohorts.map(x=>`<td>${fmt(x)}</td>`).join('')}<td>${fmt(r.population)}</td></tr>`).join('')}</tbody>`;
  const components=[['payroll','Personal exkl. pension'],['pensionExpense','Pensionskostnad'],['otherOperatingExpense','Övriga kostnader'],['operatingRevenue','Verksamhetsintäkter'],['cost','Nettodrift'],['pensionCashPayments','Pensionsbetalning'],['operatingCash','Operativt kassaflöde']];
  $('operating-ledger').innerHTML=`<caption>Mnkr. Basår är bokslut; framtida pensionsbetalningar antas motsvara kostnaden om ingen separat betalningsbana anges.</caption><thead><tr><th scope="col">År</th>${components.map(c=>`<th scope="col">${c[1]}</th>`).join('')}</tr></thead><tbody>${run.rows.map(r=>`<tr><th scope="row">${r.year}</th>${components.map(([k])=>`<td>${r[k]==null?'—':fmt(r[k])}</td>`).join('')}</tr>`).join('')}</tbody>`;
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
async function drawOnce() {
  try {
    const a={...b.assumptions,...overrides},stressed=path?[]:[-1,1];
    const requests=[{overrides,revenuePath:path},{overrides:{},revenuePath:path},
      ...stressed.map(d=>({overrides:stressOverrides(a,d),revenuePath:path})),
      ...sensitivityCases.map(([k,d])=>({overrides:{...overrides,[k]:a[k]+d},revenuePath:path}))];
    const results=await engine.simulateMany(b,history,requests);
    if(dirty) return;
    for(const r of results.slice(0,2)) if(r.error) throw Error(r.error);
    run=results[0].run;base=results[1].run;version++;modelView?.update(run);$('error').hidden=true;$('engine').textContent=ENGINE;
    const stressRuns=results.slice(2,2+stressed.length),sensitivityRuns=results.slice(2+stressed.length);
    const end=run.rows.at(-1),initial=run.rows[0],margin=end.result/(end.tax+end.grants)*100;
    $('metrics').innerHTML=[['Resultat '+end.year,fmt(end.result),'mnkr',`${decimal(margin)} % av skatt och bidrag`],['Banklåneskuld '+end.year,fmt(end.debt),'mnkr',`${fmt(end.debt-initial.debt)} mnkr förändring från 2025`],['Invånare '+end.year,fmt(end.population),'pers.',`${fmt(end.population-initial.population)} personer från 2025`]].map(([label,value,unit,detail])=>`<div class="metric"><div class="metric-label">${label}</div><div class="metric-number">${value}<small>${unit}</small></div><div class="metric-detail">${detail}</div></div>`).join('');
    const stresses=stressRuns.map((r,i)=>r.run?{name:'Stress '+(stressed[i]<0?'svag':'stark'),values:r.run.rows.map(x=>x.result),color:'#b4c0ae',thin:true}:null).filter(Boolean);
    chart('result-chart',[...stresses,{name:'Grundbana',values:base.rows.map(r=>r.result),color:'#ad8053',dash:true},{name:'Ditt scenario',values:run.rows.map(r=>r.result),color:'#17634e'}],{unit:'mnkr'});
    document.querySelector('.legend-line.stress').hidden=!!path;
    chart('debt-chart',[{name:'Grundbana',values:base.rows.map(r=>r.debt),color:'#ad8053',dash:true},{name:'Låneskuld',values:run.rows.map(r=>r.debt),color:'#17634e'}],{unit:'mnkr',height:205});
    const sensitivities=sensitivityCases.map(([,,label],i)=>({label,delta:sensitivityRuns[i].run?sensitivityRuns[i].run.rows.at(-1).result-end.result:NaN}));
    const max=Math.max(...sensitivities.filter(s=>Number.isFinite(s.delta)).map(s=>Math.abs(s.delta)),1);$('sensitivity').innerHTML=sensitivities.map(s=>`<div class="sensitivity-row"><div class="sensitivity-label"><span>${s.label}</span><strong>${Number.isFinite(s.delta)?`${s.delta>0?'+':''}${fmt(s.delta)} mnkr`:'—'}</strong></div><div class="sensitivity-track"><div class="sensitivity-fill ${s.delta>0?'positive':''}" style="width:${Number.isFinite(s.delta)?Math.abs(s.delta)/max*100:0}%"></div></div></div>`).join('');
    const colors=['#17634e','#80a979','#c8d779','#ad8053','#516e9c'];chart('population-chart',b.ageGroups.map((name,i)=>({name,values:run.rows.map(r=>r.cohorts[i]),color:colors[i]})),{unit:'personer'});
    $('age-legend').innerHTML=b.ageGroups.map((x,i)=>`<span><span style="color:${colors[i]}">●</span> ${x}</span>`).join('');chart('demand-chart',[{name:'Utbildning',values:run.rows.map(r=>r.educationIndex*100),color:'#17634e'},{name:'Äldreomsorg',values:run.rows.map(r=>r.careIndex*100),color:'#ad8053'}],{unit:'index'});
    $('revenue-status').textContent=path?`SKR-referens för Motala · ${path.vintage}`:(b.planningInputs?'SKR nationell trend · Motala-intäkter ej importerade':'Illustrativ intäktsbana · SKR ej importerad');$('clear-import').hidden=!path;
    for(const k of ['taxGrowth','grantGrowth']){$(k).disabled=!!path;$(k+'-range').disabled=!!path;}
    $('planning-status').textContent=b.planningInputs?(path?'Aktivt: befolkningsprognos, SKR:s Motala-intäkter och årsvisa kostnadsindex. Scenariot justerar intäkterna med förenklade samband.':'Aktivt: befolkningsprognos och SKR:s årsvisa index. Ingen lokal intäktsbana är vald.'):'Illustrativa antaganden aktiva. Nedladdade underlag visas som jämförelse.';
    ledger();
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
async function boot(){try{
  $('engine').textContent='Hämtar OpenModelica…';
  const mib=x=>(x/1048576).toFixed(0);
  engine=createWorkerEngine({
    onProgress:(loaded,total)=>{$('engine').textContent=total?`Hämtar OpenModelica ${Math.round(loaded/total*100)} % (${mib(total)} MB)`:`Hämtar OpenModelica ${mib(loaded)} MB`;},
    onCompiling:()=>{$('engine').textContent='Kompilerar Motala.mo…';}});
  engine.ready.catch(report);
  modelView=createModelView($('model-view'),{source:fetch('Motala.mo').then(r=>r.ok?r.text():Promise.reject(Error('Motala.mo')))});
  modelSource=fetch('Motala.mo').then(r=>r.text()).then(async text=>({file:'Motala.mo',sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(x=>x.toString(16).padStart(2,'0')).join('')})).catch(()=>null);
  const files=await Promise.all(['baseline.json','history.json','sources.json','backtest.json','municipal-benchmarks.json','planning-inputs.json'].map(async f=>{const r=await fetch(f);if(!r.ok){if(f==='backtest.json')return null;throw Error(`Kunde inte läsa ${f}`);}return r.json();}));
  [b,{rows:history}]=files;planning=files[5];b.planningInputs=planning;path=planning.revenuePath?validateRevenuePath(planning.revenuePath,b.baseYear):null;planningControls();draw();renderEvidence(files[2],files[3]);renderPlanning();
  $('municipal-benchmarks').innerHTML=`<thead><tr><th scope="col">2025</th><th scope="col">Budget/prognos</th><th scope="col">Utfall</th><th scope="col">Absolut fel</th></tr></thead><tbody>${files[4].rows.map(r=>`<tr><th scope="row">${({budget:'Budget',april:'Aprilprognos',august:'Augustiprognos'})[r.stage]}</th><td>${fmt(r.forecast)}</td><td>${fmt(r.actual)}</td><td>${fmt(Math.abs(r.forecast-r.actual))}</td></tr>`).join('')}</tbody>`;
  document.querySelector('.controls').addEventListener('input',event=>{const el=event.target;if(!el.dataset.key)return;
    // An empty or half-typed number ("", "-", "2,") is not a value yet; wait for more input instead of computing with 0.
    if(el.value===''||el.validity.badInput)return;
    if(!el.validity.valid){report(Error('Värdet ligger utanför reglagets intervall.'));return;}
    const k=el.dataset.key;overrides[k]=Number(el.value)+(b.planningInputs&&sourcedRates[k]?b.assumptions[k]:0);$('preset').value='custom';syncControls(el);draw();});
  // Normalise the number field's text once the user leaves it.
  document.querySelector('.controls').addEventListener('change',event=>{if(event.target.dataset.key)syncControls();});
  $('planning-enabled').onchange=()=>{const enabled=$('planning-enabled').checked;b.planningInputs=enabled?planning:null;path=enabled?(planning.revenuePath??null):null;planningControls();draw();};
  document.querySelectorAll('.tab').forEach(el=>el.addEventListener('click',()=>{document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!==el.dataset.tab);document.querySelectorAll('.tab').forEach(t=>{t.classList.toggle('active',t===el);t.setAttribute('aria-pressed',String(t===el));});}));
  $('docs-link').onclick=e=>{e.preventDefault();document.querySelector('.tab[data-tab="model"]').click();$('model').scrollIntoView({behavior:'smooth'});};
  $('reset').onclick=()=>{overrides={};$('preset').value='base';syncControls();draw();};
  $('preset').onchange=()=>{overrides=({base:{},adverse:{taxGrowth:2.5,wageGrowth:4,priceGrowth:3,interestRate:4,migrationDelta:-100},migration:{migrationDelta:300},investment:{investment:250}})[$('preset').value];syncControls();draw();};
  $('import').onchange=async e=>{try{const next=validateRevenuePath(JSON.parse(await e.target.files[0].text()),b.baseYear);await engine.simulate(b,history,overrides,next);path=next;draw();}catch(e){report(e);}finally{$('import').value='';}};
  $('clear-import').onclick=()=>{path=null;draw();};
  $('pdf').onclick=async()=>{
    // Open the tab inside the click, before any await, or the popup blocker stops it.
    const tab=window.open('','_blank');
    if(!tab){report(Error('Tillåt att rapporten öppnas i en ny flik för att exportera PDF.'));return;}
    tab.document.write('<p style="font:14px sans-serif">Förbereder rapporten…</p>');
    try{
      // Recompute now so the report always matches the current controls, even after a rejected draw.
      const [current,reference]=await Promise.all([engine.simulate(b,history,overrides,path),engine.simulate(b,history,{},path)]);
      await draw();
      openScenarioReport({baseline:structuredClone(b),run:current,referenceRun:reference,revenuePath:structuredClone(path),charts:Object.fromEntries(['result-chart','debt-chart','population-chart','demand-chart','sensitivity'].map(id=>[id,$(id).innerHTML]))},tab);
    }catch(e){tab.close();report(e);}};
  $('csv').onclick=()=>{const keys=['year','population','tax','grants','payroll','pensionExpense','pensionCashPayments','otherOperatingExpense','operatingRevenue','cost','depreciation','interest','otherFinancialExpense','result','operatingCash','investment','debt','cash'];download('motala-scenario.csv',keys.join(',')+'\n'+run.rows.map(r=>keys.map(k=>r[k]).join(',')).join('\n'),'text/csv');};
  $('json').onclick=async()=>download('motala-scenario.json',JSON.stringify({municipality:'0583',baseYear:b.baseYear,baseline:b,history,overrides:run.assumptions,revenuePath:path,calibration:run.calibration,annualInputs:run.inputs,planningStatus:run.planningStatus,engine:run.engine,modelSource:await modelSource,rows:run.rows,status:'Illustrative scenario, not validated forecast'},null,2),'application/json');
  $('modelica').onclick=()=>download('Scenario.mo',modelicaSource(b,history,overrides,path));
  $('wasm-status').textContent='OpenModelica kompilerar Motala.mo i din webbläsare (wasm-jit). Ändrade antaganden kör den kompilerade modellen igen; inget skickas till någon server.';
  // The compiler is OSMC-PL/AGPL software: name its exact revision, source and licence.
  fetch('omc-web/manifest.json').then(r=>r.ok?r.json():null).then(m=>{if(!m)return;
    const commit=m.commit?`<a href="https://github.com/OpenModelica/OpenModelica/commit/${safe(m.commit)}">${safe(m.revision)}</a>`:safe(m.revision);
    $('omc-version').innerHTML=`Kompilator: OpenModelica ${commit} · <a href="omc-web/LICENSE-OpenModelica.txt">licens (OSMC-PL eller AGPL 3)</a> · <a href="${safe(m.source)}">källkod</a>`;}).catch(()=>{});
}catch(e){report(e);}}
boot();
