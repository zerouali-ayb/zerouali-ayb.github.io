// يحفظ التطبيق في الهاتف ليعمل دون إنترنت
const V="hijri-v1";
const SHELL=["./","index.html","manifest.webmanifest","icon.svg","icon-192.png","icon-512.png","data.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const u=new URL(e.request.url);if(e.request.method!=="GET")return;
  // البيانات: من الشبكة أولا، ثم المحفوظ
  if(u.origin===location.origin&&u.pathname.endsWith("/data.json")){
    e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open(V).then(x=>x.put("data.json",c));return r}).catch(()=>caches.match("data.json")));return}
  // الخطوط: المحفوظ ثم تحديث في الخلفية
  if(u.host==="fonts.googleapis.com"||u.host==="fonts.gstatic.com"){
    e.respondWith(caches.open(V).then(c=>c.match(e.request).then(hit=>{const net=fetch(e.request).then(r=>{c.put(e.request,r.clone());return r}).catch(()=>hit);return hit||net})));return}
  // صفحة التطبيق: الشبكة أولا مع رجوع للمحفوظ، لتصل التعديلات
  if(u.origin===location.origin){
    const cached=()=>caches.match(e.request,{ignoreSearch:true}).then(h=>h||caches.match("index.html"));
    const net=fetch(e.request).then(r=>{if(r.ok){const c=r.clone();caches.open(V).then(x=>x.put(e.request,c))}return r});
    // اتصال ضعيف: بعد 4 ثوان نعرض المحفوظ
    e.respondWith(Promise.race([net,new Promise(res=>setTimeout(()=>res(null),4000))]).then(r=>r||cached()).catch(cached))}
});
