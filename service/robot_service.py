#!/usr/bin/env python3
"""Lokaler Roboter-Dienst: REST-API + Weboberfläche + Code-Ausführung.

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 service/robot_service.py
    # Browser:  http://<board-ip>:8765/

Nur Python-Standardbibliothek (kein Flask) -> läuft ohne Zusatzinstallation auf
dem Board wie am Laptop. CORS ist offen, damit die Scratch-Extension (eigener
Origin) per fetch zugreifen kann.

REST-Überblick:
  Bewegung   POST /api/gelenk /greifer /home /bewege /tempo /gehe_zu
  Vision     GET  /api/vision/farben /vision/finde?ziel= /vision/alle?ziel=
  KI         POST /api/ki/aufnehmen /trainiere /reset /speichern /laden
             GET  /api/ki/status /erkenne /bewerte
  Posen      GET  /api/posen   POST /api/pose/speichern /pose/anfahren
  Aufnahme   POST /api/aufnahme/start /stop /wiedergabe
  Projekte   GET  /api/projekte /programme /programm?name=
             POST /api/projekt/waehle /programm/speichern
  Code       POST /api/code/run /code/stop   GET /api/code/ausgabe?seit=
  Kamera     GET  /api/kamera.img   /api/kamera/stream (MJPEG)
  Sim        POST /api/sim_szene /sim_objekte
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
sys.path.insert(0, ROOT)

from roboterarm import Arm                       # noqa: E402
from roboterarm import vision as vision_mod      # noqa: E402

arm = Arm()
sperre = threading.Lock()


# ------------------------------ Bild-Helfer ------------------------------

def _bmp(frame) -> bytes:
    h, w, _ = frame.shape
    pad = (-(w * 3)) % 4
    daten = bytearray()
    for y in range(h - 1, -1, -1):
        daten += frame[y].tobytes() + b"\x00" * pad
    info = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(daten), 2835, 2835, 0, 0)
    return b"BM" + struct.pack("<IHHI", 54 + len(daten), 0, 0, 54) + info + bytes(daten)


def frame_bild(frame):
    try:
        import cv2
        ok, buf = cv2.imencode(".jpg", frame)
        if ok:
            return bytes(buf), "image/jpeg"
    except Exception:
        pass
    return _bmp(frame), "image/bmp"


def status() -> dict:
    return {"backend": type(arm._ctrl.backend).__name__,
            "winkel": arm.alle_winkel(),
            "aktiv": dict(arm._ctrl.aktiv),
            "projekt": arm.cfg.projekt}


# Mime-Typen für die lokal ausgelieferte TurboWarp-Oberfläche (web/turbowarp/).
_MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
         ".css": "text/css", ".json": "application/json", ".map": "application/json",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif",
         ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
         ".wasm": "application/wasm", ".wav": "audio/wav", ".mp3": "audio/mpeg", ".hex": "application/octet-stream"}


def _mime(pfad: str) -> str:
    return _MIME.get(os.path.splitext(pfad)[1].lower(), "application/octet-stream")


TURBOWARP = os.path.join(WEB, "turbowarp")


# --------------------------- Code-Ausführ-Engine ---------------------------

class CodeRunner:
    def __init__(self):
        self.proc = None
        self.zeilen: list[str] = []
        self.lock = threading.Lock()

    def laeuft(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, code: str):
        self.stop()
        with self.lock:
            self.zeilen = []
        f = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
        f.write(code)
        f.close()
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        self.proc = subprocess.Popen([sys.executable, "-u", f.name], cwd=ROOT, env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        threading.Thread(target=self._lese, args=(self.proc,), daemon=True).start()

    def _lese(self, proc):
        for raw in proc.stdout:
            with self.lock:
                self.zeilen.append(raw.decode("utf-8", "replace").rstrip("\n"))
        rc = proc.poll()
        with self.lock:
            self.zeilen.append(f"— Programm beendet (Exit-Code {rc}) —")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(2)
            except Exception:
                self.proc.kill()

    def ausgabe(self, seit: int = 0):
        with self.lock:
            return self.zeilen[seit:], len(self.zeilen)


runner = CodeRunner()


# -------------------------------- Handler --------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ---- Antwort-Helfer (mit CORS) ----
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, obj, code=200):
        roh = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self._cors()
        self.end_headers()
        self.wfile.write(roh)

    def _bytes(self, roh, typ):
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(roh)))
        self._cors()
        self.end_headers()
        self.wfile.write(roh)

    def _datei(self, pfad, typ="text/html; charset=utf-8"):
        try:
            with open(pfad, "rb") as f:
                roh = f.read()
        except OSError:
            return self._json({"fehler": "nicht gefunden"}, 404)
        self._bytes(roh, typ)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # --------------------------------- GET ---------------------------------
    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        q = parse_qs(u.query)

        if p in ("/", "/index.html"):
            return self._datei(os.path.join(WEB, "index.html"))
        if p == "/roboterarm_extension.js":
            # Scratch/TurboWarp-Extension direkt vom Board laden (Ein-Klick, offline).
            return self._datei(os.path.join(ROOT, "scratch", "roboterarm_extension.js"),
                               "text/javascript")
        if p.startswith("/static/"):
            datei = os.path.normpath(os.path.join(WEB, p.lstrip("/")))
            if not datei.startswith(os.path.join(WEB, "static")):
                return self._json({"fehler": "verboten"}, 403)
            typ = "text/javascript" if datei.endswith(".js") else (
                "text/css" if datei.endswith(".css") else "application/octet-stream")
            return self._datei(datei, typ)
        if p == "/turbowarp" or p.startswith("/turbowarp/"):
            rel = p[len("/turbowarp"):].lstrip("/") or "index.html"
            datei = os.path.normpath(os.path.join(TURBOWARP, rel))
            if not (datei == TURBOWARP or datei.startswith(TURBOWARP + os.sep)):
                return self._json({"fehler": "verboten"}, 403)
            if os.path.isdir(datei):
                datei = os.path.join(datei, "index.html")
            return self._datei(datei, _mime(datei))
        if p == "/api/scratch/status":
            return self._json({"vorhanden": os.path.isfile(os.path.join(TURBOWARP, "index.html"))})

        if p == "/api/status":
            return self._json(status())
        if p == "/api/kalib":
            g = {n: {"kanal": x.kanal, "min_winkel": x.min_winkel, "max_winkel": x.max_winkel,
                     "home": x.home, "offset": x.offset, "invertiert": x.invertiert}
                 for n, x in arm.cfg.gelenke.items()}
            return self._json({"gelenke": g, "greifer_auf": arm.cfg.greifer_auf,
                               "greifer_zu": arm.cfg.greifer_zu})
        if p == "/api/kamera.img":
            with sperre:
                bild, typ = frame_bild(arm.kamera.frame())
            return self._bytes(bild, typ)
        if p == "/api/kamera/stream":
            return self._mjpeg()

        if p == "/api/vision/farben":
            return self._json({"farben": vision_mod.verfuegbare_farben(),
                               "eigene": list(getattr(arm.cfg, "farben", {}))})
        if p == "/api/vision/finde":
            ziel = (q.get("ziel") or ["rot"])[0]
            try:
                with sperre:
                    return self._json({"ziel": ziel, "treffer": vision_mod.finde(arm.kamera.frame(), ziel, arm.cfg)})
            except (KeyError, TypeError) as e:
                return self._json({"fehler": str(e)}, 400)
        if p == "/api/vision/alle":
            ziel = (q.get("ziel") or ["rot"])[0]
            try:
                with sperre:
                    return self._json({"ziel": ziel, "treffer": vision_mod.finde_alle(arm.kamera.frame(), ziel, arm.cfg)})
            except (KeyError, TypeError) as e:
                return self._json({"fehler": str(e)}, 400)

        if p == "/api/ki/status":
            m = arm.modell
            return self._json({"klassen": m.klassen, "verteilung": m.datensatz.zaehle(),
                               "trainiert": m._fit, "beispiele": len(m.datensatz)})
        if p == "/api/ki/erkenne":
            with sperre:
                return self._json(arm.erkenne())
        if p == "/api/ki/bewerte":
            with sperre:
                return self._json(arm.modell.bewerte())

        if p == "/api/posen":
            return self._json({"posen": arm.projekt.posen()})
        if p == "/api/projekte":
            from roboterarm.projekt import Projekt
            return self._json({"projekte": Projekt.liste(), "aktuell": arm.cfg.projekt})
        if p == "/api/programme":
            return self._json({"programme": arm.projekt.programme()})
        if p == "/api/programm":
            name = (q.get("name") or [""])[0]
            try:
                return self._json({"name": name, "code": arm.projekt.programm_laden(name)})
            except OSError:
                return self._json({"fehler": "unbekannt"}, 404)

        if p == "/api/code/ausgabe":
            seit = int((q.get("seit") or ["0"])[0])
            zeilen, gesamt = runner.ausgabe(seit)
            return self._json({"zeilen": zeilen, "gesamt": gesamt, "laeuft": runner.laeuft()})

        if p == "/api/sieht":
            ziel = (q.get("ziel") or [""])[0]
            with sperre:
                return self._json({"ziel": ziel, "sieht": arm.sieht(ziel)})

        return self._json({"fehler": "unbekannt", "pfad": p}, 404)

    # --------------------------------- POST ---------------------------------
    def do_POST(self):
        p = urlparse(self.path).path
        d = self._body()

        # ---- NOT-AUS: laufende Bewegung sofort abbrechen, dann ALLE Servos stromlos ----
        if p == "/api/panik":
            arm.not_aus()                       # bricht laufende Interpolation sofort ab (keine Sperre)
            runner.stop()                       # laufenden Python-Code beenden
            with sperre:
                for name in arm.cfg.gelenke:
                    arm.servo(name, False)      # jeden Kanal stromlos schalten
            return self._json(status())

        # Jede bewusste Bewegung hebt einen vorherigen NOT-AUS wieder auf.
        if p in ("/api/gelenk", "/api/bewege", "/api/greifer", "/api/home", "/api/gehe_zu",
                 "/api/tempo", "/api/pose/anfahren", "/api/aufnahme/wiedergabe"):
            arm.weiter()

        # ---- Bewegung ----
        if p == "/api/gelenk":
            if d.get("name") not in arm.cfg.gelenke:
                return self._json({"fehler": "unbekanntes Gelenk"}, 400)
            with sperre:
                arm._ctrl.setze(d["name"], float(d.get("winkel", 90)), speed=d.get("speed"))
            return self._json(status())
        if p == "/api/bewege":
            with sperre:
                arm.bewege(d["name"], float(d["winkel"]), d.get("speed"))
            return self._json(status())
        if p == "/api/greifer":
            with sperre:
                (arm.greifer.auf if d.get("aktion") == "auf" else arm.greifer.zu)()
            return self._json(status())
        if p == "/api/servo":
            if d.get("name") not in arm.cfg.gelenke:
                return self._json({"fehler": "unbekanntes Gelenk"}, 400)
            an = bool(d.get("an", True))
            if an:
                arm.weiter()                    # Einschalten hebt einen vorherigen NOT-AUS auf
            with sperre:
                arm.servo(d["name"], an)
            return self._json(status())

        # ---- Kalibrierung (grafisch in der Weboberfläche) ----
        if p == "/api/kalib/test":              # Servo OHNE Winkelgrenzen fahren (Endpunkte finden)
            if d.get("name") not in arm.cfg.gelenke:
                return self._json({"fehler": "unbekanntes Gelenk"}, 400)
            arm.weiter()
            with sperre:
                arm._ctrl.aktiv[d["name"]] = True
                arm._ctrl.setze(d["name"], float(d.get("winkel", 90)), sanft=False, grenzen=False)
            return self._json(status())
        if p == "/api/kalib/set":               # Grenzen/Home/Offset/Richtung übernehmen (live)
            name = d.get("name")
            if name not in arm.cfg.gelenke:
                return self._json({"fehler": "unbekanntes Gelenk"}, 400)
            g = arm.cfg.gelenke[name]
            for k in ("min_winkel", "max_winkel", "home", "offset"):
                if d.get(k) is not None:
                    setattr(g, k, float(d[k]))
            if "invertiert" in d:
                g.invertiert = bool(d["invertiert"])
            return self._json({"ok": True})
        if p == "/api/kalib/greifer":
            if d.get("auf") is not None:
                arm.cfg.greifer_auf = float(d["auf"])
            if d.get("zu") is not None:
                arm.cfg.greifer_zu = float(d["zu"])
            return self._json({"ok": True})
        if p == "/api/kalib/speichern":
            from roboterarm.config import speichere_config
            pfad = speichere_config(arm.cfg)
            return self._json({"ok": True, "pfad": pfad})
        if p == "/api/home":
            with sperre:
                arm.home()
            return self._json(status())
        if p == "/api/tempo":
            arm.tempo(float(d.get("grad", 3)))
            return self._json({"ok": True})
        if p == "/api/gehe_zu":
            with sperre:
                return self._json({"winkel": arm.gehe_zu(float(d["x"]), float(d["y"]), float(d["z"]))})

        # ---- KI ----
        if p == "/api/ki/aufnehmen":
            with sperre:
                arm.modell.aufnehmen(d.get("label", "Klasse"), arm.kamera.frame())
            return self._json({"beispiele": len(arm.modell.datensatz), "verteilung": arm.modell.datensatz.zaehle()})
        if p == "/api/ki/trainiere":
            with sperre:
                return self._json(arm.modell.trainiere())
        if p == "/api/ki/reset":
            from roboterarm.ml import Modell
            arm._modell = Modell()
            return self._json({"ok": True})
        if p == "/api/ki/speichern":
            ordner = arm.projekt.modell_pfad(d.get("name", "standard"))
            with sperre:
                arm.modell.speichere(ordner)
            return self._json({"ok": True, "ordner": ordner})
        if p == "/api/ki/laden":
            from roboterarm.ml import Modell
            ordner = arm.projekt.modell_pfad(d.get("name", "standard"))
            try:
                arm._modell = Modell.lade(ordner)
                return self._json({"ok": True, "klassen": arm._modell.klassen})
            except Exception as e:
                return self._json({"fehler": str(e)}, 400)

        # ---- Posen ----
        if p == "/api/pose/speichern":
            arm.pose_speichern(d["name"])
            return self._json({"ok": True, "posen": arm.projekt.posen()})
        if p == "/api/pose/anfahren":
            try:
                with sperre:
                    arm.pose_anfahren(d["name"])
                return self._json(status())
            except KeyError as e:
                return self._json({"fehler": str(e)}, 404)
        if p == "/api/pose/loeschen":
            arm.projekt.pose_loeschen(d.get("name", ""))
            return self._json({"ok": True, "posen": arm.projekt.posen()})

        # ---- Aufnahme ----
        if p == "/api/aufnahme/start":
            arm.aufnahme_start()
            return self._json({"ok": True})
        if p == "/api/aufnahme/stop":
            self._letzte_aufnahme = arm.aufnahme_stop()
            Handler.letzte_aufnahme = self._letzte_aufnahme
            return self._json({"schritte": self._letzte_aufnahme})
        if p == "/api/aufnahme/wiedergabe":
            with sperre:
                arm.wiedergabe(getattr(Handler, "letzte_aufnahme", []))
            return self._json(status())

        # ---- Projekte / Programme ----
        if p == "/api/projekt/waehle":
            arm.cfg.projekt = d.get("name", "standard")
            arm._projekt = None
            from roboterarm.projekt import Projekt
            return self._json({"aktuell": arm.cfg.projekt, "projekte": Projekt.liste()})
        if p == "/api/programm/speichern":
            arm.projekt.programm_speichern(d["name"], d.get("code", ""))
            return self._json({"ok": True, "programme": arm.projekt.programme()})

        # ---- Code-Ausführung ----
        if p == "/api/code/run":
            runner.start(d.get("code", ""))
            return self._json({"ok": True})
        if p == "/api/code/stop":
            runner.stop()
            return self._json({"ok": True})

        # ---- High-Level-Verhalten (für Scratch & Blöcke) ----
        if p == "/api/ki/lerne":
            with sperre:
                return self._json(arm.lerne(d.get("label", "Klasse"), int(d.get("anzahl", 10))))
        if p == "/api/verhalten/suche":
            with sperre:
                return self._json({"gefunden": arm.suche(d.get("ziel"))})
        if p == "/api/verhalten/zentriere":
            with sperre:
                return self._json({"ok": arm.zentriere_auf(d.get("ziel"))})
        if p == "/api/verhalten/hole":
            with sperre:
                return self._json({"ok": arm.hole(d.get("ziel"))})
        if p == "/api/verhalten/sortiere":
            with sperre:
                return self._json({"anzahl": arm.sortiere(d.get("zuordnung", {}))})

        # ---- Simulation ----
        if p == "/api/sim_szene":
            if hasattr(arm.kamera, "sim_szene"):
                arm.kamera.sim_szene(ball_welt=d.get("ball_welt"), fov_halb=d.get("fov_halb"),
                                     hat_ball=d.get("hat_ball"))
                return self._json({"ok": True})
            return self._json({"ok": False, "grund": "keine Sim-Kamera"})
        if p == "/api/sim_objekte":
            if hasattr(arm.kamera, "sim_objekte"):
                arm.kamera.sim_objekte(d.get("objekte", []))
                return self._json({"ok": True})
            return self._json({"ok": False, "grund": "keine Sim-Kamera"})

        return self._json({"fehler": "unbekannt", "pfad": p}, 404)

    # ---- MJPEG-Stream (vor allem für Hardware/JPEG) ----
    def _mjpeg(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self._cors()
        self.end_headers()
        try:
            while True:
                with sperre:
                    bild, typ = frame_bild(arm.kamera.frame())
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(f"Content-Type: {typ}\r\n".encode())
                self.wfile.write(f"Content-Length: {len(bild)}\r\n\r\n".encode())
                self.wfile.write(bild)
                self.wfile.write(b"\r\n")
                time.sleep(0.1)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def main():
    p = argparse.ArgumentParser(description="roboterarm Web-Dienst")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"roboterarm-Dienst: http://{args.host}:{args.port}/   (Backend: {status()['backend']})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        runner.stop()
        srv.server_close()
        arm.schliessen()


if __name__ == "__main__":
    main()
