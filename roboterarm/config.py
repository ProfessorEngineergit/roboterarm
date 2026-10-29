"""Konfiguration pro Roboterarm-Station.

Hält Kanalzuordnung, Winkelgrenzen, Home-Pose, Servo-Pulsbreiten, Armgeometrie
(für inverse Kinematik), den HSV-Farbbereich der Ball-Erkennung und die
Backend-/Hardware-Einstellungen. Wird als JSON gespeichert (calibrate.py).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict, fields

STANDARD_PFAD = os.environ.get(
    "ROBOTERARM_CONFIG", os.path.expanduser("~/.roboterarm/config.json")
)


@dataclass
class GelenkConfig:
    """Ein einzelnes Servo-Gelenk."""
    kanal: int                       # PCA9685-Kanal (0..15)
    min_winkel: float = 0.0          # mechanische Untergrenze (Grad)
    max_winkel: float = 180.0        # mechanische Obergrenze (Grad)
    home: float = 90.0               # Ruhestellung
    offset: float = 0.0              # Kalibrier-Offset (mechanischer Nullpunkt)
    puls_min: int = 500              # Pulsbreite (µs) bei 0°  (MG90S)
    puls_max: int = 2400             # Pulsbreite (µs) bei 180° (MG90S typ. ~500–2400)
    invertiert: bool = False         # Drehrichtung umkehren


def _standard_gelenke():
    return {
        "basis":    GelenkConfig(kanal=0, min_winkel=0,  max_winkel=180, home=90),
        "schulter": GelenkConfig(kanal=1, min_winkel=20, max_winkel=160, home=90),
        "ellbogen": GelenkConfig(kanal=2, min_winkel=20, max_winkel=160, home=90),
        "greifer":  GelenkConfig(kanal=3, min_winkel=30, max_winkel=110, home=35),
    }


@dataclass
class Config:
    gelenke: dict = field(default_factory=_standard_gelenke)
    greifer_auf: float = 95.0
    greifer_zu: float = 35.0

    # Armgeometrie (mm) — EEZYbotARM MK1 (Quelle: meisben/easyEEZYbotARM, L1/L2/L3);
    # auf echter HW via calibrate.py final justieren.
    laenge_oberarm: float = 80.0     # MK1 L2
    laenge_unterarm: float = 80.0    # MK1 L3
    basis_hoehe: float = 61.0        # MK1 L1

    # Ball-Farbbereich (HSV, OpenCV-Konvention: H 0..179, S/V 0..255). Default ~orange.
    hsv_min: tuple = (5, 120, 120)
    hsv_max: tuple = (20, 255, 255)

    # Bewegung
    speed_grad_pro_schritt: float = 3.0
    schritt_pause_s: float = 0.02

    # Hardware
    i2c_bus: int = 7                 # ROCK Pi 4: per i2cdetect ermitteln
    pca9685_adresse: int = 0x40
    backend: str = "auto"            # "auto" | "sim" | "hardware"
    kamera_index: int = 0

    # Eigene Farb-Presets: name -> [[low,high], ...] (HSV, OpenCV-Konvention)
    farben: dict = field(default_factory=dict)
    projekt: str = "standard"

    # ---- Serialisierung ----
    def to_dict(self) -> dict:
        d = asdict(self)             # verschachtelte GelenkConfig -> dict
        d["hsv_min"] = list(self.hsv_min)
        d["hsv_max"] = list(self.hsv_max)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        d = dict(d)
        if "gelenke" in d and d["gelenke"]:
            d["gelenke"] = {n: GelenkConfig(**gd) for n, gd in d["gelenke"].items()}
        for key in ("hsv_min", "hsv_max"):
            if key in d:
                d[key] = tuple(d[key])
        if d.get("farben"):
            d["farben"] = {n: [(tuple(lo), tuple(hi)) for lo, hi in bereiche]
                           for n, bereiche in d["farben"].items()}
        bekannt = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in bekannt})


def lade_config(pfad: str = STANDARD_PFAD) -> Config:
    if os.path.exists(pfad):
        with open(pfad, encoding="utf-8") as f:
            return Config.from_dict(json.load(f))
    return Config()


def speichere_config(cfg: Config, pfad: str = STANDARD_PFAD) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(pfad)), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=2, ensure_ascii=False)
    return pfad
