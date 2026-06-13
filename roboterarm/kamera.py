"""Kamera-Zugriff — USB/UVC über OpenCV auf dem Board, sonst Simulation.

Die SimKamera kann *beliebig viele* farbige Objekte darstellen, deren Lage vom
Basiswinkel des Arms abhängt (Kamera sitzt auf der drehenden Säule). Damit
funktionieren „drehen bis sichtbar", Zentrieren und Sortieren auch ohne Hardware.
"""
from __future__ import annotations

import os

# Anzeigefarben (BGR) für die Sim-Objekte — passen zu den HSV-Presets in vision.py.
FARB_BGR = {
    "orange": (0, 140, 255), "rot": (40, 40, 220), "gelb": (40, 220, 220),
    "gruen": (40, 200, 40), "cyan": (220, 220, 40), "blau": (220, 60, 40),
    "violett": (200, 40, 150), "pink": (180, 50, 255), "weiss": (245, 245, 245),
    "schwarz": (15, 15, 15),
}


def _hardware_cam_verfuegbar() -> bool:
    try:
        import cv2  # noqa: F401
        return True
    except Exception:
        return False


class SimKamera:
    def __init__(self, cfg, arm=None, breite: int = 160, hoehe: int = 120):
        self.cfg = cfg
        self.arm = arm
        self.breite = breite
        self.hoehe = hoehe
        self.fov_halb = 30.0                       # halber Öffnungswinkel (Weitwinkel)
        self.bg = (60, 60, 60)
        self.objekte = [{"welt": 120.0, "farbe": "orange", "radius": 18}]

    # ---- Szene setzen ----
    def sim_szene(self, ball_welt=None, fov_halb=None, hat_ball=None):
        """Abwärtskompatibel: genau ein oranger Ball."""
        if fov_halb is not None:
            self.fov_halb = fov_halb
        if hat_ball is False:
            self.objekte = []
        elif hat_ball is True or ball_welt is not None:
            welt = ball_welt if ball_welt is not None else (
                self.objekte[0]["welt"] if self.objekte else 120.0)
            self.objekte = [{"welt": welt, "farbe": "orange", "radius": 18}]

    def sim_objekte(self, liste):
        """liste: [{"welt": Grad, "farbe": Name, "radius": Pixel}, ...]"""
        self.objekte = [{"welt": o["welt"], "farbe": o.get("farbe", "orange"),
                         "radius": int(o.get("radius", 18))} for o in liste]

    def _sichtbar(self):
        base = self.arm.basis_winkel() if self.arm is not None else 90.0
        out = []
        for o in self.objekte:
            off = (o["welt"] - base + 180) % 360 - 180
            if abs(off) <= self.fov_halb:
                out.append((off / self.fov_halb, o))
        return out

    def frame(self):
        import numpy as np
        img = np.empty((self.hoehe, self.breite, 3), dtype=np.uint8)
        img[:, :] = self.bg
        yy, xx = np.ogrid[: self.hoehe, : self.breite]
        for off, o in self._sichtbar():
            cx = int((self.breite / 2) * (1 + off))
            cy = self.hoehe // 2
            r = o["radius"]
            img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = FARB_BGR.get(o["farbe"], (0, 140, 255))
        return img

    def zeige(self):
        print(f"[SIM-Kamera] sichtbare Objekte: {[o['farbe'] for _, o in self._sichtbar()]}")

    def foto(self, pfad: str):
        try:
            from PIL import Image
            Image.fromarray(self.frame()[:, :, ::-1]).save(pfad)
            return pfad
        except Exception:
            return None

    def schliessen(self):
        pass


class HardwareKamera:
    def __init__(self, cfg, arm=None):
        import cv2
        self.cv2 = cv2
        self.cap = cv2.VideoCapture(cfg.kamera_index)

    def frame(self):
        ok, f = self.cap.read()
        if not ok:
            raise RuntimeError("Kamera lieferte kein Bild (USB/UVC prüfen)")
        return f

    def zeige(self):
        pass

    def foto(self, pfad: str):
        self.cv2.imwrite(pfad, self.frame())
        return pfad

    def schliessen(self):
        try:
            self.cap.release()
        except Exception:
            pass


def Kamera(cfg, arm=None):
    wahl = os.environ.get("ROBOTERARM_BACKEND", cfg.backend)
    if wahl == "auto":
        wahl = "hardware" if _hardware_cam_verfuegbar() else "sim"
    if wahl == "hardware":
        return HardwareKamera(cfg, arm)
    return SimKamera(cfg, arm)
