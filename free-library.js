(() => {
"use strict";
const list=document.getElementById("dailyFreeList");
const status=document.getElementById("dailyFreeStatus");
const count=document.getElementById("dailyFreeCount");
const search=document.getElementById("dailyFreeSearch");
const category=document.getElementById("dailyFreeCategory");
const more=document.getElementById("dailyFreeMore");
if (!list || !status || !count || !search || !category || !more) return;

const PAGE=8;
const WAV_PATH=/^library\/audio\/20\d\d-\d\d-\d\d\/[0-9]{1,20}-[0-9]{1,5}\/[a-z][a-z0-9_]{1,70}_[0-9]{2}\.wav$/;
const CONTEXT=new Set(["cinematic","comedy","audio_drama","commercial","gaming","shortform"]);
let sounds=[],visible=PAGE,activeId=null,activeButton=null;
const player=new Audio();
player.preload="none";
player.volume=0.9;
player.addEventListener("ended",resetPlayer);
player.addEventListener("error",()=>{
  if(activeId) status.textContent="Audio gagal dimuat. Coba unduh WAV-nya.";
  resetPlayer();
});
function resetPlayer(){
  if(activeButton){activeButton.textContent="▶";activeButton.setAttribute("aria-label","Putar sound");}
  activeButton=null;activeId=null;
  list.querySelectorAll(".daily-free-row.is-playing").forEach(el=>el.classList.remove("is-playing"));
}
function setStatus(value){status.textContent=value;}
function valid(item){
  return item && typeof item.id==="string" && /^[a-z0-9_-]{4,110}$/.test(item.id) &&
    typeof item.url==="string" && WAV_PATH.test(item.url) &&
    typeof item.title==="string" && item.title.length<=70 &&
    typeof item.description==="string" && item.description.length<=220 &&
    CONTEXT.has(item.context) && typeof item.date_wib==="string" &&
    /^20\d\d-\d\d-\d\d$/.test(item.date_wib) && item.tier==="FREE_DEMO";
}
function makeText(tag,text,className){
  const el=document.createElement(tag);
  el.textContent=text;
  if(className)el.className=className;
  return el;
}
function labelOf(context){
  return {audio_drama:"Audio drama",gaming:"Game audio",cinematic:"Cinematic",comedy:"Comedy",
    commercial:"Commercial",shortform:"Short-form"}[context]||context;
}
function makeRow(item,index){
  const row=document.createElement("article");
  row.className="daily-free-row";
  row.setAttribute("role","listitem");
  const no=makeText("span",String(index+1).padStart(2,"0"),"daily-free-index mono");
  const play=document.createElement("button");
  play.type="button";play.className="daily-free-play";
  play.setAttribute("aria-label","Putar "+item.title);
  play.textContent="▶";
  play.addEventListener("click",async()=>{
    if(activeId===item.id){
      if(player.paused){
        try{await player.play();play.textContent="Ⅱ";}catch(e){setStatus("Pemutar gagal dibuka");}
      }else{player.pause();play.textContent="▶";}
      return;
    }
    player.pause();resetPlayer();
    activeId=item.id;activeButton=play;
    row.classList.add("is-playing");
    window.dispatchEvent(new Event("lal:external-play"));
    player.src=new URL(item.url,document.baseURI).href;
    player.currentTime=0;
    try{await player.play();play.textContent="Ⅱ";play.setAttribute("aria-label","Jeda "+item.title)}
    catch(e){resetPlayer();setStatus("Audio gagal diputar. Gunakan tombol WAV.")}
  });
  const body=document.createElement("div");
  body.className="daily-free-details";
  body.appendChild(makeText("h4",item.title));
  body.appendChild(makeText("p",item.description));
  const tags=document.createElement("div");
  tags.className="daily-free-tags";
  tags.appendChild(makeText("span",labelOf(item.context)));
  tags.appendChild(makeText("span","FREE WAV"));
  body.appendChild(tags);
  const date=makeText("time",item.date_wib,"daily-free-date mono");
  date.setAttribute("datetime",item.date_wib);
  const button=document.createElement("a");
  button.className="daily-free-download";
  button.href=new URL(item.url,document.baseURI).href;
  button.setAttribute("download",item.url.split("/").pop());
  button.setAttribute("aria-label","Unduh "+item.title+" WAV");
  button.textContent="↓ WAV";
  row.append(no,play,body,date,button);
  return row;
}
function filtered(){
  const query=search.value.trim().toLocaleLowerCase("id");
  const chosen=category.value;
  return sounds.filter(x=>(chosen==="all"||x.context===chosen) &&
    (!query || (x.title+" "+x.description+" "+labelOf(x.context)).toLocaleLowerCase("id").includes(query)));
}
function draw(){
  const matching=filtered();
  list.replaceChildren();
  for(const [index,item] of matching.slice(0,visible).entries())list.appendChild(makeRow(item,index));
  more.hidden=matching.length<=visible;
  if(!matching.length)list.appendChild(makeText("p",
    sounds.length?"Tidak ada suara yang cocok. Coba filter lain.":"Belum ada free demo yang terbit dari produksi harian.","daily-free-empty"));
  setStatus(sounds.length?matching.length+" dari "+sounds.length+" free audio tersedia":"Menunggu paket free demo pertama.");
}
function updateFilter(){visible=PAGE;player.pause();resetPlayer();draw();}
search.addEventListener("input",updateFilter);
category.addEventListener("change",updateFilter);
more.addEventListener("click",()=>{visible+=PAGE;draw();});
window.addEventListener("lal:internal-play",()=>{player.pause();resetPlayer();});
document.addEventListener("visibilitychange",()=>{if(document.hidden){player.pause();resetPlayer();}});
async function load(){
  setStatus("Memuat audio dari produksi...");
  try{
    const response=await fetch("./library/catalog.json",{cache:"no-store"});
    if(response.status===404){sounds=[];draw();return;}
    if(!response.ok)throw new Error("HTTP "+response.status);
    const catalog=await response.json();
    if(catalog.version!==1||!Array.isArray(catalog.sounds))throw new Error("Invalid catalog");
    sounds=catalog.sounds.filter(valid).sort((a,b)=>b.date_wib.localeCompare(a.date_wib));
    count.textContent=String(sounds.length).padStart(2,"0");
    draw();
  }catch(error){console.error("Unable to load free library:",error);
    list.replaceChildren(makeText("p","Katalog sedang tidak tersedia. Enam sound demo di atas tetap bisa dicoba.","daily-free-empty"));
    setStatus("Katalog belum tersedia.");
  }
}
load();
})();