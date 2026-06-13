"""Advanced-Track: kartesische Steuerung über inverse Kinematik.

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/koordinaten.py
"""
from roboterarm import Arm


def main():
    arm = Arm()
    arm.home()
    for (x, y, z) in [(120, 0, 60), (90, 60, 40), (100, -40, 90)]:
        print(f"gehe_zu({x:4d},{y:4d},{z:3d}) -> {arm.gehe_zu(x, y, z)}")
    arm.home()
    arm.schliessen()
    print("✅ Koordinaten angefahren.")


if __name__ == "__main__":
    main()
