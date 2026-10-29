# Hardware-Inbetriebnahme (Radxa ROCK Pi 4 SE)

Zielplattform: **Radxa ROCK Pi 4 Model SE** (RK3399-T, keine NPU) + **InnoMaker 16 MP USB-UVC-Kamera**
(IMX298, Autofokus) + **PCA9685** 16-Kanal-Servotreiber + **EEZYbotARM MK1** (4× MG90S, 9 g).

## Stückliste / Einkaufsliste

**Vorhanden (bestätigt):**
- Radxa ROCK Pi 4 Model SE (Board)
- InnoMaker 16 MP USB-UVC-Kamera (IMX298, Autofokus)
- PCA9685 16-Kanal-PWM-/Servotreiber

**Noch zu beschaffen (Pflicht):**
- **4× MG90S** (3 Achsen + Greifer) — 9-g-Metallgetriebe-Servos (Standard beim MK1)
- **Servo-Netzteil 5 V / ≥3 A** — wir nutzen ein **5 V / 5 A**; der
  **Hohlstecker→Schraubklemmen-Adapter liegt dem Netzteil bei** (keine Extra-Beschaffung)
- **Aktiv gekühltes Gehäuse mit Lüfter + Kühlkörper** (pro Station) — das
  beiliegende **USB-C-Netzteil 5 V/3 A** versorgt zugleich das Board
- **microSD ≥32 GB** (Class 10 / A1) — Boot-Medium des Boards

**Zusammenbau:** kleine **M2/M3**-Schrauben/Muttern (EEZYbotARM-MK1-Stückliste; vieles liegt den Servos bei).

**Schon vorhanden / nicht erneut kaufen:** **Jumperkabel** (Buchse-Buchse, ~4×) für I²C
(SDA/SCL/VCC/GND), 3D-Drucker + **PLA-Filament**, EEZYbotARM-STLs (kostenloser Download).

## Verdrahtung

| PCA9685 | Verbindung |
|---|---|
| VCC (Logik) | 3V3 des Boards |
| GND | **gemeinsame Masse** mit Board **und** Servo-Netzteil |
| SDA / SCL | I²C-Pins des 40-Pin-Headers |
| V+ / GND (Servo) | **separates 5 V / ≥3 A Netzteil** über den **beiliegenden Schraubklemmen-Adapter** — *nicht* vom Board! |

Servo-Kanäle (Default, in `config.py` änderbar): `basis=0, schulter=1, ellbogen=2, greifer=3`.
Kamera: per USB anstecken (UVC, erscheint als `/dev/video0`).

> ⚠️ **Servos nie aus dem Board speisen** (Brown-out). Gemeinsame Masse nicht vergessen.
> Bewegungsgrenzen in der Config konservativ halten — der Arm kann klemmen.

## Schritte

```bash
git clone <repo> roboterarm && cd roboterarm
./install.sh                       # Pakete, Python-Deps, I2C, optional Autostart + Hotspot
```

1. **I²C-Bus finden:** `i2cdetect -y 7` (ggf. andere Busnummer probieren). Es muss `40` erscheinen.
   Den Wert in `~/.roboterarm/config.json` als `i2c_bus` setzen (oder `Config.i2c_bus`).
2. **Backend auf Hardware:** in der Config `"backend": "hardware"` — oder die Beispiele/den Dienst
   schlicht **ohne** `ROBOTERARM_BACKEND=sim` starten (Auto-Erkennung nutzt Hardware, sobald `smbus2`/`cv2` da sind).
3. **Kalibrieren:** `PYTHONPATH=. python3 calibrate.py` — Home, Grenzen, Offsets je Gelenk; optional Test-Winken.
4. **Starten:** `PYTHONPATH=. python3 service/robot_service.py` → `http://<board-ip>:8765/`.

### Workshop-Zugang: jede Station ein eigener WLAN-Hotspot

Damit die Kinder-Laptops ohne Schulnetz und ohne IP-Tipperei drankommen, macht jedes Board
ein **eigenes WLAN** auf:

```bash
sudo ./deploy/hotspot.sh 1     # Station 1 → SSID „Roboterarm-1", Host arm1, Autostart
# Abschalten: sudo ./deploy/hotspot.sh --aus
```

- WLAN **`Roboterarm-<N>`**, Passwort **`roboterarm`** (in `hotspot.sh` änderbar).
- Oberfläche dann unter **`http://arm<N>.local:8765`** (Rückfall `http://10.42.0.1:8765`).
- Setzt **NetworkManager** + **avahi** voraus (installiert `install.sh` mit).

Die bebilderte **Schritt-für-Schritt-Anleitung für Kinder**: [`anleitung_kinder.md`](anleitung_kinder.md).

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
läuft rein in numpy. Das aktiv gekühlte Gehäuse (Lüfter + Kühlkörper) hält die CPU bei
Dauerlast auf Takt, sodass die Inferenz nicht durch Throttling einbricht.
Für stärkere Merkmale ein MobileNet-TFLite-Modell hinterlegen:

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
