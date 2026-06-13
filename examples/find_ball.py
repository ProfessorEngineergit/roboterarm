"""Die KI-Story: drehen bis sichtbar -> zentrieren -> aufheben -> ablegen.

Funktioniert mit jeder Farbe — hier am orangen Ball gezeigt.

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/find_ball.py
"""
from roboterarm import Arm

ZIEL = "orange"


def main():
    arm = Arm()
    arm.home()
    if hasattr(arm.kamera, "sim_objekte"):                 # Sim-Szene
        arm.kamera.sim_objekte([{"welt": 130, "farbe": "orange", "radius": 18}])

    print(f"Suche '{ZIEL}' …")
    if not arm.suche(ZIEL):
        print("❌ Nichts gefunden.")
        return
    print(f"👀 Gesichtet bei Basis = {arm.basis_winkel():.0f}°. Zentriere …")
    arm.zentriere_auf(ZIEL)
    print(f"🎯 Zentriert bei Basis = {arm.basis_winkel():.0f}°. Hebe auf …")
    arm.aufheben()
    arm.ablegen()
    arm.schliessen()
    print("✅ Gefunden, aufgehoben und abgelegt.")


if __name__ == "__main__":
    main()
