# Architektur

Eine Idee trägt alles: **genau eine veröffentlichte Schnittstelle** (`roboterarm.Arm`),
die von allen Zugriffsebenen aufgerufen wird. Hardware vs. Simulation entscheidet eine
Backend-Factory — derselbe Code läuft am Laptop (Sim) wie am Board (echte Servos/Kamera).

```
 Scratch-Blöcke      Web-SPA (Manuell/Vision/KI/Code)      voller Python / Thonny
        │                        │                                  │
        └────── HTTP/REST ───────┴──────── HTTP/REST ───────────────┤  (oder direkter Import)
                                 │                                  │
                       service/robot_service.py                     │
                                 │                                  │
                                 ▼                                  ▼
                    ┌──────────────────────  roboterarm.Arm  ──────────────────────┐
                    │  arm.py   (Gelenke, Greifer, Posen, Aufnahme, Verhalten, IK)  │
                    │  vision.py (Farben/Objekte)   ml.py (Datensatz+Klassifikator) │
                    │  servos.py   kamera.py   config.py   projekt.py   verhalten.py │
                    └───────────────────────────────────────────────────────────────┘
                                 │                         │
                      Backend-Factory (auto)      Backend-Factory (auto)
                       ┌─────────┴─────────┐       ┌───────┴────────┐
                  PCA9685 (smbus2)     SimBackend  USB/UVC (cv2)   SimKamera
```

## Schichten

1. **Bibliothek `roboterarm/`** — die API + Logik. Schwergewichtige Importe (numpy/cv2/tflite)
   sind *lazy*; der reine Bewegungs-Sim-Kern läuft ohne sie.
2. **Dienst `service/`** — HTTP-Server (nur Standardbibliothek), serviert die Web-SPA und die
   REST-API, führt Nutzer-Python in einem **Subprozess** aus (mit Stop), CORS offen für Scratch.
3. **Frontends** — Web-SPA (`web/`), Scratch-Extension (`scratch/`), Thonny/EduBlocks.

## Backend-Auswahl

`ROBOTERARM_BACKEND` = `auto` (Default) | `sim` | `hardware`.
Bei `auto` wird Hardware genutzt, sobald `smbus2` (Servos) bzw. `cv2` (Kamera) importierbar sind,
sonst Simulation. So ist Entwicklung ohne Hardware möglich und das Deployment ändert nichts am Code.

## ML-Datenfluss

```
Kamerabild ─► Merkmals-Extraktor ─► Klassifikator ─► Label (+ Konfidenz)
            (MobileNet/Farbhist./Thumb)  (kNN/Centroid/LogReg)
```
Training (kNN) ist instanzbasiert und in Millisekunden fertig — passend für die NPU-lose CPU
des RK3399-T. Auswertung liefert Genauigkeit + Confusion-Matrix.
