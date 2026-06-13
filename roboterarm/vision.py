"""Generische Bildverarbeitung: beliebige Farben & Objekte erkennen.

Kein „Ball" mehr fest verdrahtet — Ziele sind *benannte Farb-Presets*
(`"rot"`, `"blau"`, …, inkl. korrektem Rot-Wraparound), *eigene HSV-Bereiche*
oder werden vom ML-Modell (ml.py) geliefert. Funktioniert mit OpenCV (Board)
und reinem numpy (Simulation/Laptop). Mehrere Objekte gleichzeitig via
Connected-Components (cv2 → scipy → Einzel-Blob-Fallback).
"""
from __future__ import annotations

import numpy as np

# HSV in OpenCV-Konvention: H 0..179, S/V 0..255.
# Jeder Eintrag ist eine Liste von (low, high)-Paaren (für Farben wie Rot, die
# über den Hue-Nullpunkt „wrappen").
FARBEN: dict[str, list[tuple[tuple, tuple]]] = {
    "rot":     [((0, 110, 80), (10, 255, 255)), ((160, 110, 80), (179, 255, 255))],
    "orange":  [((10, 120, 110), (22, 255, 255))],
    "gelb":    [((22, 90, 90), (34, 255, 255))],
    "gruen":   [((35, 60, 50), (85, 255, 255))],
    "cyan":    [((85, 60, 60), (100, 255, 255))],
    "blau":    [((100, 80, 50), (130, 255, 255))],
    "violett": [((130, 50, 50), (150, 255, 255))],
    "pink":    [((145, 60, 70), (170, 255, 255))],
    "weiss":   [((0, 0, 200), (179, 45, 255))],
    "schwarz": [((0, 0, 0), (179, 255, 55))],
}

# Synonyme, damit Kinder intuitiv tippen können.
SYNONYME = {
    "red": "rot", "orange ": "orange", "yellow": "gelb", "gelb ": "gelb",
    "green": "gruen", "grün": "gruen", "gruen ": "gruen",
    "blue": "blau", "purple": "violett", "lila": "violett", "magenta": "pink",
    "white": "weiss", "black": "schwarz", "türkis": "cyan", "tuerkis": "cyan",
}


def _bgr_to_hsv(frame):
    """BGR-uint8 -> (H, S, V) in OpenCV-Konvention (H 0..179, S/V 0..255)."""
    try:
        import cv2
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return hsv[..., 0].astype(np.float32), hsv[..., 1].astype(np.float32), hsv[..., 2].astype(np.float32)
    except Exception:
        pass
    bgr = frame.astype(np.float32) / 255.0
    b, g, r = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    mx, mn = bgr.max(-1), bgr.min(-1)
    df = mx - mn
    safe = np.where(df == 0, 1.0, df)
    h = np.select(
        [mx == r, mx == g, mx == b],
        [((g - b) / safe) % 6, (b - r) / safe + 2, (r - g) / safe + 4],
        default=0.0,
    ) * 60.0
    h = np.where(df == 0, 0.0, h) / 2.0
    s = np.where(mx == 0, 0.0, df / np.where(mx == 0, 1.0, mx)) * 255.0
    return h, s, mx * 255.0


def ziel_bereiche(ziel, cfg=None):
    """Wandelt ein Ziel in HSV-Bereiche um.

    * Farbname (str)        -> Preset (inkl. eigener cfg.farben)
    * (low, high)           -> ein eigener Bereich
    * [(low,high), ...]     -> mehrere Bereiche
    """
    if isinstance(ziel, str):
        name = SYNONYME.get(ziel.strip().lower(), ziel.strip().lower())
        if cfg is not None and name in getattr(cfg, "farben", {}):
            return cfg.farben[name]
        if name in FARBEN:
            return FARBEN[name]
        raise KeyError(f"Unbekannte Farbe '{ziel}'. Bekannt: {', '.join(verfuegbare_farben())}")
    if isinstance(ziel, (tuple, list)) and len(ziel) == 2 and isinstance(ziel[0], (int, float)):
        # einzelnes (low, high)? -> nur wenn beide 3er-Tupel sind
        pass
    if isinstance(ziel, (tuple, list)) and len(ziel) == 2 and hasattr(ziel[0], "__len__"):
        return [(tuple(ziel[0]), tuple(ziel[1]))]
    if isinstance(ziel, (list, tuple)):
        return [(tuple(lo), tuple(hi)) for lo, hi in ziel]
    raise TypeError(f"Ziel nicht verstanden: {ziel!r}")


def verfuegbare_farben():
    return sorted(FARBEN)


def maske(frame, bereiche):
    h, s, v = _bgr_to_hsv(frame)
    out = None
    for lo, hi in bereiche:
        cur = ((h >= lo[0]) & (h <= hi[0]) & (s >= lo[1]) & (s <= hi[1])
               & (v >= lo[2]) & (v <= hi[2]))
        out = cur if out is None else (out | cur)
    return out


def _komponenten(m):
    """Liste zusammenhängender Regionen: {cx, cy, flaeche, bbox}."""
    try:
        import cv2
        n, _lab, stats, cent = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        return [
            {"cx": float(cent[i][0]), "cy": float(cent[i][1]),
             "flaeche": int(stats[i][4]),
             "bbox": (int(stats[i][0]), int(stats[i][1]), int(stats[i][2]), int(stats[i][3]))}
            for i in range(1, n)
        ]
    except Exception:
        pass
    try:
        from scipy import ndimage
        lab, n = ndimage.label(m)
        comps = []
        for i in range(1, n + 1):
            ys, xs = np.where(lab == i)
            if xs.size:
                comps.append({"cx": float(xs.mean()), "cy": float(ys.mean()), "flaeche": int(xs.size),
                              "bbox": (int(xs.min()), int(ys.min()),
                                       int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))})
        return comps
    except Exception:
        pass
    # Fallback: ein Blob = Schwerpunkt aller Treffer (reicht für 1 Objekt)
    ys, xs = np.nonzero(m)
    if xs.size == 0:
        return []
    return [{"cx": float(xs.mean()), "cy": float(ys.mean()), "flaeche": int(xs.size),
             "bbox": (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))}]


def _norm(comp, frame):
    h, w = frame.shape[:2]
    return {
        "x": (comp["cx"] - w / 2) / (w / 2),     # -1 (links) .. +1 (rechts)
        "y": (comp["cy"] - h / 2) / (h / 2),     # -1 (oben)  .. +1 (unten)
        "groesse": comp["flaeche"] / float(w * h),
        "bbox": comp["bbox"],
    }


def finde(frame, ziel, cfg=None, min_flaeche_anteil: float = 0.0008):
    """Größtes Objekt der Zielfarbe -> {x, y, groesse, bbox} oder None."""
    m = maske(frame, ziel_bereiche(ziel, cfg))
    mindest = max(15, int(min_flaeche_anteil * m.size))
    comps = [c for c in _komponenten(m) if c["flaeche"] >= mindest]
    if not comps:
        return None
    return _norm(max(comps, key=lambda c: c["flaeche"]), frame)


def finde_alle(frame, ziel, cfg=None, min_flaeche_anteil: float = 0.0008, max_n: int = 20):
    m = maske(frame, ziel_bereiche(ziel, cfg))
    mindest = max(15, int(min_flaeche_anteil * m.size))
    comps = sorted((c for c in _komponenten(m) if c["flaeche"] >= mindest),
                   key=lambda c: c["flaeche"], reverse=True)
    return [_norm(c, frame) for c in comps[:max_n]]


def sieht_farbe(frame, ziel, cfg=None) -> bool:
    return finde(frame, ziel, cfg) is not None


# ---- Rückwärtskompatibilität (frühe Versionen) ----
def ball_x(frame, hsv_min, hsv_max):
    t = finde(frame, [(tuple(hsv_min), tuple(hsv_max))])
    return None if t is None else t["x"]
