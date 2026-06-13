# Die drei Ebenen: Scratch → EduBlocks → Python

Dasselbe können — drei Darstellungen. Alle rufen am Ende **dieselbe `roboterarm`-API**.

## Ebene 1 — Scratch (Blöcke)
Siehe [`scratch/README.md`](../scratch/README.md). Einstieg, volle visuelle Programmierung,
Blöcke sprechen per HTTP mit dem Dienst.

## Ebene 2 — EduBlocks (Blöcke = Python)
[EduBlocks](https://edublocks.org) zeigt zu jedem Block die **eine Python-Zeile** daneben und
lässt sie direkt bearbeiten — der ideale Übergang von Blöcken zu Text.

Einrichtung auf dem Board:
1. EduBlocks (oder schlicht **Thonny**, auf Raspberry-Pi-/Debian-Images vorhanden) öffnen.
2. Sicherstellen, dass das Paket importierbar ist: Projekt im Repo-Ordner starten **oder**
   `pip install -e .` (siehe [Hardware-Doku](hardware.md)).
3. Code wie unten schreiben — jeder „Block" ist eine Zeile.

## Ebene 3 — Voller Python
Im **Code-Tab** der Weboberfläche, in **Thonny** oder als Datei in `examples/`.

## „Rosetta" — gleiche Aktion in jeder Ebene

| Scratch-Block | Python (EduBlocks/Thonny) |
|---|---|
| Grundstellung | `arm.home()` |
| basis auf (90) Grad | `arm.basis(90)` |
| Greifer (zu) | `arm.greifer.zu()` |
| drehe bis (rot) sichtbar | `arm.suche("rot")` |
| zentriere auf (rot) | `arm.zentriere_auf("rot")` |
| hole (blau) | `arm.hole("blau")` |
| sehe ich (Ball)? | `arm.sieht("Ball")` |
| lerne (Ball) mit (15) Bildern | `arm.lerne("Ball", 15)` |
| erkanntes Objekt | `arm.erkenne()["label"]` |

Vollständiges Python-Startprogramm:

```python
from roboterarm import Arm
arm = Arm()
arm.home()

# Bringe dem Arm ein Objekt bei …
arm.lerne("Apfel", 20)
arm.lerne("nichts", 20)

# … und lass ihn danach selbst suchen:
if arm.suche("Apfel"):
    arm.zentriere_auf("Apfel")
    arm.aufheben()
    arm.ablegen()
    print("Apfel geholt!")
```
