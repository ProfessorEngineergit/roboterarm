"""Arm — die kindgerechte High-Level-Schnittstelle (generisch für *alles*).

Bewegung, Greifer, Kamera, Farb- und ML-Erkennung, Such-/Greif-/Sortier-
Verhalten, benannte Posen, Bewegungsaufnahme und inverse Kinematik — alles
hinter einer API. Kamera/ML werden erst beim ersten Zugriff geladen (lazy),
damit die reine Bewegungs-Simulation ohne numpy/opencv läuft.
"""
from __future__ import annotations

import math

from .config import lade_config
from .servos import ServoController


class Greifer:
    def __init__(self, arm: "Arm"):
        self._arm = arm

    def auf(self):
        self._arm._move("greifer", self._arm.cfg.greifer_auf)

    def zu(self):
        self._arm._move("greifer", self._arm.cfg.greifer_zu)

    def setze(self, winkel: float):
        self._arm._move("greifer", winkel)


class Arm:
    def __init__(self, cfg=None):
        self.cfg = cfg or lade_config()
        self._ctrl = ServoController(self.cfg)
        self.greifer = Greifer(self)
        self._kamera = None
        self._modell = None
        self._projekt = None
        self._aufnahme = None          # None = inaktiv, sonst Liste von Schritten

    # ----------------------------- Gelenke -----------------------------
    def _move(self, name: str, winkel: float, speed: float | None = None):
        self._ctrl.setze(name, winkel, speed=speed)
        if self._aufnahme is not None:
            self._aufnahme.append((name, round(self.winkel(name), 1)))

    def basis(self, winkel: float, speed: float | None = None):
        self._move("basis", winkel, speed)

    def schulter(self, winkel: float, speed: float | None = None):
        self._move("schulter", winkel, speed)

    def ellbogen(self, winkel: float, speed: float | None = None):
        self._move("ellbogen", winkel, speed)

    def bewege(self, name: str, winkel: float, speed: float | None = None):
        self._move(name, winkel, speed)

    def winkel(self, name: str) -> float:
        return self._ctrl.winkel[name]

    def basis_winkel(self) -> float:
        return self._ctrl.winkel["basis"]

    def alle_winkel(self) -> dict:
        return {n: round(self._ctrl.winkel[n], 1) for n in self.cfg.gelenke}

    def tempo(self, grad_pro_schritt: float):
        """Bewegungsgeschwindigkeit setzen (Grad pro Interpolationsschritt)."""
        self.cfg.speed_grad_pro_schritt = max(0.0, float(grad_pro_schritt))

    def home(self):
        for name, g in self.cfg.gelenke.items():
            self._move(name, g.home)

    # ----------------------------- NOT-AUS -----------------------------
    def not_aus(self):
        """Sofort-Stopp: laufende und neue Bewegungen werden unterbunden."""
        self._ctrl.gestoppt.set()

    def weiter(self):
        """Sperre nach NOT-AUS aufheben — neue Bewegungen wieder erlaubt."""
        self._ctrl.gestoppt.clear()

    def servo(self, name: str, an: bool):
        """Servo eines Gelenks an-/ausschalten (aus = kraftlos, von Hand verstellbar)."""
        self._ctrl.schalte(name, an)

    # ------------------------ Kamera / ML / Projekt ------------------------
    @property
    def kamera(self):
        if self._kamera is None:
            from .kamera import Kamera
            self._kamera = Kamera(self.cfg, arm=self)
        return self._kamera

    @property
    def modell(self):
        if self._modell is None:
            from .ml import Modell
            self._modell = Modell()
        return self._modell

    @property
    def projekt(self):
        if self._projekt is None:
            from .projekt import Projekt
            self._projekt = Projekt(self.cfg.projekt)
        return self._projekt

    # ------------------------ Erkennung (generisch) ------------------------
    def sieht(self, ziel) -> bool:
        """True, wenn *ziel* im Bild ist — eine gelernte ML-Klasse ODER eine Farbe."""
        if self._modell is not None and ziel in self._modell.klassen:
            return self._modell.sieht(ziel, self.kamera.frame())
        try:
            from . import vision
            return vision.sieht_farbe(self.kamera.frame(), ziel, self.cfg)
        except (KeyError, TypeError):
            pass
        if self._modell is not None and len(self._modell.datensatz):
            return self._modell.sieht(ziel, self.kamera.frame())
        return False

    def finde(self, ziel):
        """Position des Ziels -> {x, y, groesse, bbox} (x/y in [-1,1]) oder None."""
        from . import vision
        try:
            return vision.finde(self.kamera.frame(), ziel, self.cfg)
        except (KeyError, TypeError):
            return {"x": 0.0, "y": 0.0, "groesse": 0.0, "bbox": None} if self.sieht(ziel) else None

    def finde_alle(self, ziel):
        from . import vision
        try:
            return vision.finde_alle(self.kamera.frame(), ziel, self.cfg)
        except (KeyError, TypeError):
            return []

    def erkenne(self) -> dict:
        """Was sieht das Modell gerade? -> {label, confidence, proba}."""
        return self.modell.vorhersage_detail(self.kamera.frame())

    # ------------------------- ML-Komfort -------------------------
    def lerne(self, label: str, anzahl: int = 15):
        """Nimmt *anzahl* Kamerabilder für eine Klasse auf und trainiert neu."""
        for _ in range(anzahl):
            self.modell.aufnehmen(label, self.kamera.frame())
        return self.modell.trainiere()

    # ------------------------ Verhalten (generisch) ------------------------
    def zentriere_auf(self, ziel, toleranz: float = 0.08, max_schritte: int = 60,
                      verstaerkung: float = 15.0) -> bool:
        """Dreht die Basis (Proportionalregelung), bis *ziel* mittig ist."""
        for _ in range(max_schritte):
            t = self.finde(ziel)
            if t is None:
                return False
            if abs(t["x"]) <= toleranz:
                return True
            # Vorzeichen ist montage-abhängig -> auf echter Hardware kalibrieren.
            self.basis(self.basis_winkel() + t["x"] * verstaerkung)
        return False

    def suche(self, ziel, schritt: float = 6.0, max_schritte: int = 60) -> bool:
        """Dreht die Basis, bis *ziel* sichtbar wird."""
        for _ in range(max_schritte):
            if self.finde(ziel):
                return True
            self.basis(self.basis_winkel() + schritt)
        return bool(self.finde(ziel))

    def hole(self, ziel) -> bool:
        """Komplett: suchen -> zentrieren -> aufheben -> ablegen."""
        if not self.suche(ziel):
            return False
        self.zentriere_auf(ziel)
        self.aufheben()
        self.ablegen()
        return True

    def sortiere(self, zuordnung: dict, runden: int = 10) -> int:
        """zuordnung: {ziel -> Basiswinkel der Ablage}. Sortiert erkannte Objekte ein."""
        erledigt = 0
        for _ in range(runden):
            gefunden = next((z for z in zuordnung if self.suche(z, max_schritte=24)), None)
            if gefunden is None:
                break
            self.zentriere_auf(gefunden)
            self.aufheben()
            self.basis(zuordnung[gefunden])
            self.ablegen()
            erledigt += 1
        return erledigt

    # ----------------------------- Posen -----------------------------
    def pose_speichern(self, name: str):
        self.projekt.pose_speichern(name, self.alle_winkel())

    def pose_anfahren(self, name: str):
        p = self.projekt.pose(name)
        if not p:
            raise KeyError(f"Pose '{name}' unbekannt")
        for gelenk, w in p.items():
            self._move(gelenk, w)

    def posen(self) -> list:
        return list(self.projekt.posen())

    # ----------------------- Bewegungsaufnahme -----------------------
    def aufnahme_start(self):
        self._aufnahme = []

    def aufnahme_stop(self) -> list:
        schritte = self._aufnahme or []
        self._aufnahme = None
        return schritte

    def wiedergabe(self, schritte):
        for name, winkel in schritte:
            self._move(name, winkel)

    # ------------------- Vordefinierte Sequenzen -------------------
    def aufheben(self):
        self.greifer.auf()
        self.schulter(130)
        self.ellbogen(60)
        self.greifer.zu()
        self.schulter(90)
        self.ellbogen(90)

    def ablegen(self):
        self.schulter(130)
        self.ellbogen(60)
        self.greifer.auf()
        self.home()

    # Komfort-Wrapper (Abwärtskompatibilität)
    def zentriere_auf_ball(self, **kw) -> bool:
        return self.zentriere_auf([(self.cfg.hsv_min, self.cfg.hsv_max)], **kw)

    # --------------- Inverse Kinematik (Advanced-Track) ---------------
    def gehe_zu(self, x: float, y: float, z: float) -> dict:
        """Kartesische Zielvorgabe (mm) -> Gelenkwinkel (2-Glied-Planar-IK + Basis).

        Vereinfacht; die Servo-Konvention muss auf echter Hardware kalibriert werden.
        """
        L1, L2 = self.cfg.laenge_oberarm, self.cfg.laenge_unterarm
        basis = math.degrees(math.atan2(y, x))
        r = math.hypot(x, y)
        h = z - self.cfg.basis_hoehe
        d = min(math.hypot(r, h), L1 + L2 - 1e-3)
        cos_e = max(-1.0, min(1.0, (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)))
        ellbogen = math.acos(cos_e)
        cos_s = 1.0 if d == 0 else max(-1.0, min(1.0, (d * d + L1 * L1 - L2 * L2) / (2 * L1 * d)))
        schulter = math.atan2(h, r) + math.acos(cos_s)
        ziel = {"basis": 90 + basis, "schulter": math.degrees(schulter),
                "ellbogen": 180 - math.degrees(ellbogen)}
        self.basis(ziel["basis"])
        self.schulter(ziel["schulter"])
        self.ellbogen(ziel["ellbogen"])
        return {k: round(v, 1) for k, v in ziel.items()}

    def schliessen(self):
        self._ctrl.schliessen()
