"""Abwärtskompatibilität — die Bildverarbeitung ist nach vision.py umgezogen.

Bitte künftig `from roboterarm import vision` verwenden.
"""
from .vision import ball_x, finde, finde_alle, maske, FARBEN  # noqa: F401
