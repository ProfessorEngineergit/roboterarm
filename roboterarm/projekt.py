"""Projekte bündeln alles, was ein Team erarbeitet: Programme (Python-Text),
Datensätze, ML-Modelle und gespeicherte Posen — unter einem Ordner.

Standardbasis: ~/.roboterarm/projekte/<name>/  (per ROBOTERARM_PROJEKTE änderbar).
"""
from __future__ import annotations

import json
import os
import time

BASIS = os.environ.get("ROBOTERARM_PROJEKTE", os.path.expanduser("~/.roboterarm/projekte"))


class Projekt:
    def __init__(self, name: str = "standard"):
        self.name = name
        self.pfad = os.path.join(BASIS, name)
        for unter in ("programme", "datensaetze", "modelle"):
            os.makedirs(os.path.join(self.pfad, unter), exist_ok=True)
        self._posen_pfad = os.path.join(self.pfad, "posen.json")

    # ---- Programme (Python-Quelltext) ----
    def programm_speichern(self, name: str, code: str):
        with open(os.path.join(self.pfad, "programme", name + ".py"), "w", encoding="utf-8") as f:
            f.write(code)

    def programm_laden(self, name: str) -> str:
        with open(os.path.join(self.pfad, "programme", name + ".py"), encoding="utf-8") as f:
            return f.read()

    def programme(self) -> list[str]:
        d = os.path.join(self.pfad, "programme")
        return sorted(f[:-3] for f in os.listdir(d) if f.endswith(".py"))

    # ---- Posen ----
    def _lade_posen(self) -> dict:
        if os.path.exists(self._posen_pfad):
            with open(self._posen_pfad, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def pose_speichern(self, name: str, winkel: dict):
        posen = self._lade_posen()
        posen[name] = {k: round(float(v), 1) for k, v in winkel.items()}
        with open(self._posen_pfad, "w", encoding="utf-8") as f:
            json.dump(posen, f, ensure_ascii=False, indent=2)

    def pose(self, name: str) -> dict | None:
        return self._lade_posen().get(name)

    def pose_loeschen(self, name: str):
        posen = self._lade_posen()
        if name in posen:
            del posen[name]
            with open(self._posen_pfad, "w", encoding="utf-8") as f:
                json.dump(posen, f, ensure_ascii=False, indent=2)

    def posen(self) -> dict:
        return self._lade_posen()

    # ---- Pfade für Datensätze / Modelle ----
    def datensatz_pfad(self, name: str = "standard") -> str:
        p = os.path.join(self.pfad, "datensaetze", name)
        os.makedirs(p, exist_ok=True)
        return p

    def modell_pfad(self, name: str = "standard") -> str:
        p = os.path.join(self.pfad, "modelle", name)
        os.makedirs(p, exist_ok=True)
        return p

    def info(self) -> dict:
        return {"name": self.name, "pfad": self.pfad,
                "programme": self.programme(), "posen": list(self.posen())}

    @staticmethod
    def liste() -> list[str]:
        if not os.path.isdir(BASIS):
            return []
        return sorted(d for d in os.listdir(BASIS) if os.path.isdir(os.path.join(BASIS, d)))

    @staticmethod
    def loeschen(name: str):
        import shutil
        p = os.path.join(BASIS, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
