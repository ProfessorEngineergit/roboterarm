"""roboterarm — die *eine* veröffentlichte Schnittstelle zum 3D-gedruckten KI-Roboterarm.

Alle Zugriffsebenen (Scratch-Blöcke, EduBlocks, voller Python) rufen dieselbe API:

    from roboterarm import Arm
    arm = Arm()
    arm.home()
    arm.basis(90); arm.schulter(60); arm.ellbogen(40)
    arm.greifer.auf(); arm.greifer.zu()

    # generisch für *alles* — Farben oder gelernte Objekte:
    arm.suche("rot"); arm.zentriere_auf("rot"); arm.hole("blau")
    arm.lerne("Tasse", anzahl=20)        # ML: Beispiele aufnehmen + trainieren
    arm.sieht("Tasse")                   # -> True/False
    arm.sortiere({"rot": 40, "blau": 140})

Backend-Auswahl automatisch: echte Hardware (PCA9685 / USB-Kamera) sonst Simulation.
Erzwingen mit der Umgebungsvariable ROBOTERARM_BACKEND=sim|hardware.
"""
from .config import Config, GelenkConfig, lade_config, speichere_config
from .arm import Arm, Greifer

__all__ = [
    "Arm", "Greifer", "Config", "GelenkConfig", "lade_config", "speichere_config",
    "Modell", "Projekt", "vision",
]
__version__ = "0.2.0"


def __getattr__(name):
    # Lazy: schwere Module (numpy) erst bei Bedarf laden.
    # 'vision' NICHT hier behandeln — das ist ein Submodul, das der Import-
    # Mechanismus selbst lädt (sonst Endlos-Rekursion über hasattr).
    if name == "Modell":
        from .ml import Modell
        return Modell
    if name == "Projekt":
        from .projekt import Projekt
        return Projekt
    raise AttributeError(name)
