"""Sortieren nach Farbe: rot -> links, blau -> rechts (Simulation).

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/sortieren.py

Auf echter Hardware genügt:  arm.sortiere({"rot": 40, "blau": 140})
(die aufgehobenen Teile sind dann physisch weg). In der Simulation entfernen
wir sie hier von Hand aus der Szene.
"""
from roboterarm import Arm

ABLAGE = {"rot": 40, "blau": 140}


def main():
    arm = Arm()
    arm.home()
    objekte = [{"welt": 70, "farbe": "rot", "radius": 18},
               {"welt": 150, "farbe": "blau", "radius": 18}]
    arm.kamera.sim_objekte(objekte)

    sortiert = 0
    for o in list(objekte):
        farbe = o["farbe"]
        if not arm.suche(farbe):
            continue
        arm.zentriere_auf(farbe)
        arm.aufheben()
        arm.basis(ABLAGE[farbe])
        arm.ablegen()
        objekte.remove(o)
        arm.kamera.sim_objekte(objekte)          # Teil ist jetzt „weg"
        sortiert += 1
        print(f"  {farbe} -> Ablage bei {ABLAGE[farbe]}°")
    arm.schliessen()
    print(f"✅ {sortiert} Objekte sortiert.")


if __name__ == "__main__":
    main()
