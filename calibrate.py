"""Interaktiver Servo-Kalibrier-Assistent (pro Station einmal).

Setzt für jedes Gelenk Home, Grenzen und Offset und speichert sie in die
Config-JSON. Auf dem Board mit echter Hardware ausführen:

    PYTHONPATH=. python3 calibrate.py
"""
from __future__ import annotations

from roboterarm import Arm, lade_config, speichere_config


def _frage_zahl(text, default):
    roh = input(f"{text} [{default}]: ").strip()
    if not roh:
        return float(default)
    try:
        return float(roh)
    except ValueError:
        print("  (keine Zahl – behalte Vorgabe)")
        return float(default)


def _frage_ja_nein(text, default):
    roh = input(f"{text} [{'j' if default else 'n'}]: ").strip().lower()
    if not roh:
        return default
    return roh in ("j", "ja", "y", "yes")


def main():
    cfg = lade_config()
    arm = Arm(cfg)
    print("=== Servo-Kalibrierung ===")
    print("Tippe Winkel ein; der Arm fährt hin. Leer = Vorgabe übernehmen.\n")
    for name, g in cfg.gelenke.items():
        print(f"--- Gelenk: {name} (Kanal {g.kanal}) ---")
        print("  Tipp: dreht das Gelenk genau verkehrt herum (z.B. Greifer schließt statt öffnet")
        print("  oder Schulter fährt in den Anschlag und brummt) -> Drehrichtung umkehren.")
        while True:
            roh = input(f"Testwinkel für '{name}' (oder Enter zum Weiter): ").strip()
            if not roh:
                break
            if roh.lower() in ("i", "inv", "umkehren"):
                g.invertiert = not g.invertiert
                print(f"  Drehrichtung jetzt: {'umgekehrt' if g.invertiert else 'normal'} – probier den Winkel nochmal.")
                continue
            try:
                arm._ctrl.setze(name, float(roh), sanft=True)
            except ValueError:
                print("  bitte eine Zahl eingeben (oder 'i' zum Umkehren der Richtung)")
        g.invertiert = _frage_ja_nein("Drehrichtung umkehren?", g.invertiert)
        g.home = _frage_zahl("Home-Winkel", g.home)
        g.min_winkel = _frage_zahl("min. Winkel", g.min_winkel)
        g.max_winkel = _frage_zahl("max. Winkel", g.max_winkel)
        g.offset = _frage_zahl("Offset", g.offset)
        print()

    cfg.greifer_auf = _frage_zahl("Greifer OFFEN (Winkel)", cfg.greifer_auf)
    cfg.greifer_zu = _frage_zahl("Greifer ZU (Winkel)", cfg.greifer_zu)

    pfad = speichere_config(cfg)
    print(f"\n✅ Kalibrierung gespeichert: {pfad}")

    if input("Testbewegung (winken)? [j/N]: ").strip().lower() in ("j", "y"):
        from roboterarm.verhalten import winken
        winken(arm)
    arm.home()
    arm.schliessen()


if __name__ == "__main__":
    main()
