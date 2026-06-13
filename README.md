# roboterarm 🤖

Offene Lern-Plattform für einen **3D-gedruckten KI-Roboterarm** — ein offener
„LEGO-Spike-Klon" für den Schul-/Workshop-Einsatz (Grundschule bis Oberstufe).

Dieselben Fähigkeiten — **Bewegung, Kamera, maschinelles Lernen** — auf **drei Ebenen**:

> **Scratch-Blöcke → EduBlocks/Python (Blöcke = Code) → voller Python**

…und das **generisch für beliebige Objekte** (nicht nur „ein Ball") sowie **komplett offline**
auf dem Gerät (Radxa ROCK Pi 4 SE + USB-Kamera + PCA9685-Servos). Alles läuft auch ohne
Hardware in **Simulation** — auf jedem Laptop.

## Highlights

- 🦾 **Eine veröffentlichte API** (`roboterarm.Arm`), die alle Ebenen aufrufen.
- 🎨 **Generische Wahrnehmung:** beliebige Farben (`rot`, `blau`, …, eigene HSV) **oder** gelernte Objekte.
- 🧠 **ML-Studio:** beliebige Klassen, Training in Millisekunden (kNN/Centroid/LogReg), **Confusion-Matrix** — offline, ohne NPU.
- 🕹️ **Web-Oberfläche:** Manuell · Vision · KI-Studio · Code-Editor (mit Ausführung) · Aufnahme/Posen.
- 🧩 **Scratch-3-Extension** + EduBlocks/Thonny-Brücke (eine API, drei Darstellungen).
- 🔁 **Sim/Hardware automatisch:** identischer Code am Laptop und am Board.
- 🧪 Test-Suite, CI, Packaging, Deployment (`install.sh` + systemd).

## 🛠️ Bauen & Drucken (es wird nichts gekauft)

Die Arm-Teile (**EEZYbotARM MK2**) werden von den Betreuer:innen **vorab** gedruckt; jedes
Kind druckt im Workshop **genau ein eigenes Teil** — sein **Namensschild** — als 3D-Druck-Erlebnis:

```bash
python3 hardware/3d-druck/namensschild.py MAX     # -> namensschild_MAX.stl (drucken, fertig)
```

Vollständige, eigenständige **Bau- & Druckanleitung** (Druckeinstellungen, Teileliste, Montage):
**[hardware/3d-druck/README.md](hardware/3d-druck/README.md)**.

## Schnellstart (Simulation — ohne Hardware, nur `numpy`)

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/find_ball.py     # finden→zentrieren→aufheben
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/sortieren.py     # rot/blau sortieren
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/objekt_lernen.py # ML: mehrere Klassen + Bewertung
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/koordinaten.py   # inverse Kinematik
```

## Weboberfläche

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 service/robot_service.py
# Browser:  http://localhost:8765/        (im Workshop: http://<board-ip>:8765/)
```

Tabs: **Manuell** (Slider, Greifer, IK), **Vision** (Live-Erkennung jeder Farbe),
**KI-Studio** (Klassen anlegen, aufnehmen, trainieren, Confusion-Matrix, Live-Erkennung),
**Code** (Python-Editor mit Ausführung & Ausgabe), **Aufnahme & Posen**.

## Die eine Schnittstelle

```python
from roboterarm import Arm
arm = Arm()
arm.home()
arm.basis(90); arm.greifer.zu()

arm.suche("rot"); arm.zentriere_auf("rot"); arm.hole("blau")   # Farben
arm.lerne("Tasse", 20); arm.sieht("Tasse"); arm.erkenne()      # beliebige Objekte (ML)
arm.sortiere({"rot": 40, "blau": 140})                          # einsortieren
arm.gehe_zu(120, 0, 60)                                         # inverse Kinematik
```

## Drei Ebenen

| Ebene | Werkzeug | Wo |
|---|---|---|
| 1 · Blöcke | **Scratch 3** + Extension | [`scratch/`](scratch/README.md) |
| 2 · Blöcke = Python | **EduBlocks / Thonny** | [`docs/scratch_edublocks.md`](docs/scratch_edublocks.md) |
| 3 · voller Python | **Code-Tab / Thonny / `examples/`** | [`examples/`](examples) |

## Projektstruktur

```
roboterarm/        Bibliothek (die eine API)
  arm.py vision.py ml.py servos.py kamera.py config.py projekt.py verhalten.py
service/           HTTP-Dienst (REST + Web-SPA + Code-Ausführung), nur Standardbibliothek
web/               Vanilla-JS-Oberfläche (offline, ohne CDN)
scratch/           Scratch-3-Extension + Anleitung
examples/          tanz, find_ball, sortieren, objekt_lernen, koordinaten
tests/             Test-Suite (Simulation)
deploy/            systemd-Unit
docs/              Architektur, API, Hardware, Curriculum, Ebenen
hardware/3d-druck/ 3D-Dateien + Bauanleitung (EEZYbotARM vorab, Namensschild fürs Kind)
calibrate.py       Servo-Kalibrier-Assistent      install.sh   Inbetriebnahme
```

## Hardware

Radxa ROCK Pi 4 SE + Arducam USB-UVC + PCA9685 + EEZYbotARM MK2 (3× MG996R + SG90).
- **Bauen & 3D-Druck** (Arm vorab, ein Teil pro Kind, nichts kaufen): **[hardware/3d-druck/README.md](hardware/3d-druck/README.md)**
- **Elektronik, Verkabelung, Kalibrierung & Fehlersuche:** **[docs/hardware.md](docs/hardware.md)**

```bash
./install.sh        # Pakete, Deps, I2C, optional Autostart (systemd)
```

Backend automatisch: `smbus2`/`cv2` vorhanden → Hardware, sonst Simulation. Erzwingen mit
`ROBOTERARM_BACKEND=sim|hardware`.

## Tests

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## Lizenz

MIT — siehe [LICENSE](LICENSE). Doku: [`docs/`](docs). Mitmachen: [CONTRIBUTING.md](CONTRIBUTING.md).
