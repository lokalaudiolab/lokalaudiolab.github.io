const CACHE='viola-android-v4';
const CORE=['./','./index.html','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('viola-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const req=event.request,u=new URL(req.url);
  if(req.method!=='GET'||u.origin!==self.location.origin||!u.pathname.startsWith('/viola/'))return;
  if(u.pathname.includes('/api/')||u.pathname.includes('/functions/'))return;
  event.respondWith((async()=>{
    try{
      const response=await fetch(req);
      if(response.ok){const cache=await caches.open(CACHE);cache.put(req,response.clone()).catch(()=>{});}
      return response;
    }catch{
      return (await caches.match(req))||(req.mode==='navigate'?await caches.match('./index.html'):Response.error());
    }
  })());
});
