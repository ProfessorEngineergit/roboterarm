"""ML für beliebige Objekte: mehrere Klassen lernen, bewerten, erkennen.

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/objekt_lernen.py
"""
from roboterarm import Arm


def main():
    arm = Arm()
    k = arm.kamera

    print("📸 Lerne drei Klassen …")
    k.sim_objekte([{"welt": 90, "farbe": "rot", "radius": 26}])
    arm.lerne("rote Tasse", 12)
    k.sim_objekte([{"welt": 90, "farbe": "blau", "radius": 26}])
    arm.lerne("blauer Wuerfel", 12)
    k.sim_objekte([])
    print("   ", arm.lerne("nichts", 12))

    print("📊 Bewertung:", arm.modell.bewerte())

    print("🔎 Erkennung:")
    for szene, name in (([{"welt": 90, "farbe": "rot", "radius": 26}], "rot"),
                        ([{"welt": 90, "farbe": "blau", "radius": 26}], "blau"),
                        ([], "leer")):
        k.sim_objekte(szene)
        d = arm.erkenne()
        print(f"   Szene {name:5s} -> {d['label']}  (Konfidenz {d['confidence']})")
    print("✅ Fertig.")


if __name__ == "__main__":
    main()
