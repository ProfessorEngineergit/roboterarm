/* roboterarm — Weboberfläche (vanilla JS, offline, ohne Abhängigkeiten)
 *
 * Vier Stufen, von einfach nach frei:
 *   Regler · Eigene Blöcke · Scratch · Python
 * Ein großer NOT-AUS ist immer sichtbar und stoppt sofort alles.
 */

const API = {
  async get(p) { const r = await fetch(p); return r.json(); },
  async post(p, b) { const r = await fetch(p, { method: "POST", body: JSON.stringify(b || {}) }); return r.json(); },
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const schlafe = (ms) => new Promise((r) => setTimeout(r, ms));

let tab = "regler";
let pollers = [];
let ABBRUCH = false;            // bricht laufende Block-/Warte-Sequenzen ab
let PROGRAMM = [];              // Block-Programm (Tab „Eigene Blöcke")
let WINKEL = {};                // letzte bekannte Gelenkwinkel (für das Live-Modell)
let KALIBDATA = { gelenke: {} };// zuletzt geladene Kalibrierwerte (für Modell-Drehrichtung)

function stopPoll() { pollers.forEach(clearInterval); pollers = []; }
function poll(fn, ms) { fn(); pollers.push(setInterval(fn, ms)); }

// Range-Regler „googly" füllen: linker Teil in Primärfarbe (CSS-Variable --pct).
function sliderFill(el) {
  const min = +el.min || 0, max = +el.max || 100;
  const pct = max > min ? ((+el.value - min) / (max - min)) * 100 : 0;
  el.style.setProperty("--pct", pct.toFixed(1) + "%");
}
function fuelleSlider() { document.querySelectorAll('input[type=range]').forEach(sliderFill); }
document.addEventListener("input", (e) => { if (e.target.matches('input[type=range]')) sliderFill(e.target); });

// --------------------------------- Start ---------------------------------
window.addEventListener("DOMContentLoaded", init);

async function init() {
  document.body.innerHTML = `
    <header>
      <h1>🤖 roboterarm</h1>
      <span class="backend" id="backend">…</span>
      <button class="notaus" id="notaus" onclick="panik()" title="Sofort alles stoppen">■ NOT-AUS</button>
      <nav id="nav"></nav>
    </header>
    <div class="statusbar" id="statusbar">…</div>
    <main><div id="inhalt"></div></main>
    <div id="toast" class="toast"></div>`;

  const navs = ["regler", "bloecke", "scratch", "python", "kalib"];
  const titel = { regler: "🎚 Regler", bloecke: "🧩 Eigene Blöcke", scratch: "🐱 Scratch",
                  python: "🐍 Python", kalib: "⚙ Kalibrieren" };
  document.getElementById("nav").innerHTML = navs.map(
    (n) => `<button id="nav_${n}" onclick="zeigeTab('${n}')">${titel[n]}</button>`).join("");

  setInterval(refreshStatus, 1000);
  refreshStatus();
  zeigeTab("regler");
}

async function refreshStatus() {
  try {
    const s = await API.get("/api/status");
    WINKEL = s.winkel;
    document.getElementById("backend").textContent = s.backend + " · " + s.projekt;
    document.getElementById("statusbar").innerHTML = Object.entries(s.winkel)
      .map(([k, v]) => `<span class="stat">${k} <b>${Math.round(v)}°</b></span>`).join("");
    if (tab === "kalib") zeichneArm();
  } catch (e) {}
}

function zeigeTab(name) {
  tab = name; stopPoll();
  document.querySelectorAll("#nav button").forEach((b) => b.classList.remove("aktiv"));
  document.getElementById("nav_" + name).classList.add("aktiv");
  ({ regler: renderRegler, bloecke: renderBloecke, scratch: renderScratch, python: renderPython,
     kalib: renderKalib }[name])();
}

// ------------------------------- NOT-AUS -------------------------------
async function panik() {
  ABBRUCH = true;
  try { await API.post("/api/panik"); } catch (e) {}
  const b = document.getElementById("notaus");
  if (b) { b.classList.add("blink"); setTimeout(() => b.classList.remove("blink"), 1500); }
  flash("⏹ NOT-AUS — alle Servos stromlos. Zum Weitermachen Servos wieder einschalten.");
  if (tab === "regler") renderRegler();   // Schalter zeigen jetzt „aus"
}

// ------------------------------- 1) Regler -------------------------------
async function renderRegler() {
  const s = await API.get("/api/status");
  WINKEL = s.winkel;
  const aktiv = s.aktiv || {};
  const regler = Object.entries(s.winkel).map(([n, w]) => {
    const an = aktiv[n] !== false;
    return `
    <div class="gelenk">
      <label><span class="gname">${n}</span>
        <span class="gright"><b id="v_${n}">${Math.round(w)}°</b>
          <label class="schalter" title="Servo an/aus">
            <input type="checkbox" ${an ? "checked" : ""} onchange="servoSchalt('${n}', this.checked)">
            <span class="schieber"></span></label>
        </span></label>
      <input type="range" id="r_${n}" min="0" max="180" value="${w}" oninput="rSet('${n}', this.value)" ${an ? "" : "disabled"}>
    </div>`;
  }).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Gelenke direkt steuern</h2>${regler}
      <div class="reihe">
        <button class="primary" onclick="API.post('/api/home').then(refreshRegler)">🏠 Grundstellung</button>
        <button onclick="API.post('/api/greifer',{aktion:'auf'}).then(refreshRegler)">✋ Greifer auf</button>
        <button onclick="API.post('/api/greifer',{aktion:'zu'}).then(refreshRegler)">✊ Greifer zu</button>
      </div>
      <div class="reihe">Tempo <input type="range" min="0" max="15" value="3" oninput="API.post('/api/tempo',{grad:Number(this.value)})"></div>
    </div>
    <div class="karte"><h2>Posen</h2>
      <div class="reihe">
        <input type="text" id="pose_name" placeholder="Posenname (z.B. winken_1)">
        <button class="primary" onclick="poseSpeichern()">＋ aktuelle Pose speichern</button>
      </div>
      <div id="pose_liste" class="pose-liste" style="margin-top:12px">…</div>
    </div>
    <div class="karte"><h2>Koordinaten (für Fortgeschrittene)</h2>
      <div class="reihe">
        x <input type="number" id="gx" value="120"> y <input type="number" id="gy" value="0"> z <input type="number" id="gz" value="60">
        <button class="primary" onclick="rGehe()">gehe zu</button>
        <span id="gehe_out" class="klein"></span>
      </div>
    </div>`;
  fuelleSlider();
  poseListe();
}
async function refreshRegler() { if (tab === "regler") renderRegler(); }

// ----- Live-Arm-Modell (SVG, reagiert auf die Gelenkwinkel) -----
function zeichneArm() {
  const box = document.getElementById("armmodell");
  if (!box) return;
  const W = WINKEL || {};
  const inv = (n) => !!(KALIBDATA.gelenke && KALIBDATA.gelenke[n] && KALIBDATA.gelenke[n].invertiert);
  const eff = (n, v) => inv(n) ? (180 - v) : v;     // Drehrichtung wie in der Kalibrierung
  const schulter = eff("schulter", W.schulter ?? 90), ellbogen = eff("ellbogen", W.ellbogen ?? 90);
  const basis = eff("basis", W.basis ?? 90), greifer = eff("greifer", W.greifer ?? 35);
  const S = 0.82, L1 = 61 * S, L2 = 80 * S, L3 = 80 * S;   // mm -> px (MK1)
  const bx = 120, bodenY = 232, topY = bodenY - L1;
  const rad = (d) => d * Math.PI / 180;
  // Oberarm: schulter=90 -> senkrecht nach oben; Unterarm relativ zum Ellbogen
  const aU = rad(schulter), aF = rad(schulter + (ellbogen - 90));
  const p1 = [bx + L2 * Math.cos(aU), topY - L2 * Math.sin(aU)];
  const p2 = [p1[0] + L3 * Math.cos(aF), p1[1] - L3 * Math.sin(aF)];
  // Greifer-Öffnung
  const auf = (greifer - 30) / (110 - 30);                  // 0..1 grob
  const spread = 6 + Math.max(0, Math.min(1, auf)) * 12;
  const gA = aF + Math.PI / 2, gl = 16;
  const gx1 = [p2[0] + spread * Math.cos(gA), p2[1] - spread * Math.sin(gA)];
  const gx2 = [p2[0] - spread * Math.cos(gA), p2[1] + spread * Math.sin(gA)];
  const gt1 = [gx1[0] + gl * Math.cos(aF), gx1[1] - gl * Math.sin(aF)];
  const gt2 = [gx2[0] + gl * Math.cos(aF), gx2[1] - gl * Math.sin(aF)];
  // Basis-Drehung (Top-Down-Mini-Dial)
  const dcx = 268, dcy = 52, dr = 26, ba = rad(basis - 90);
  const dpx = dcx + dr * Math.cos(ba), dpy = dcy + dr * Math.sin(ba);
  const f = (x) => x.toFixed(1);
  const ln = (a, b, cls) => `<line x1="${f(a[0])}" y1="${f(a[1])}" x2="${f(b[0])}" y2="${f(b[1])}" class="${cls}"/>`;
  const kreis = (c, r, cls) => `<circle cx="${f(c[0])}" cy="${f(c[1])}" r="${r}" class="${cls}"/>`;
  box.innerHTML = `
  <svg viewBox="0 0 320 250" class="arm-svg" xmlns="http://www.w3.org/2000/svg">
    <line x1="20" y1="${bodenY}" x2="300" y2="${bodenY}" class="boden"/>
    <rect x="${bx - 26}" y="${bodenY - 12}" width="52" height="12" rx="3" class="sockel"/>
    <rect x="${bx - 11}" y="${f(topY)}" width="22" height="${f(L1)}" rx="6" class="saeule"/>
    ${ln([bx, topY], p1, "segment")}
    ${ln(p1, p2, "segment")}
    ${ln(gx1, gt1, "greifer")}
    ${ln(gx2, gt2, "greifer")}
    ${kreis([bx, topY], 7, "gelenkpunkt")}
    ${kreis(p1, 6, "gelenkpunkt")}
    ${kreis(p2, 4, "gelenkpunkt")}
    <g class="dial">
      ${kreis([dcx, dcy], dr, "dial-bg")}
      ${ln([dcx, dcy], [dpx, dpy], "dial-zeiger")}
      ${kreis([dcx, dcy], 3, "gelenkpunkt")}
      <text x="${dcx}" y="${dcy + dr + 13}" class="dial-text">Basis ${Math.round(basis)}°</text>
    </g>
  </svg>`;
}
async function servoSchalt(name, an) {
  await API.post("/api/servo", { name, an });
  const r = document.getElementById("r_" + name);
  if (r) r.disabled = !an;
  flash(an ? `${name}: Servo an` : `${name}: Servo aus (locker)`);
}
let rLast = 0;
async function rSet(name, val) {
  document.getElementById("v_" + name).textContent = Math.round(val) + "°";
  WINKEL[name] = Number(val);
  const now = Date.now(); if (now - rLast < 70) return; rLast = now;
  await API.post("/api/gelenk", { name, winkel: Number(val) });
}
async function rGehe() {
  const r = await API.post("/api/gehe_zu", { x: Number(gx.value), y: Number(gy.value), z: Number(gz.value) });
  document.getElementById("gehe_out").textContent = JSON.stringify(r.winkel || r.fehler);
  refreshRegler();
}

// ----- Posen (grafisch: aktuelle Stellung speichern, anfahren, löschen) -----
async function poseListe() {
  const el = document.getElementById("pose_liste");
  if (!el) return;
  const p = await API.get("/api/posen");
  const posen = p.posen || {};
  const namen = Object.keys(posen);
  if (!namen.length) { el.innerHTML = '<p class="klein">Noch keine Pose. Stell den Arm ein und speichere ihn.</p>'; return; }
  el.innerHTML = namen.map((nm) => {
    const w = Object.entries(posen[nm]).map(([k, v]) => `${k[0]}${Math.round(v)}`).join(" ");
    return `<div class="pose-zeile">
      <span class="pose-name">${esc(nm)}</span>
      <span class="pose-werte klein">${w}</span>
      <span class="pose-aktion">
        <button class="primary" onclick="poseAnfahren('${esc(nm)}')">anfahren</button>
        <button onclick="poseLoeschen('${esc(nm)}')" title="löschen">✕</button>
      </span></div>`;
  }).join("");
}
async function poseSpeichern() {
  const name = (document.getElementById("pose_name").value || "").trim();
  if (!name) { flash("Bitte einen Posennamen eingeben."); return; }
  await API.post("/api/pose/speichern", { name });
  document.getElementById("pose_name").value = "";
  flash("Pose gespeichert: " + name);
  poseListe();
}
async function poseAnfahren(name) { await API.post("/api/pose/anfahren", { name }); refreshRegler(); }
async function poseLoeschen(name) { await API.post("/api/pose/loeschen", { name }); poseListe(); }

// ---------------------------- 2) Eigene Blöcke ----------------------------
const BLOCKARTEN = {
  home:        { text: "🏠 Grundstellung",       farbe: "b-move" },
  basis:       { text: "Basis auf [w]°",         farbe: "b-move", min: 0, max: 180, std: 90 },
  schulter:    { text: "Schulter auf [w]°",      farbe: "b-move", min: 0, max: 180, std: 90 },
  ellbogen:    { text: "Ellbogen auf [w]°",      farbe: "b-move", min: 0, max: 180, std: 90 },
  greifer_auf: { text: "✋ Greifer auf",          farbe: "b-grip" },
  greifer_zu:  { text: "✊ Greifer zu",           farbe: "b-grip" },
  warte:       { text: "⏱ warte [w] s",          farbe: "b-wait", min: 0, max: 30, std: 1 },
};
const hatParam = (d) => d.text.includes("[w]");

function renderBloecke() {
  ladeProgramm();
  const palette = Object.entries(BLOCKARTEN).map(([typ, d]) =>
    `<button class="palettenblock ${d.farbe}" onclick="blockAdd('${typ}')">${d.text.replace("[w]", "…")}</button>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="bloecke-layout">
      <div class="karte palette"><h2>Bausteine</h2>${palette}
        <p class="klein" style="margin-top:10px">Klick einen Baustein → er kommt rechts ins Programm.</p>
      </div>
      <div class="karte programm-spalte"><h2>Mein Programm</h2>
        <div id="programm" class="programm"></div>
        <div class="reihe" style="margin-top:12px">
          Wiederhole alles <input type="number" id="runden" value="1" min="1" max="99" style="width:56px">×
        </div>
        <div class="reihe">
          <button class="primary gross" onclick="bloeckeRun()">▶ Start</button>
          <button onclick="panik()">■ Stop</button>
          <button onclick="programmLeeren()">🗑 leeren</button>
        </div>
        <div class="klein" id="block_msg" style="margin-top:8px"></div>
      </div>
    </div>`;
  zeichneProgramm();
}

function blockText(d, b, i) {
  if (!hatParam(d)) return d.text;
  const inp = `<input type="number" class="binp" value="${b.wert}" min="${d.min}" max="${d.max}" onchange="blockSet(${i}, this.value)">`;
  return d.text.replace("[w]", inp);
}
function zeichneProgramm() {
  const el = document.getElementById("programm");
  if (!PROGRAMM.length) { el.innerHTML = '<p class="klein">Noch leer — wähle links Bausteine.</p>'; speichereProgramm(); return; }
  el.innerHTML = PROGRAMM.map((b, i) => {
    const d = BLOCKARTEN[b.typ];
    return `<div class="block ${d.farbe}" id="blk_${i}">
        <span class="bnr">${i + 1}</span>
        <span class="btext">${blockText(d, b, i)}</span>
        <span class="bctrl">
          <button onclick="blockMove(${i},-1)" title="hoch">▲</button>
          <button onclick="blockMove(${i},1)" title="runter">▼</button>
          <button onclick="blockDel(${i})" title="entfernen">✕</button>
        </span></div>`;
  }).join("");
  speichereProgramm();
}
function blockAdd(typ) {
  const d = BLOCKARTEN[typ];
  PROGRAMM.push({ typ, wert: hatParam(d) ? d.std : null });
  zeichneProgramm();
}
function blockSet(i, val) { PROGRAMM[i].wert = Number(val); speichereProgramm(); }
function blockDel(i) { PROGRAMM.splice(i, 1); zeichneProgramm(); }
function blockMove(i, dir) {
  const j = i + dir; if (j < 0 || j >= PROGRAMM.length) return;
  [PROGRAMM[i], PROGRAMM[j]] = [PROGRAMM[j], PROGRAMM[i]]; zeichneProgramm();
}
function programmLeeren() { PROGRAMM = []; zeichneProgramm(); }
function speichereProgramm() { try { localStorage.setItem("roboterarm_programm", JSON.stringify(PROGRAMM)); } catch (e) {} }
function ladeProgramm() {
  if (PROGRAMM.length) return;
  try { PROGRAMM = JSON.parse(localStorage.getItem("roboterarm_programm") || "[]"); } catch (e) { PROGRAMM = []; }
}

async function bloeckeRun() {
  if (!PROGRAMM.length) { msgBlock("Programm ist leer."); return; }
  ABBRUCH = false;
  const runden = Math.max(1, Number(document.getElementById("runden").value) || 1);
  msgBlock(`läuft … (${runden}×)`);
  for (let r = 0; r < runden && !ABBRUCH; r++) {
    for (let i = 0; i < PROGRAMM.length && !ABBRUCH; i++) {
      hebeHervor(i);
      await fuehreBlock(PROGRAMM[i]);
    }
  }
  hebeHervor(-1);
  msgBlock(ABBRUCH ? "gestoppt." : "fertig ✓");
}
async function fuehreBlock(b) {
  switch (b.typ) {
    case "home": await API.post("/api/home"); break;
    case "basis": case "schulter": case "ellbogen":
      await API.post("/api/gelenk", { name: b.typ, winkel: Number(b.wert) }); break;
    case "greifer_auf": await API.post("/api/greifer", { aktion: "auf" }); break;
    case "greifer_zu": await API.post("/api/greifer", { aktion: "zu" }); break;
    case "warte": await warteAbbrechbar(Number(b.wert) * 1000); break;
  }
}
async function warteAbbrechbar(ms) {
  const ende = Date.now() + ms;
  while (Date.now() < ende && !ABBRUCH) await schlafe(Math.min(100, Math.max(0, ende - Date.now())));
}
function hebeHervor(i) {
  document.querySelectorAll(".block").forEach((e) => e.classList.remove("aktivblock"));
  const el = document.getElementById("blk_" + i); if (el) el.classList.add("aktivblock");
}
function msgBlock(t) { const m = document.getElementById("block_msg"); if (m) m.textContent = t; }

// ------------------------------- 3) Scratch -------------------------------
async function renderScratch() {
  let vorhanden = false;
  try { vorhanden = (await API.get("/api/scratch/status")).vorhanden; } catch (e) {}
  const host = location.hostname || "localhost";
  if (vorhanden) {
    const ext = encodeURIComponent(`http://${host}:8765/roboterarm_extension.js`);
    document.getElementById("inhalt").innerHTML = `
      <div class="karte scratch-karte"><h2>Scratch — Blöcke ziehen</h2>
        <iframe class="scratch-frame" src="/turbowarp/index.html?extension=${ext}" allow="fullscreen" title="Scratch"></iframe>
        <p class="klein">Die „Roboterarm"-Blöcke findest du links unten bei den Erweiterungen.</p>
      </div>`;
  } else {
    document.getElementById("inhalt").innerHTML = `
      <div class="karte"><h2>Scratch ist noch nicht installiert</h2>
        <p>Die lokale Scratch-Oberfläche (TurboWarp) muss <b>einmalig mit Internet</b> aufs Board geladen werden:</p>
        <pre class="konsole">cd ~/roboterarm
./deploy/turbowarp_holen.sh</pre>
        <p class="klein">Danach läuft dieser Tab komplett offline. Bis dahin kannst du den Tab
           „Eigene Blöcke" nutzen — der kann fast dasselbe.</p>
      </div>`;
  }
}

// ------------------------------- 4) Python -------------------------------
const BEISPIELE = {
  "— Beispiel wählen —": "",
  "Winken": `from roboterarm import Arm
arm = Arm(); arm.home()
for _ in range(3):
    arm.basis(60); arm.basis(120)
arm.home()
print("gewunken!")`,
  "Greifer-Test": `from roboterarm import Arm
arm = Arm(); arm.home()
arm.greifer.auf()
arm.greifer.zu()
print("Greifer ok")`,
  "Quadrat (Koordinaten)": `from roboterarm import Arm
arm = Arm(); arm.home()
for (x, y) in [(120,-40),(120,40),(160,40),(160,-40)]:
    print(arm.gehe_zu(x, y, 60))
arm.home()`,
};
function renderPython() {
  const opt = Object.keys(BEISPIELE).map((k) => `<option>${k}</option>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Python-Editor</h2>
      <div class="reihe"><select id="bsp" onchange="codeBeispiel(this.value)">${opt}</select>
        <input type="text" id="prog_name" placeholder="Name" style="width:120px">
        <button onclick="codeSave()">💾</button></div>
      <textarea id="code" spellcheck="false" style="margin-top:10px"># Schreibe Python mit der roboterarm-API.
from roboterarm import Arm
arm = Arm()
arm.home()
print("bereit:", arm.alle_winkel())</textarea>
      <div class="reihe"><button class="primary" onclick="codeRun()">▶ Ausführen</button>
        <button class="gefahr" onclick="panik()">■ Stop</button></div>
    </div>
    <div class="karte"><h2>Ausgabe</h2><pre class="konsole" id="konsole">—</pre></div>`;
}
function codeBeispiel(k) { if (BEISPIELE[k]) document.getElementById("code").value = BEISPIELE[k]; }
async function codeSave() {
  const name = document.getElementById("prog_name").value.trim() || "programm";
  await API.post("/api/programm/speichern", { name, code: document.getElementById("code").value });
  flash("gespeichert: " + name);
}
async function codeRun() {
  ABBRUCH = false;
  await API.post("/api/code/run", { code: document.getElementById("code").value });
  stopPoll(); poll(codeTick, 400);
}
async function codeTick() {
  const r = await API.get("/api/code/ausgabe?seit=0");
  document.getElementById("konsole").textContent = (r.zeilen || []).join("\n") || "…";
  if (!r.laeuft) stopPoll();
}

// ----------------------------- ⚙ Kalibrieren -----------------------------
let KALIB_TEST = {};      // letzter Test-Reglerwert je Gelenk
// Test-Regler darf bewusst ÜBER 0–180 hinaus (für schief montierte Arme, z.B. Station 2/3).
// Der Servo selbst wird im Backend hart geschützt (PULS_HARTLIMIT_*), kann also nicht beschädigt werden.
const KAL_MIN = -90, KAL_MAX = 270;
async function renderKalib() {
  const k = await API.get("/api/kalib");
  KALIBDATA = k;
  const joints = Object.entries(k.gelenke).map(([n, g]) => kalibKarte(n, g)).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte modell-karte"><h2>Live-Modell — passt sich beim Kalibrieren an</h2>
      <div id="armmodell" class="armmodell"></div>
      <p class="klein" style="margin-top:6px">Bewege unten die Test-Regler — das Modell läuft mit.
      Stell die <b>Drehrichtung</b> so ein, dass das Modell zum echten Arm passt.</p>
    </div>
    <div class="karte"><h2>⚙ Kalibrieren — für Betreuer:innen</h2>
      <p class="klein">Pro Gelenk den <b>Test-Regler</b> bewegen (fährt den Servo <b>ohne Limit</b>).
      Endpunkte anfahren → <b>„= jetzt"</b> übernimmt den Wert als min bzw. max. Mitte = Home.
      Dreht es verkehrt herum → <b>Umkehren</b>. Pro Gelenk <b>Übernehmen</b>, am Ende <b>💾 Speichern</b>.</p>
      <p class="klein" style="color:var(--warn)">⚠ Fährt ein Servo in den Anschlag und summt: Test-Regler
      zurückziehen oder oben <b>■ NOT-AUS</b> (schaltet alle stromlos).</p>
    </div>
    ${joints}
    <div class="karte"><h2>Greifer offen / zu</h2>
      <div class="reihe">
        offen <input type="number" id="gr_auf" value="${k.greifer_auf}">
        <button onclick="kalibTest('greifer', document.getElementById('gr_auf').value)">testen</button>
        &nbsp; zu <input type="number" id="gr_zu" value="${k.greifer_zu}">
        <button onclick="kalibTest('greifer', document.getElementById('gr_zu').value)">testen</button>
        <button class="primary" onclick="kalibGreifer()">übernehmen</button>
      </div>
    </div>
    <div class="karte"><div class="reihe">
      <button class="primary gross" onclick="kalibSpeichern()">💾 Speichern (dauerhaft)</button>
      <span class="klein" id="kalib_msg"></span></div>
      <p class="klein">Speichert nach <code>~/.roboterarm/config.json</code> — gilt nach Neustart weiter.</p>
    </div>`;
  zeichneArm();
  fuelleSlider();
}
function kalibKarte(n, g) {
  return `<div class="karte"><h2>${n} — Kanal ${g.kanal}</h2>
    <div class="reihe">
      <label class="schalter" title="Drehrichtung umkehren">
        <input type="checkbox" ${g.invertiert ? "checked" : ""} onchange="kalibInvert('${n}', this.checked)">
        <span class="schieber"></span></label> Drehrichtung umkehren
    </div>
    <div class="gelenk" style="margin-top:12px">
      <label><span>Test-Regler (ohne Limit, auch über 0–180 hinaus)</span> <b id="kt_${n}">${Math.round(g.home)}°</b></label>
      <input type="range" min="${KAL_MIN}" max="${KAL_MAX}" value="${g.home}" oninput="kalibTestLive('${n}', this.value)">
    </div>
    <div class="reihe">
      min <input type="number" id="kmin_${n}" value="${g.min_winkel}">
      <button onclick="kalibCapture('${n}','kmin_${n}')">= jetzt</button>
      &nbsp; max <input type="number" id="kmax_${n}" value="${g.max_winkel}">
      <button onclick="kalibCapture('${n}','kmax_${n}')">= jetzt</button>
    </div>
    <div class="reihe">
      home <input type="number" id="khome_${n}" value="${g.home}">
      <button onclick="kalibCapture('${n}','khome_${n}')">= jetzt</button>
      &nbsp; offset <input type="number" id="koff_${n}" value="${g.offset}">
      <button class="primary" onclick="kalibUebernehmen('${n}')">übernehmen</button>
    </div></div>`;
}
let ktLast = {};
function kalibTestLive(n, val) {
  document.getElementById("kt_" + n).textContent = Math.round(val) + "°";
  KALIB_TEST[n] = Number(val);
  WINKEL[n] = Number(val);
  zeichneArm();                                   // Modell läuft beim Kalibrieren mit
  const now = Date.now(); if (now - (ktLast[n] || 0) < 80) return; ktLast[n] = now;
  API.post("/api/kalib/test", { name: n, winkel: Number(val) });
}
function kalibCapture(n, feldId) {
  const v = KALIB_TEST[n] != null ? KALIB_TEST[n] : Number(document.getElementById("kt_" + n).textContent);
  document.getElementById(feldId).value = Math.round(v);
}
async function kalibTest(name, winkel) { await API.post("/api/kalib/test", { name, winkel: Number(winkel) }); }
async function kalibInvert(n, an) {
  await API.post("/api/kalib/set", { name: n, invertiert: an });
  if (KALIBDATA.gelenke && KALIBDATA.gelenke[n]) KALIBDATA.gelenke[n].invertiert = an;
  zeichneArm();                                   // Modell dreht sofort mit
  if (KALIB_TEST[n] != null) API.post("/api/kalib/test", { name: n, winkel: KALIB_TEST[n] });
  kalibFlash(`${n}: Richtung ${an ? "umgekehrt" : "normal"}`);
}
async function kalibUebernehmen(n) {
  await API.post("/api/kalib/set", { name: n,
    min_winkel: Number(document.getElementById("kmin_" + n).value),
    max_winkel: Number(document.getElementById("kmax_" + n).value),
    home: Number(document.getElementById("khome_" + n).value),
    offset: Number(document.getElementById("koff_" + n).value) });
  kalibFlash(`${n}: übernommen`);
}
async function kalibGreifer() {
  await API.post("/api/kalib/greifer", {
    auf: Number(document.getElementById("gr_auf").value),
    zu: Number(document.getElementById("gr_zu").value) });
  kalibFlash("Greifer übernommen");
}
async function kalibSpeichern() {
  const r = await API.post("/api/kalib/speichern");
  kalibFlash(r.ok ? "💾 gespeichert: " + r.pfad : "Fehler beim Speichern");
}
function kalibFlash(t) { const m = document.getElementById("kalib_msg"); if (m) m.textContent = t; flash(t); }

// -------------------------------- Helfer --------------------------------
function flash(text) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = text; t.classList.add("an");
  clearTimeout(flash._t); flash._t = setTimeout(() => t.classList.remove("an"), 2800);
}
