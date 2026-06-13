# Hardware-Inbetriebnahme (Radxa ROCK Pi 4 SE)

Zielplattform: **Radxa ROCK Pi 4 Model SE** (RK3399-T, keine NPU) + **Arducam 5 MP USB-UVC-Kamera**
+ **PCA9685** 16-Kanal-Servotreiber + **EEZYbotARM MK2** (3× MG996R/MG995 + 1× SG90).

## Verdrahtung

| PCA9685 | Verbindung |
|---|---|
| VCC (Logik) | 3V3 des Boards |
| GND | **gemeinsame Masse** mit Board **und** Servo-Netzteil |
| SDA / SCL | I²C-Pins des 40-Pin-Headers |
| V+ (Servo) | **separates 5–6 V / ≥3 A Netzteil** — *nicht* vom Board! |

Servo-Kanäle (Default, in `config.py` änderbar): `basis=0, schulter=1, ellbogen=2, greifer=3`.
Kamera: per USB anstecken (UVC, erscheint als `/dev/video0`).

> ⚠️ **Servos nie aus dem Board speisen** (Brown-out). Gemeinsame Masse nicht vergessen.
> Bewegungsgrenzen in der Config konservativ halten — der Arm kann klemmen.

## Schritte

```bash
git clone <repo> roboterarm && cd roboterarm
./install.sh                       # Pakete, Python-Deps, I2C, optional Autostart
```

1. **I²C-Bus finden:** `i2cdetect -y 7` (ggf. andere Busnummer probieren). Es muss `40` erscheinen.
   Den Wert in `~/.roboterarm/config.json` als `i2c_bus` setzen (oder `Config.i2c_bus`).
2. **Backend auf Hardware:** in der Config `"backend": "hardware"` — oder die Beispiele/den Dienst
   schlicht **ohne** `ROBOTERARM_BACKEND=sim` starten (Auto-Erkennung nutzt Hardware, sobald `smbus2`/`cv2` da sind).
3. **Kalibrieren:** `PYTHONPATH=. python3 calibrate.py` — Home, Grenzen, Offsets je Gelenk; optional Test-Winken.
4. **Starten:** `PYTHONPATH=. python3 service/robot_service.py` → `http://<board-ip>:8765/`.

## Kalibrier-Hinweise (echte Hardware)

- **Servohörner** in Home-Stellung montieren, *bevor* das Gestänge dran kommt.
- **Pulsbreiten** `puls_min`/`puls_max` (µs) pro Servo anpassen, falls 0–180° nicht exakt stimmen.
- **`invertiert`** setzen, wenn ein Gelenk falschherum dreht.
- **Zentrier-Vorzeichen:** dreht `zentriere_auf` vom Ziel *weg*, das Vorzeichen in
  `Arm.zentriere_auf` (Verstärkung) umkehren — es ist montageabhängig.
- **Inverse Kinematik:** `gehe_zu` ist eine Näherung; `laenge_oberarm/_unterarm/basis_hoehe`
  in der Config an den realen Arm anpassen.

## ML auf dem RK3399-T

Keine NPU → CPU-Inferenz mit wenigen FPS. Der Default-Extraktor (Farbhistogramm + Thumbnail)
läuft rein in numpy. Für stärkere Merkmale ein MobileNet-TFLite-Modell hinterlegen:

```bash
export ROBOTERARM_MOBILENET=/pfad/zu/mobilenet_v2_embeddings.tflite
```

## Fehlersuche

| Symptom | Ursache / Lösung |
|---|---|
| `i2cdetect` zeigt kein `40` | Verkabelung/Bus falsch; anderen Bus probieren; I²C aktiviert? |
| Servos zucken/Board startet neu | Servos am Board statt am eigenen Netzteil; Netzteil zu schwach |
| „Kamera lieferte kein Bild" | falscher `kamera_index`; `ls /dev/video*`; USB neu stecken |
| Gelenk dreht falschherum | `invertiert: true` in der Gelenk-Config |
| ML langsam | Bildauflösung/!FPS senken; kleines Modell; kNN statt LogReg |
