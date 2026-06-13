"""Wiederverwendbare Verhalten/Choreografien — funktional auf einem Arm.

    from roboterarm import Arm
    from roboterarm.verhalten import tanz, pick_and_place, bewache
"""
from __future__ import annotations


def winken(arm, male: int = 3):
    arm.schulter(120)
    for _ in range(male):
        arm.basis(70)
        arm.basis(110)
    arm.basis(90)


def tanz(arm):
    arm.home()
    for _ in range(2):
        arm.basis(45); arm.schulter(120); arm.ellbogen(60); arm.greifer.auf()
        arm.basis(135); arm.schulter(70); arm.ellbogen(120); arm.greifer.zu()
    arm.home()


def pick_and_place(arm, von_basis: float, nach_basis: float):
    arm.basis(von_basis)
    arm.aufheben()
    arm.basis(nach_basis)
    arm.ablegen()


def bewache(arm, ziel, runden: int = 30, bei_sichtung=None) -> bool:
    """Beobachtet; ruft bei_sichtung(arm) auf, sobald *ziel* erscheint."""
    for _ in range(runden):
        if arm.sieht(ziel):
            if bei_sichtung:
                bei_sichtung(arm)
            return True
    return False


def aufraeumen(arm, zuordnung: dict) -> int:
    """Sortiert alle erkannten Objekte gemäß {ziel -> Ablage-Basiswinkel}."""
    return arm.sortiere(zuordnung)
