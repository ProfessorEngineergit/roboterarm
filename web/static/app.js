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

function stopPoll() { pollers.forEach(clearInterval); pollers = []; }
function poll(fn, ms) { fn(); pollers.push(setInterval(fn, ms)); }

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

  const navs = ["regler", "bloecke", "scratch", "python"];
  const titel = { regler: "🎚 Regler", bloecke: "🧩 Eigene Blöcke", scratch: "🐱 Scratch", python: "🐍 Python" };
  document.getElementById("nav").innerHTML = navs.map(
    (n) => `<button id="nav_${n}" onclick="zeigeTab('${n}')">${titel[n]}</button>`).join("");

  setInterval(refreshStatus, 1000);
  refreshStatus();
  zeigeTab("regler");
}

async function refreshStatus() {
  try {
    const s = await API.get("/api/status");
    document.getElementById("backend").textContent = s.backend + " · " + s.projekt;
    document.getElementById("statusbar").innerHTML = Object.entries(s.winkel)
      .map(([k, v]) => `<span class="stat">${k} <b>${Math.round(v)}°</b></span>`).join("");
  } catch (e) {}
}

function zeigeTab(name) {
  tab = name; stopPoll();
  document.querySelectorAll("#nav button").forEach((b) => b.classList.remove("aktiv"));
  document.getElementById("nav_" + name).classList.add("aktiv");
  ({ regler: renderRegler, bloecke: renderBloecke, scratch: renderScratch, python: renderPython }[name])();
}

// ------------------------------- NOT-AUS -------------------------------
async function panik() {
  ABBRUCH = true;
  try { await API.post("/api/panik"); } catch (e) {}
  const b = document.getElementById("notaus");
  if (b) { b.classList.add("blink"); setTimeout(() => b.classList.remove("blink"), 1500); }
  flash("⏹ NOT-AUS — alles gestoppt. Bewege etwas, um weiterzumachen.");
}

// ------------------------------- 1) Regler -------------------------------
async function renderRegler() {
  const s = await API.get("/api/status");
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
        <button onclick="API.post('/api/home').then(refreshRegler)">🏠 Grundstellung</button>
        <button onclick="API.post('/api/greifer',{aktion:'auf'})">✋ Greifer auf</button>
        <button onclick="API.post('/api/greifer',{aktion:'zu'})">✊ Greifer zu</button>
      </div>
      <div class="reihe">Tempo <input type="range" min="0" max="15" value="3" oninput="API.post('/api/tempo',{grad:Number(this.value)})"></div>
    </div>
    <div class="karte"><h2>Koordinaten (für Fortgeschrittene)</h2>
      <div class="reihe">
        x <input type="number" id="gx" value="120"> y <input type="number" id="gy" value="0"> z <input type="number" id="gz" value="60">
        <button class="primary" onclick="rGehe()">gehe zu</button>
        <span id="gehe_out" class="klein"></span>
      </div>
    </div>`;
}
async function refreshRegler() { if (tab === "regler") renderRegler(); }
async function servoSchalt(name, an) {
  await API.post("/api/servo", { name, an });
  const r = document.getElementById("r_" + name);
  if (r) r.disabled = !an;
  flash(an ? `${name}: Servo an` : `${name}: Servo aus (locker)`);
}
let rLast = 0;
async function rSet(name, val) {
  document.getElementById("v_" + name).textContent = Math.round(val) + "°";
  const now = Date.now(); if (now - rLast < 70) return; rLast = now;
  await API.post("/api/gelenk", { name, winkel: Number(val) });
}
async function rGehe() {
  const r = await API.post("/api/gehe_zu", { x: Number(gx.value), y: Number(gy.value), z: Number(gz.value) });
  document.getElementById("gehe_out").textContent = JSON.stringify(r.winkel || r.fehler);
}

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

// -------------------------------- Helfer --------------------------------
function flash(text) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = text; t.classList.add("an");
  clearTimeout(flash._t); flash._t = setTimeout(() => t.classList.remove("an"), 2800);
}
