/* Terminal-Schule — Service Worker (Offline-Caching / PWA).
   Cache-first für die App-Shell, danach Netzwerk. Version hochzählen = Update. */
const CACHE = "terminal-schule-v3";
const ASSETS = [
  "./", "./index.html", "./style.css", "./manifest.json", "./icon.svg",
  "./trainer/", "./trainer/index.html",
  "./fertig/", "./fertig/index.html",
  "./fonts/orbitron.woff2", "./loesungen.pdf"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(ASSETS.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((resp) => {
        const copy = resp.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return resp;
      }).catch(() => caches.match("./index.html"))
    )
  );
});
