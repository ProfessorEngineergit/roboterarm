# Scratch-Anbindung (Ebene 1: Blöcke)

Die Datei [`roboterarm_extension.js`](roboterarm_extension.js) ist eine Scratch-3-Erweiterung.
Sie baut **keine eigene Block-Sprache**, sondern legt eine Handvoll Befehls- und Fühler-Blöcke
über die bestehende `roboterarm`-API — die Blöcke rufen per HTTP den lokalen Dienst
([`service/robot_service.py`](../service/robot_service.py)) auf. Damit steuern Kinder
**denselben Arm** wie über Python, nur in Scratch.

```
Scratch-Blöcke ──HTTP──► robot_service.py ──► roboterarm (Arm/Vision/ML) ──► Hardware
```

## Voraussetzung

Der Dienst muss laufen (am Board oder lokal):

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 service/robot_service.py   # Sim/Test
# oder auf dem Board ohne Variable -> echte Hardware
```

## Extension laden

**Empfohlen: TurboWarp** (Scratch-kompatibel, kann eigene Erweiterungen laden; Desktop-Version läuft offline):

1. [turbowarp.org/editor](https://turbowarp.org/editor) öffnen (oder TurboWarp Desktop).
2. Unten links **Erweiterung hinzufügen** → **Eigene Erweiterung** → **Datei** → `roboterarm_extension.js` wählen.
   *(Beim Laden aus Datei fragt TurboWarp nach „unsandboxed" — bestätigen, da die Extension `fetch` nutzt.)*
3. Die Block-Kategorie **Roboterarm** erscheint.

> Original-Scratch-GUI selbst hosten ist auch möglich (`scratch-gui` per npm builden und
> die Extension als Custom-Extension registrieren), aber für den Workshop ist TurboWarp der
> schnellste, installationsärmste Weg.

## Server-Adresse

Standardmäßig spricht die Extension `http://<aktueller-Host>:8765` an. Läuft der Dienst auf
einem anderen Gerät (z.B. dem ROCK Pi im Schulnetz), zu Beginn des Programms den Block
**„verbinde mit Server [http://<board-ip>:8765]"** benutzen.

## Blöcke

| Block | Wirkung |
|---|---|
| Grundstellung | `arm.home()` |
| [basis/schulter/ellbogen] auf [Winkel] Grad | Gelenk fahren |
| Greifer [auf/zu] | greifen/loslassen |
| Tempo [Grad] | Geschwindigkeit |
| gehe zu x/y/z | inverse Kinematik |
| drehe bis [Ziel] sichtbar | `arm.suche(ziel)` |
| zentriere auf [Ziel] | `arm.zentriere_auf(ziel)` |
| hole [Ziel] | suchen → greifen → ablegen |
| sehe ich [Ziel]? | Fühler: Farbe **oder** gelernte Klasse |
| lerne [Label] mit [n] Bildern · trainiere KI | ML aufnehmen + trainieren |
| erkanntes Objekt | Reporter: aktuelle Vorhersage |

„Ziel" ist eine **Farbe** (`rot`, `blau`, `orange`, …) **oder** eine zuvor **gelernte Klasse**
(`Ball`, `Tasse`, …). Genau dieselbe Logik wie in Python.
