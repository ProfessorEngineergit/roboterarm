#!/usr/bin/env python3
"""Dirigent — steuert mehrere Roboterarme gleichzeitig für eine Show.

Schickt jeden Choreografie-Schritt PARALLEL an alle Arme (per HTTP-API des
robot_service). Nur Python-Standardbibliothek -> läuft auf dem Board wie auf
dem Laptop/Mac, ohne Zusatzinstallation.

    python3 show/dirigent.py show/tanz_demo.json
    python3 show/dirigent.py show/tanz_demo.json --arme 10.42.0.11 10.42.0.12
    python3 show/dirigent.py show/tanz_demo.json --wiederhole 3

Abbruch: Strg+C  -> löst bei ALLEN Armen sofort NOT-AUS (/api/panik) aus.

Choreografie-Format (JSON), siehe show/tanz_demo.json:
  {
    "name":  "...",
    "arme":  ["roboterarm-01.local", "roboterarm-02.local", "roboterarm-03.local"],
    "tempo": 4,                      # Grad pro Schritt (größer = schneller/ruckiger)
    "schritte": [
       {"home": true,            "warte": 1.0},
       {"gelenk": "basis", "winkel": 45, "warte": 0.6},
       {"greifer": "auf",        "warte": 0.4},
       {"pose": "winken",        "warte": 1.0},
       {"tempo": 8},
       {"warte": 0.5},
       {"per_arm": {              # einzelne Arme unterschiedlich (echte Choreo)
           "roboterarm-01.local": {"gelenk": "schulter", "winkel": 60},
           "roboterarm-02.local": {"gelenk": "schulter", "winkel": 120}
        }, "warte": 0.8}
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import URLError


def adresse(a: str) -> str:
    """'roboterarm-01.local' oder '10.42.0.11' -> 'http://.../...:8765'."""
    a = a.strip()
    if not a.startswith("http"):
        a = "http://" + a
    if a.count(":") < 2:                # noch kein Port angegeben
        a = a + ":8765"
    return a


def sende(basis: str, pfad: str, daten: dict | None = None, timeout: float = 4.0):
    """Ein POST an einen Arm. Fehler werden gemeldet, brechen die Show aber nicht ab."""
    url = basis + pfad
    roh = json.dumps(daten or {}).encode()
    req = Request(url, data=roh, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as r:
            r.read()
        return True
    except (URLError, OSError) as e:
        print(f"   ⚠️  {basis} nicht erreichbar ({e})", file=sys.stderr)
        return False


def schritt_zu_befehl(s: dict) -> tuple[str, dict] | None:
    """Macht aus einem Schritt einen (pfad, body) für die API. None = reine Pause."""
    if s.get("home"):
        return "/api/home", {}
    if "gelenk" in s:
        b = {"name": s["gelenk"], "winkel": float(s["winkel"])}
        if "speed" in s:
            b["speed"] = s["speed"]
        return "/api/gelenk", b
    if "greifer" in s:
        return "/api/greifer", {"aktion": s["greifer"]}
    if "pose" in s:
        return "/api/pose/anfahren", {"name": s["pose"]}
    if "tempo" in s:
        return "/api/tempo", {"grad": float(s["tempo"])}
    return None                          # nur "warte"


def fuehre_aus(arme: list[str], choreo: dict, wiederhole: int, tempo: float | None):
    schritte = choreo.get("schritte", [])
    pool = ThreadPoolExecutor(max_workers=max(1, len(arme)))

    def an_alle(pfad: str, body_fn):
        """body_fn(arm) -> dict; an alle Arme parallel schicken."""
        list(pool.map(lambda a: sende(a, pfad, body_fn(a)), arme))

    # Tempo einmal global setzen (CLI schlägt JSON, JSON schlägt Default)
    t = tempo if tempo is not None else choreo.get("tempo")
    if t is not None:
        an_alle("/api/tempo", lambda a: {"grad": float(t)})

    name = choreo.get('name', 'Tanz')
    print(f"🎬  Show: {name} — {len(arme)} Arme, {len(schritte)} Schritte, {wiederhole}x")
    for runde in range(1, wiederhole + 1):
        if wiederhole > 1:
            print(f"— Durchlauf {runde}/{wiederhole} —")
        for i, s in enumerate(schritte, 1):
            per = s.get("per_arm")
            if per:                       # jeder Arm sein eigener Befehl
                def einzeln(a):
                    sub = per.get(a)
                    if not sub:
                        return
                    bf = schritt_zu_befehl(sub)
                    if bf:
                        sende(a, bf[0], bf[1])
                list(pool.map(einzeln, arme))
                print(f"  [{i:>2}] per-Arm")
            else:
                bf = schritt_zu_befehl(s)
                if bf:
                    an_alle(bf[0], lambda a: bf[1])
                    print(f"  [{i:>2}] {bf[0].split('/')[-1]}  {bf[1]}")
            warte = float(s.get("warte", 0))
            if warte:
                time.sleep(warte)
    print("✅  Show fertig.")


def main():
    ap = argparse.ArgumentParser(description="Mehrere Roboterarme synchron steuern (Show).")
    ap.add_argument("choreo", help="Pfad zur Choreografie-JSON")
    ap.add_argument("--arme", nargs="+", help="Arm-Adressen (überschreibt die JSON-Liste)")
    ap.add_argument("--wiederhole", type=int, default=1, help="Wie oft die Choreo laufen soll")
    ap.add_argument("--tempo", type=float, help="Grad pro Schritt (überschreibt JSON)")
    args = ap.parse_args()

    with open(args.choreo, encoding="utf-8") as f:
        choreo = json.load(f)

    roh = args.arme if args.arme else choreo.get("arme", [])
    if not roh:
        ap.error("Keine Arme angegeben — weder per --arme noch in der JSON.")
    arme = [adresse(a) for a in roh]

    try:
        fuehre_aus(arme, choreo, args.wiederhole, args.tempo)
    except KeyboardInterrupt:
        print("\n⛔ NOT-AUS an alle Arme …")
        with ThreadPoolExecutor(max_workers=len(arme)) as pool:
            list(pool.map(lambda a: sende(a, "/api/panik", {}), arme))
        sys.exit(130)


if __name__ == "__main__":
    main()
