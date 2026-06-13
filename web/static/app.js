/* roboterarm — Weboberfläche (vanilla JS, offline, ohne Abhängigkeiten) */

const API = {
  async get(p) { const r = await fetch(p); return r.json(); },
  async post(p, b) { const r = await fetch(p, { method: "POST", body: JSON.stringify(b || {}) }); return r.json(); },
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let FARBEN = [];
let tab = "manuell";
let pollers = [];
let kiKlassen = [];
let simObjekte = [{ welt: 120, farbe: "orange", radius: 18 }];

function stopPoll() { pollers.forEach(clearInterval); pollers = []; }
function poll(fn, ms) { fn(); pollers.push(setInterval(fn, ms)); }

// ------------------------------- Beispiele -------------------------------
const BEISPIELE = {
  "— Beispiel wählen —": "",
  "Winken": `from roboterarm import Arm
from roboterarm.verhalten import winken
arm = Arm(); arm.home()
winken(arm)
print("gewunken!")`,
  "Objekt finden & aufheben": `from roboterarm import Arm
arm = Arm(); arm.home()
ziel = "orange"
if arm.suche(ziel):
    arm.zentriere_auf(ziel)
    arm.aufheben(); arm.ablegen()
    print("aufgehoben:", ziel)
else:
    print("nichts gefunden")`,
  "Nach Farbe sortieren": `from roboterarm import Arm
arm = Arm(); arm.home()
arm.sortiere({"rot": 40, "blau": 140})
print("sortiert")`,
  "KI: erkennen": `from roboterarm import Arm
arm = Arm()
print(arm.erkenne())`,
  "Koordinaten (IK)": `from roboterarm import Arm
arm = Arm(); arm.home()
print(arm.gehe_zu(120, 0, 60))`,
};

// --------------------------------- Start ---------------------------------
window.addEventListener("DOMContentLoaded", init);

async function init() {
  document.body.innerHTML = `
    <header>
      <h1>🤖 roboterarm</h1>
      <span class="backend" id="backend">…</span>
      <nav id="nav"></nav>
    </header>
    <main>
      <div>
        <div class="karte">
          <h2>Kamera</h2>
          <img class="cam" id="cam" alt="Kamerabild">
          <div id="simbox"></div>
        </div>
        <div class="karte"><h2>Status</h2><div id="status" class="klein">…</div></div>
      </div>
      <div id="inhalt"></div>
    </main>`;

  const navs = ["manuell", "vision", "ki", "code", "aufnahme"];
  const titel = { manuell: "Manuell", vision: "Vision", ki: "KI-Studio", code: "Code", aufnahme: "Aufnahme & Posen" };
  document.getElementById("nav").innerHTML = navs.map(
    (n) => `<button id="nav_${n}" onclick="zeigeTab('${n}')">${titel[n]}</button>`).join("");

  try { FARBEN = (await API.get("/api/vision/farben")).farben || []; } catch (e) { FARBEN = []; }
  renderSim();
  setInterval(() => { document.getElementById("cam").src = "/api/kamera.img?t=" + Date.now(); }, 160);
  setInterval(refreshStatus, 1000);
  zeigeTab("manuell");
}

async function refreshStatus() {
  try {
    const s = await API.get("/api/status");
    document.getElementById("backend").textContent = s.backend + " · " + s.projekt;
    document.getElementById("status").innerHTML = Object.entries(s.winkel)
      .map(([k, v]) => `${k}: <b>${Math.round(v)}°</b>`).join(" · ");
  } catch (e) {}
}

function zeigeTab(name) {
  tab = name; stopPoll();
  document.querySelectorAll("#nav button").forEach((b) => b.classList.remove("aktiv"));
  document.getElementById("nav_" + name).classList.add("aktiv");
  ({ manuell: renderManuell, vision: renderVision, ki: renderKI, code: renderCode, aufnahme: renderAufnahme }[name])();
}

// ------------------------------ Simulation ------------------------------
function renderSim() {
  const opt = FARBEN.map((f) => `<option>${f}</option>`).join("");
  document.getElementById("simbox").innerHTML = `
    <div class="reihe klein" style="margin-top:8px">Sim-Objekt:
      <select id="sim_farbe">${opt}</select>
      <input type="number" id="sim_welt" value="120" title="Azimut in Grad" style="width:64px">
      <button onclick="simAdd()">+ legen</button>
      <button onclick="simClear()">leeren</button>
    </div>`;
}
async function simAdd() {
  simObjekte.push({ welt: Number(document.getElementById("sim_welt").value), farbe: document.getElementById("sim_farbe").value, radius: 18 });
  await API.post("/api/sim_objekte", { objekte: simObjekte });
}
async function simClear() { simObjekte = []; await API.post("/api/sim_objekte", { objekte: [] }); }

// ------------------------------- Manuell -------------------------------
async function renderManuell() {
  const s = await API.get("/api/status");
  const regler = Object.entries(s.winkel).map(([n, w]) => `
    <div class="gelenk"><label>${n} <b id="v_${n}">${Math.round(w)}°</b></label>
      <input type="range" min="0" max="180" value="${w}" oninput="mSet('${n}', this.value)"></div>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Gelenke</h2>${regler}
      <div class="reihe">
        <button onclick="API.post('/api/home').then(refreshManuell)">🏠 Home</button>
        <button onclick="API.post('/api/greifer',{aktion:'auf'})">✋ Greifer auf</button>
        <button onclick="API.post('/api/greifer',{aktion:'zu'})">✊ Greifer zu</button>
      </div>
      <div class="reihe">Tempo <input type="range" min="0" max="15" value="3" oninput="API.post('/api/tempo',{grad:Number(this.value)})"></div>
    </div>
    <div class="karte"><h2>Koordinaten (inverse Kinematik)</h2>
      <div class="reihe">
        x <input type="number" id="gx" value="120"> y <input type="number" id="gy" value="0"> z <input type="number" id="gz" value="60">
        <button class="primary" onclick="mGehe()">gehe_zu</button>
        <span id="gehe_out" class="klein"></span>
      </div>
    </div>`;
}
async function refreshManuell() { if (tab === "manuell") renderManuell(); }
let mLast = 0;
async function mSet(name, val) {
  document.getElementById("v_" + name).textContent = Math.round(val) + "°";
  const now = Date.now(); if (now - mLast < 70) return; mLast = now;
  await API.post("/api/gelenk", { name, winkel: Number(val) });
}
async function mGehe() {
  const r = await API.post("/api/gehe_zu", {
    x: Number(gx.value), y: Number(gy.value), z: Number(gz.value) });
  document.getElementById("gehe_out").textContent = JSON.stringify(r.winkel);
}

// -------------------------------- Vision --------------------------------
function renderVision() {
  const opt = FARBEN.map((f) => `<option>${f}</option>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Farb-/Objekterkennung</h2>
      <div class="reihe">Ziel: <select id="v_ziel" onchange="">${opt}</select></div>
      <div class="pred" id="v_pred">—</div>
      <div class="posbar"><i id="v_bar" style="left:50%"></i></div>
      <div class="klein" id="v_info" style="margin-top:8px"></div>
    </div>
    <div class="karte"><h2>Alle Treffer</h2><div id="v_alle" class="klein">…</div></div>`;
  poll(visionTick, 300);
}
async function visionTick() {
  const ziel = document.getElementById("v_ziel").value;
  const r = await API.get("/api/vision/finde?ziel=" + encodeURIComponent(ziel));
  const t = r.treffer;
  document.getElementById("v_pred").textContent = t ? `${ziel} sichtbar` : `${ziel}: —`;
  document.getElementById("v_pred").style.color = t ? "var(--gut)" : "var(--muted)";
  document.getElementById("v_bar").style.left = (t ? (t.x + 1) * 50 : 50) + "%";
  document.getElementById("v_info").textContent = t
    ? `x=${t.x.toFixed(2)}  y=${t.y.toFixed(2)}  Größe=${(t.groesse * 100).toFixed(1)}%` : "nicht im Bild";
  const a = await API.get("/api/vision/alle?ziel=" + encodeURIComponent(ziel));
  document.getElementById("v_alle").textContent = (a.treffer || []).length
    ? (a.treffer.map((o, i) => `#${i + 1} x=${o.x.toFixed(2)} größe=${(o.groesse * 100).toFixed(1)}%`).join("\n")) : "keine";
}

// ------------------------------- KI-Studio -------------------------------
async function renderKI() {
  const st = await API.get("/api/ki/status");
  const set = new Set([...(st.klassen || []), ...kiKlassen]);
  kiKlassen = [...set];
  const verteilung = st.verteilung || {};
  const zeilen = kiKlassen.map((k) => `
    <div class="klassenzeile"><span class="name">${esc(k)}</span>
      <span class="badge">${verteilung[k] || 0} Bilder</span>
      <button onclick="kiCapture('${esc(k)}',5)">📸 ×5</button></div>`).join("");
  const chips = ["Ball", "Tasse", "Hand", "Würfel", "leer"].map(
    (c) => `<span class="chip" onclick="kiQuickAdd('${c}')">+ ${c}</span>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Klassen</h2>
      <div class="klassenliste" id="ki_liste">${zeilen || '<span class="klein">noch keine Klasse</span>'}</div>
      <div class="reihe"><input type="text" id="ki_neu" placeholder="neue Klasse"><button onclick="kiAdd()">+ hinzufügen</button></div>
      <div class="chips" style="margin-top:8px">${chips}</div>
      <div class="reihe">
        <button class="primary" onclick="kiTrain()">🧠 Trainieren</button>
        <button onclick="kiBewerte()">📊 Bewerten</button>
        <button onclick="API.post('/api/ki/speichern',{}).then(()=>flash('gespeichert'))">💾 Speichern</button>
        <button onclick="API.post('/api/ki/laden',{}).then(renderKI)">📂 Laden</button>
        <button class="gefahr" onclick="API.post('/api/ki/reset',{}).then(()=>{kiKlassen=[];renderKI();})">Reset</button>
      </div>
      <div class="klein" id="ki_msg"></div>
    </div>
    <div class="karte"><h2>Live-Erkennung</h2><div class="pred" id="ki_pred">—</div><div class="klein" id="ki_proba"></div></div>
    <div class="karte" id="ki_bewertung" style="display:none"><h2>Bewertung (Confusion-Matrix)</h2><div id="ki_conf"></div></div>`;
  poll(kiTick, 700);
}
function kiAdd() { const v = document.getElementById("ki_neu").value.trim(); if (v && !kiKlassen.includes(v)) { kiKlassen.push(v); renderKI(); } }
function kiQuickAdd(v) { if (!kiKlassen.includes(v)) kiKlassen.push(v); renderKI(); }
async function kiCapture(label, n) {
  for (let i = 0; i < n; i++) await API.post("/api/ki/aufnehmen", { label });
  flash(`${n} Bilder für „${label}"`); renderKI();
}
async function kiTrain() { const r = await API.post("/api/ki/trainiere"); flash("trainiert: " + JSON.stringify(r.klassen || r.fehler)); }
async function kiTick() {
  const d = await API.get("/api/ki/erkenne");
  document.getElementById("ki_pred").textContent = d.label ? `${d.label} (${d.confidence})` : "—";
  document.getElementById("ki_proba").textContent = Object.entries(d.proba || {}).map(([k, v]) => `${k}:${v}`).join("  ");
}
async function kiBewerte() {
  const b = await API.get("/api/ki/bewerte");
  const box = document.getElementById("ki_bewertung");
  if (b.fehler) { box.style.display = "block"; document.getElementById("ki_conf").textContent = b.fehler; return; }
  const ks = b.klassen;
  const kopf = `<tr><th>echt ＼ erkannt</th>${ks.map((k) => `<th>${esc(k)}</th>`).join("")}</tr>`;
  const zeilen = ks.map((a) => `<tr><th>${esc(a)}</th>${ks.map((p) =>
    `<td class="${a === p ? "diag" : ""}">${b.confusion[a][p]}</td>`).join("")}</tr>`).join("");
  box.style.display = "block";
  document.getElementById("ki_conf").innerHTML =
    `<p class="klein">Genauigkeit: <b>${(b.genauigkeit * 100).toFixed(0)}%</b> (${b.n_test} Testbilder)</p><table>${kopf}${zeilen}</table>`;
}

// --------------------------------- Code ---------------------------------
function renderCode() {
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
        <button class="gefahr" onclick="codeStop()">■ Stop</button></div>
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
  await API.post("/api/code/run", { code: document.getElementById("code").value });
  stopPoll(); poll(codeTick, 400);
}
async function codeStop() { await API.post("/api/code/stop"); }
async function codeTick() {
  const r = await API.get("/api/code/ausgabe?seit=0");
  document.getElementById("konsole").textContent = (r.zeilen || []).join("\n") || "…";
  if (!r.laeuft) { stopPoll(); }
}

// ----------------------------- Aufnahme/Posen -----------------------------
async function renderAufnahme() {
  const p = await API.get("/api/posen");
  const posen = Object.entries(p.posen || {}).map(([n, w]) =>
    `<div class="klassenzeile"><span class="name">${esc(n)}</span>
       <span class="badge">${Object.entries(w).map(([k, v]) => k[0] + Math.round(v)).join(" ")}</span>
       <button onclick="poseGo('${esc(n)}')">anfahren</button></div>`).join("");
  document.getElementById("inhalt").innerHTML = `
    <div class="karte"><h2>Bewegung aufnehmen</h2>
      <div class="reihe">
        <button onclick="API.post('/api/aufnahme/start').then(()=>flash('Aufnahme läuft – jetzt bewegen'))">⏺ Start</button>
        <button onclick="API.post('/api/aufnahme/stop').then(r=>flash(r.schritte.length+' Schritte'))">⏹ Stop</button>
        <button class="primary" onclick="API.post('/api/aufnahme/wiedergabe')">▶ Wiedergabe</button>
      </div>
      <p class="klein">Start → im Tab „Manuell" bewegen → Stop → Wiedergabe spielt es ab.</p>
    </div>
    <div class="karte"><h2>Posen</h2>
      <div class="reihe"><input type="text" id="pose_name" placeholder="Posenname"><button onclick="poseSave()">Pose speichern</button></div>
      <div class="klassenliste" style="margin-top:10px">${posen || '<span class="klein">keine Posen</span>'}</div>
    </div>`;
}
async function poseSave() {
  const name = document.getElementById("pose_name").value.trim(); if (!name) return;
  await API.post("/api/pose/speichern", { name }); renderAufnahme();
}
async function poseGo(name) { await API.post("/api/pose/anfahren", { name }); }

// -------------------------------- Helfer --------------------------------
function flash(text) {
  const m = document.getElementById("ki_msg") || document.getElementById("status");
  if (m) { m.textContent = text; setTimeout(() => { if (m.id === "ki_msg") m.textContent = ""; }, 2500); }
}
