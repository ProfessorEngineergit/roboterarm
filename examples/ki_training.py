"""ML-Workflow in Simulation: Datensatz aufnehmen -> trainieren -> erkennen.

    ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/ki_training.py
"""
from roboterarm import Arm


def main():
    arm = Arm()
    kamera = arm.kamera
    modell = arm.modell

    print("📸 Nehme Datensatz auf …")
    kamera.sim_szene(ball_welt=90, fov_halb=30, hat_ball=True)   # Ball mittig sichtbar
    for _ in range(10):
        modell.aufnehmen("Ball", kamera.frame())
    kamera.sim_szene(hat_ball=False)                             # leere Szene
    for _ in range(10):
        modell.aufnehmen("kein Ball", kamera.frame())

    print("🧠 Trainiere …", modell.trainiere())

    kamera.sim_szene(ball_welt=90, hat_ball=True)
    print("Mit Ball   ->", modell.vorhersage(kamera.frame()), "| sieht('Ball'):", arm.sieht("Ball"))
    kamera.sim_szene(hat_ball=False)
    print("Ohne Ball  ->", modell.vorhersage(kamera.frame()), "| sieht('Ball'):", arm.sieht("Ball"))
    print("✅ ML-Workflow durchlaufen.")


if __name__ == "__main__":
    main()
