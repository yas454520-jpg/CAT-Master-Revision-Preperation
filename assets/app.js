const KEY="catMasterPrepTracker.v2";
const fresh=()=>{let s={settings:{rc:{},dilr:{},crBank:1000,vaBank:500},daily:{},qa:[],eod:{}};["M1","M2","M3","M4","M5"].forEach(m=>s.settings.rc[m]={easy:50,medium:50});["M1","M2","M3","M4"].forEach(m=>s.settings.dilr[m]={DI:20,LR:20});return s};
let state=load();
function load(){try{let x=JSON.parse(localStorage.getItem(KEY));return x&&x.settings?x:fresh()}catch(e){return fresh()}}
function save(){localStorage.setItem(KEY,JSON.stringify(state))}
const today=()=>new Date().toISOString().slice(0,10);
const rand=n=>Math.floor(Math.random()*Math.max(1,n))+1;
function unique(n,max){const a=[];while(a.length<Math.min(n,max)){let x=rand(max);if(!a.includes(x))a.push(x)}return a}
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function parseAcc(v){v=String(v||"").trim();if(!v)return null;if(v.includes("/")){let p=v.split("/").map(Number);return p[1]?Math.max(0,Math.min(100,p[0]/p[1]*100)):null}let n=parseFloat(v);return Number.isFinite(n)?Math.max(0,Math.min(100,n)):null}
document.getElementById("dateText").textContent=new Date().toLocaleDateString(undefined,{weekday:"short",day:"2-digit",month:"short",year:"numeric"});

document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".nav button,.page").forEach(x=>x.classList.remove("active"));b.classList.add("active");document.getElementById(b.dataset.page).classList.add("active");render()});

function generate(){
 const d=state.daily[today()]||{items:[],reflection:""};
 let items=[];
 // Four RCs: exactly 2 Easy + 2 Medium. Module/question pair is unique.
 const used=new Set();
 for(const level of ["E","E","M","M"]){
   let tries=0, item;
   do{
     const m="M"+rand(5), max=state.settings.rc[m][level==="E"?"easy":"medium"];
     item={id:`${m}(${level}) Q${rand(max)}`,type:"VARC",done:false,acc:""};
     tries++;
   }while(used.has(item.id)&&tries<100);
   used.add(item.id);items.push(item);
 }
 // 10 CR + 5 VA unique question numbers.
 unique(10,state.settings.crBank).forEach(q=>items.push({id:`CR Q${q}`,type:"VARC",done:false,acc:""}));
 unique(5,state.settings.vaBank).forEach(q=>items.push({id:`VA Q${q}`,type:"VARC",done:false,acc:""}));
 // Four DILR sets: two DI + two LR, across M1-M4.
 const dlUsed=new Set();
 for(const t of ["DI","DI","LR","LR"]){
   let tries=0,item;
   do{const m="M"+rand(4),max=state.settings.dilr[m][t];item={id:`${m}(${t}) Q${String(rand(max)).padStart(2,"0")}`,type:"DILR",done:false,acc:""};tries++}while(dlUsed.has(item.id)&&tries<100);
   dlUsed.add(item.id);items.push(item);
 }
 state.daily[today()]={items,reflection:d.reflection||""};save();render();notice("genAlert","Today's practice set has been generated.","success");
}
document.getElementById("generate").onclick=generate;

function renderTasks(){
 const d=state.daily[today()],items=d?.items||[];
 for(const type of ["VARC","DILR"]){
  const el=document.getElementById(type==="VARC"?"varcTasks":"dilrTasks"),a=items.filter(x=>x.type===type);
  el.innerHTML=a.length?a.map((x,i)=>`<div class="task ${x.done?"done":""}"><input class="check" type="checkbox" data-type="${type}" data-i="${i}" ${x.done?"checked":""}><span class="qid">${esc(x.id)}</span><span class="tag">${x.done?"Done":"Pending"}</span><input class="acc" placeholder="e.g. 80%" value="${esc(x.acc)}" data-acc="${type}" data-i="${i}"></div>`).join(""):`<div class="empty">No practice set yet.<br>Click “Generate Today's Practice”.</div>`;
  el.querySelectorAll("[data-type]").forEach(c=>c.onchange=()=>{let x=a[+c.dataset.i];x.done=c.checked;save();renderTasks();renderProgress()});
  el.querySelectorAll("[data-acc]").forEach(c=>c.onchange=()=>{a[+c.dataset.i].acc=c.value;save();renderProgress()});
  const done=a.filter(x=>x.done).length;document.getElementById(type==="VARC"?"varcCount":"dilrCount").textContent=`${done} / ${a.length|| (type==="VARC"?19:4)}`;
 }
}
function renderProgress(){const a=state.daily[today()]?.items||[],done=a.filter(x=>x.done).length,p=a.length?Math.round(done/a.length*100):0;document.getElementById("progressBar").style.width=p+"%";document.getElementById("progressText").textContent=`${done} of ${a.length||23} completed (${p}%)`}

document.getElementById("qaForm").onsubmit=e=>{e.preventDefault();state.qa.unshift({date:today(),chapter:chapter.value,subtopic:subtopic.value,category:category.value,stage:stage.value,accuracy:qaAccuracy.value,minutes:Number(qaMinutes.value)||0,notes:qaNotes.value});save();e.target.reset();qaMinutes.value=30;render();notice("settingsAlert","");};
function renderQA(){const q=state.qa,total=q.reduce((a,x)=>a+x.minutes,0),master=q.filter(x=>x.stage==="Mastered").length;document.getElementById("qaStats").innerHTML=[["Total Logs",q.length],["Mastered",master],["Study Time",`${Math.floor(total/60)}h ${total%60}m`],["Active Revisions",q.filter(x=>x.stage!=="Mastered").length]].map(x=>`<div class="card stat"><div class="num">${x[1]}</div><div class="label">${x[0]}</div></div>`).join("");document.getElementById("qaTable").innerHTML=q.length?q.map(x=>`<tr><td>${x.date}</td><td>${esc(x.chapter)}</td><td>${esc(x.subtopic)}</td><td>${esc(x.category)}</td><td>${esc(x.stage)}</td><td>${esc(x.accuracy)||"-"}</td><td>${x.minutes} min</td></tr>`).join(""):`<tr><td colspan="7" class="empty">No QA revision logs yet.</td></tr>`}

function eodMetrics(){const items=state.daily[today()]?.items||[],done=items.filter(x=>x.done),q=state.qa.filter(x=>x.date===today()),vals=done.map(x=>parseAcc(x.acc)).filter(x=>x!==null),qaTime=q.reduce((a,x)=>a+x.minutes,0);return{v:done.filter(x=>x.type==="VARC").length,d:done.filter(x=>x.type==="DILR").length,q:q.length,acc:vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length):0,time:qaTime}}
function renderEOD(){const m=eodMetrics();document.getElementById("eodStats").innerHTML=[["VARC Completed",m.v],["DILR Completed",m.d],["QA Items",m.q],["Overall Accuracy",m.acc+"%"],["Study Time",`${Math.floor(m.time/60)}h ${m.time%60}m`]].map(x=>`<div class="card stat"><div class="num">${x[1]}</div><div class="label">${x[0]}</div></div>`).join("");document.getElementById("reflection").value=state.eod[today()]?.reflection||state.daily[today()]?.reflection||"";const h=Object.entries(state.eod).sort((a,b)=>b[0].localeCompare(a[0])).slice(0,10);document.getElementById("eodHistory").innerHTML=h.length?h.map(([d,x])=>`<div class="task"><div><b>${d}</b><div class="mini">${esc(x.reflection||"No reflection")}</div></div></div>`).join(""):`<div class="empty">No saved EOD logs yet.</div>`}
document.getElementById("saveEod").onclick=()=>{const r=document.getElementById("reflection").value;state.eod[today()]={reflection:r,metrics:eodMetrics()};if(state.daily[today()])state.daily[today()].reflection=r;save();renderEOD();alert("Daily log saved on this device.")};

function renderSettings(){
 const rc=document.getElementById("rcLimits");rc.innerHTML=["M1","M2","M3","M4","M5"].map(m=>`<div class="limitCard"><b>${m}</b><label class="field">Easy<input data-kind="rc" data-m="${m}" data-t="easy" type="number" min="1" value="${state.settings.rc[m].easy}"></label><label class="field">Medium<input data-kind="rc" data-m="${m}" data-t="medium" type="number" min="1" value="${state.settings.rc[m].medium}"></label></div>`).join("");
 const dl=document.getElementById("dilrLimits");dl.innerHTML=["M1","M2","M3","M4"].map(m=>`<div class="limitCard"><b>${m}</b><label class="field">DI<input data-kind="dilr" data-m="${m}" data-t="DI" type="number" min="1" value="${state.settings.dilr[m].DI}"></label><label class="field">LR<input data-kind="dilr" data-m="${m}" data-t="LR" type="number" min="1" value="${state.settings.dilr[m].LR}"></label></div>`).join("");
 document.getElementById("crBank").value=state.settings.crBank;document.getElementById("vaBank").value=state.settings.vaBank;
}
document.getElementById("settingsForm").onsubmit=e=>{e.preventDefault();document.querySelectorAll("[data-kind]").forEach(i=>{let o=state.settings[i.dataset.kind],m=i.dataset.m,t=i.dataset.t;o[m][t]=Math.max(1,Number(i.value)||1)});state.settings.crBank=Math.max(1,Number(document.getElementById("crBank").value)||1000);state.settings.vaBank=Math.max(1,Number(document.getElementById("vaBank").value)||500);save();notice("settingsAlert","Settings saved locally. Future generations will use these limits.","success")};
document.getElementById("export").onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:"application/json"}));a.download=`CAT_Master_Backup_${today()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
document.getElementById("restore").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const x=JSON.parse(r.result);if(!x.settings||!x.daily||!x.qa||!x.eod)throw Error("bad");state=x;save();render();notice("settingsAlert","Backup restored successfully.","success")}catch(_){notice("settingsAlert","That file is not a valid CAT tracker backup.")}};r.readAsText(f)};
document.getElementById("clear").onclick=()=>{if(confirm("Delete ALL CAT tracker data stored by this website in this browser? Export a backup first if you may need it.")){localStorage.removeItem(KEY);state=fresh();render();notice("settingsAlert","All local CAT data has been deleted.","success")}};
function notice(id,msg,kind=""){const e=document.getElementById(id);if(!e)return;e.innerHTML=msg?`<div class="alert ${kind}">${esc(msg)}</div>`:"";if(msg)setTimeout(()=>{e.innerHTML=""},3500)}
function render(){renderTasks();renderProgress();renderQA();renderEOD();renderSettings()}render();
