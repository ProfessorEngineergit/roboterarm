"""Mini-Demo: der Arm fährt Home, winkt und bewegt den Greifer.

Läuft ganz ohne Hardware in der Simulation:

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/tanz.py
"""
from roboterarm import Arm


def main():
    arm = Arm()
    print("→ Home-Position")
    arm.home()

    print("→ Winken 👋")
    for _ in range(3):
        arm.schulter(120)
        arm.basis(70)
        arm.basis(110)
    arm.basis(90)

    print("→ Greifer auf/zu")
    arm.greifer.auf()
    arm.greifer.zu()

    winkel = {n: round(arm.winkel(n), 1) for n in ("basis", "schulter", "ellbogen", "greifer")}
    print("→ Aktuelle Winkel:", winkel)

    arm.home()
    arm.schliessen()
    print("✅ Fertig")


if __name__ == "__main__":
    main()
