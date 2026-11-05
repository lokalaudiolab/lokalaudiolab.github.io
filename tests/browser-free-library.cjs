"use strict";
const {chromium}=require("playwright-core");
const assert=require("node:assert/strict");
const {execFileSync}=require("node:child_process");

const chrome=execFileSync("bash",["-lc","command -v google-chrome || command -v chromium || command -v chromium-browser"]).toString().trim();
const item={
  id:"free-42071265691-1-comedy_bonk_01",
  title:"Comedy Bonk",
  context:"comedy",
  description:"Original procedural bonk accent",
  duration_seconds:0.3,
  date_wib:"2026-11-06",
  tier:"FREE_DEMO",
  url:"library/audio/2026-11-06/42071265691-1/comedy_bonk_01.wav",
  sha256:"a".repeat(64),
  source_release:"sfx-42071265691-1"
};
function wav(){
  const n=14400,buf=Buffer.alloc(44+n*2);
  buf.write("RIFF",0);buf.writeUInt32LE(36+n*2,4);buf.write("WAVE",8);
  buf.write("fmt ",12);buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);
  buf.writeUInt16LE(1,22);buf.writeUInt32LE(48000,24);buf.writeUInt32LE(96000,28);
  buf.writeUInt16LE(2,32);buf.writeUInt16LE(16,34);buf.write("data",36);buf.writeUInt32LE(n*2,40);
  for(let i=0;i<n;i++)buf.writeInt16LE(Math.round(Math.sin(i*2*Math.PI*440/48000)*12000),44+i*2);
  return buf;
}
(async()=>{
  const browser=await chromium.launch({executablePath:chrome,headless:true,args:["--no-sandbox","--disable-dev-shm-usage","--autoplay-policy=no-user-gesture-required"]});
  try{
    const page=await browser.newPage({viewport:{width:390,height:844},acceptDownloads:true});
    const errors=[];page.on("pageerror",e=>errors.push(e.message));
    await page.route("**/library/catalog.json",route=>route.fulfill({
      status:200,contentType:"application/json",body:JSON.stringify({version:1,sounds:[item]})
    }));
    await page.route("**/library/audio/**",route=>route.fulfill({
      status:200,contentType:"audio/wav",body:wav()
    }));
    await page.goto("http://127.0.0.1:8765/",{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>document.getElementById("dailyFreeCount").textContent==="01");
    assert.equal(await page.locator(".daily-free-row").count(),1);
    assert.match(await page.locator(".daily-free-row h4").textContent(),/Comedy Bonk/);
    assert.match(await page.locator("#dailyFreeStatus").textContent(),/1 dari 1/);
    await page.locator("#dailyFreeSearch").fill("not found");
    assert.equal(await page.locator(".daily-free-row").count(),0);
    await page.locator("#dailyFreeSearch").fill("");
    await page.locator("#dailyFreeCategory").selectOption("cinematic");
    assert.equal(await page.locator(".daily-free-row").count(),0);
    await page.locator("#dailyFreeCategory").selectOption("comedy");
    assert.equal(await page.locator(".daily-free-row").count(),1);
    await page.locator(".daily-free-play").click();
    await page.waitForTimeout(80);
    assert.match(await page.locator(".daily-free-row").getAttribute("class"),/is-playing/);
    assert.match(await page.locator(".daily-free-play").textContent(),/Ⅱ/);
    const dl=page.waitForEvent("download");
    await page.locator(".daily-free-download").click();
    assert.equal((await dl).suggestedFilename(),"comedy_bonk_01.wav");
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
    assert.ok(overflow<=2,"mobile horizontal overflow: "+overflow);
    assert.deepEqual(errors,[]);
    console.log("FREE LIBRARY BROWSER PASS: JSON catalog, search, category, playback, WAV download, mobile layout, JS errors");
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
