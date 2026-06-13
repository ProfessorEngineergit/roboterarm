/* roboterarm — Scratch-3-Extension
 *
 * Spricht den lokalen Dienst (service/robot_service.py) per HTTP an. Damit
 * steuern Kinder denselben Arm wie über Python — nur in Blöcken.
 *
 * Laden:  TurboWarp (turbowarp.org/editor) → Erweiterungen → „Erweiterung
 *         hinzufügen" → „Eigene Erweiterung" → diese Datei wählen.
 *         (TurboWarp Desktop läuft offline.) Details: scratch/README.md
 *
 * Es werden keine eigenen Block-*Sprachen* gebaut — nur eine Handvoll Befehls-
 * und Fühler-Blöcke, die die veröffentlichte roboterarm-API aufrufen.
 */
(function (Scratch) {
  "use strict";

  const standardServer = () =>
    (typeof location !== "undefined" && location.hostname && location.hostname !== "")
      ? `http://${location.hostname}:8765`
      : "http://localhost:8765";
  let server = standardServer();

  async function post(pfad, body) {
    try {
      const r = await fetch(server + pfad, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      return await r.json();
    } catch (e) { return {}; }
  }
  async function get(pfad) {
    try { return await (await fetch(server + pfad)).json(); } catch (e) { return {}; }
  }

  const T = Scratch.ArgumentType;
  const B = Scratch.BlockType;

  class Roboterarm {
    getInfo() {
      return {
        id: "roboterarm",
        name: "Roboterarm",
        color1: "#2563eb",
        color2: "#1d4ed8",
        blocks: [
          { opcode: "setServer", blockType: B.COMMAND, text: "verbinde mit Server [URL]",
            arguments: { URL: { type: T.STRING, defaultValue: server } } },
          "---",
          { opcode: "home", blockType: B.COMMAND, text: "Grundstellung" },
          { opcode: "gelenk", blockType: B.COMMAND, text: "[NAME] auf [WINKEL] Grad",
            arguments: { NAME: { type: T.STRING, menu: "gelenke", defaultValue: "basis" },
                         WINKEL: { type: T.NUMBER, defaultValue: 90 } } },
          { opcode: "greifer", blockType: B.COMMAND, text: "Greifer [AKTION]",
            arguments: { AKTION: { type: T.STRING, menu: "aktion", defaultValue: "auf" } } },
          { opcode: "tempo", blockType: B.COMMAND, text: "Tempo [GRAD]",
            arguments: { GRAD: { type: T.NUMBER, defaultValue: 3 } } },
          { opcode: "geheZu", blockType: B.COMMAND, text: "gehe zu x [X] y [Y] z [Z]",
            arguments: { X: { type: T.NUMBER, defaultValue: 120 }, Y: { type: T.NUMBER, defaultValue: 0 },
                         Z: { type: T.NUMBER, defaultValue: 60 } } },
          "---",
          { opcode: "suche", blockType: B.COMMAND, text: "drehe bis [ZIEL] sichtbar",
            arguments: { ZIEL: { type: T.STRING, defaultValue: "rot" } } },
          { opcode: "zentriere", blockType: B.COMMAND, text: "zentriere auf [ZIEL]",
            arguments: { ZIEL: { type: T.STRING, defaultValue: "rot" } } },
          { opcode: "hole", blockType: B.COMMAND, text: "hole [ZIEL]",
            arguments: { ZIEL: { type: T.STRING, defaultValue: "rot" } } },
          { opcode: "sieht", blockType: B.BOOLEAN, text: "sehe ich [ZIEL]?",
            arguments: { ZIEL: { type: T.STRING, defaultValue: "rot" } } },
          "---",
          { opcode: "lerne", blockType: B.COMMAND, text: "lerne [LABEL] mit [ANZAHL] Bildern",
            arguments: { LABEL: { type: T.STRING, defaultValue: "Ball" }, ANZAHL: { type: T.NUMBER, defaultValue: 15 } } },
          { opcode: "trainiere", blockType: B.COMMAND, text: "trainiere KI" },
          { opcode: "erkanntes", blockType: B.REPORTER, text: "erkanntes Objekt" },
        ],
        menus: {
          gelenke: { items: ["basis", "schulter", "ellbogen"] },
          aktion: { items: ["auf", "zu"] },
        },
      };
    }

    setServer(a) { server = String(a.URL); }
    home() { return post("/api/home"); }
    gelenk(a) { return post("/api/gelenk", { name: a.NAME, winkel: Number(a.WINKEL) }); }
    greifer(a) { return post("/api/greifer", { aktion: a.AKTION }); }
    tempo(a) { return post("/api/tempo", { grad: Number(a.GRAD) }); }
    geheZu(a) { return post("/api/gehe_zu", { x: Number(a.X), y: Number(a.Y), z: Number(a.Z) }); }
    suche(a) { return post("/api/verhalten/suche", { ziel: a.ZIEL }); }
    zentriere(a) { return post("/api/verhalten/zentriere", { ziel: a.ZIEL }); }
    hole(a) { return post("/api/verhalten/hole", { ziel: a.ZIEL }); }
    async sieht(a) { return Boolean((await get("/api/sieht?ziel=" + encodeURIComponent(a.ZIEL))).sieht); }
    lerne(a) { return post("/api/ki/lerne", { label: a.LABEL, anzahl: Number(a.ANZAHL) }); }
    trainiere() { return post("/api/ki/trainiere"); }
    async erkanntes() { return (await get("/api/ki/erkenne")).label || ""; }
  }

  Scratch.extensions.register(new Roboterarm());
})(Scratch);
