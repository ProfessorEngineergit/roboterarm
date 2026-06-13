"""Servo-Ansteuerung über den PCA9685 — board-unabhängig per smbus2.

Zwei Backends:
  * PCA9685Backend  — echte Hardware (I2C, z.B. Radxa ROCK Pi 4)
  * SimBackend      — Simulation, merkt sich nur die Pulsbreiten

Darüber liegt ServoController: kennt die Konfiguration, rechnet Winkel -> Pulsbreite,
erzwingt Winkelgrenzen und fährt Ziele *sanft* (interpoliert) an.
"""
from __future__ import annotations

import os
import time


def _hardware_verfuegbar() -> bool:
    try:
        import smbus2  # noqa: F401
        return True
    except Exception:
        return False


class ServoBackend:
    def setze_puls(self, kanal: int, mikrosekunden: float) -> None:
        raise NotImplementedError

    def schliessen(self) -> None:
        pass


class SimBackend(ServoBackend):
    """Tut so, als gäbe es Servos — merkt sich die letzte Pulsbreite je Kanal."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.pulse: dict[int, float] = {}

    def setze_puls(self, kanal: int, mikrosekunden: float) -> None:
        self.pulse[kanal] = mikrosekunden
        if self.verbose:
            print(f"[SIM] Kanal {kanal}: {mikrosekunden:.0f} µs")


class PCA9685Backend(ServoBackend):
    """Minimaler PCA9685-Treiber (16-Kanal-PWM) direkt über I2C/smbus2."""

    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, bus: int = 7, adresse: int = 0x40, freq: int = 50):
        import smbus2
        self.bus = smbus2.SMBus(bus)
        self.adr = adresse
        self.freq = freq
        self._init(freq)

    def _schreibe(self, reg: int, val: int) -> None:
        self.bus.write_byte_data(self.adr, reg, val & 0xFF)

    def _init(self, freq: int) -> None:
        self._schreibe(self.MODE1, 0x00)
        time.sleep(0.01)
        prescale = round(25_000_000.0 / (4096 * freq)) - 1
        alt = self.bus.read_byte_data(self.adr, self.MODE1)
        self._schreibe(self.MODE1, (alt & 0x7F) | 0x10)   # Sleep zum Setzen des Prescale
        self._schreibe(self.PRESCALE, prescale)
        self._schreibe(self.MODE1, alt)
        time.sleep(0.005)
        self._schreibe(self.MODE1, alt | 0xA1)            # Restart + Auto-Increment

    def setze_puls(self, kanal: int, mikrosekunden: float) -> None:
        periode_us = 1_000_000.0 / self.freq
        off = int(round(mikrosekunden / periode_us * 4096)) & 0x0FFF
        basis = self.LED0_ON_L + 4 * kanal
        self._schreibe(basis + 0, 0)            # ON_L
        self._schreibe(basis + 1, 0)            # ON_H
        self._schreibe(basis + 2, off & 0xFF)   # OFF_L
        self._schreibe(basis + 3, off >> 8)     # OFF_H

    def schliessen(self) -> None:
        try:
            self.bus.close()
        except Exception:
            pass


def erzeuge_backend(cfg) -> ServoBackend:
    wahl = os.environ.get("ROBOTERARM_BACKEND", cfg.backend)
    if wahl == "auto":
        wahl = "hardware" if _hardware_verfuegbar() else "sim"
    if wahl == "hardware":
        return PCA9685Backend(cfg.i2c_bus, cfg.pca9685_adresse)
    return SimBackend(verbose=os.environ.get("ROBOTERARM_SIM_VERBOSE") == "1")


class ServoController:
    def __init__(self, cfg, backend: ServoBackend | None = None):
        self.cfg = cfg
        self.backend = backend or erzeuge_backend(cfg)
        self.winkel: dict[str, float] = {n: g.home for n, g in cfg.gelenke.items()}
        for name, w in self.winkel.items():     # Anfangsstellung anfahren
            self._anwenden(name, w)

    def _puls(self, g, winkel: float) -> float:
        w = winkel
        if g.invertiert:
            w = (g.min_winkel + g.max_winkel) - w
        w += g.offset
        spanne = g.puls_max - g.puls_min
        return g.puls_min + (w / 180.0) * spanne

    def _anwenden(self, name: str, winkel: float) -> None:
        g = self.cfg.gelenke[name]
        self.backend.setze_puls(g.kanal, self._puls(g, winkel))

    def grenzen(self, name: str, winkel: float) -> float:
        g = self.cfg.gelenke[name]
        return max(g.min_winkel, min(g.max_winkel, winkel))

    def setze(self, name: str, ziel: float, sanft: bool = True, speed: float | None = None) -> float:
        ziel = self.grenzen(name, ziel)
        start = self.winkel[name]
        schrittweite = speed if (speed and speed > 0) else self.cfg.speed_grad_pro_schritt
        if not sanft or schrittweite <= 0:
            self.winkel[name] = ziel
            self._anwenden(name, ziel)
            return ziel
        n = max(1, int(abs(ziel - start) / schrittweite))
        for i in range(1, n + 1):
            w = start + (ziel - start) * i / n
            self.winkel[name] = w
            self._anwenden(name, w)
            time.sleep(self.cfg.schritt_pause_s)
        self.winkel[name] = ziel
        self._anwenden(name, ziel)
        return ziel

    def schliessen(self) -> None:
        self.backend.schliessen()
