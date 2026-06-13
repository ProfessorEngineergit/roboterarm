# Änderungsverlauf

## 0.2.0
- **Generisch für beliebige Objekte:** Vision mit benannten Farb-Presets (inkl. Rot-Wrap),
  eigenen HSV-Bereichen und Multi-Blob-Erkennung; `arm.sieht/finde/suche/zentriere_auf/hole/sortiere`
  funktionieren mit Farben **oder** gelernten ML-Klassen.
- **ML-Studio:** beliebige Klassen, austauschbare Merkmals-Extraktoren (MobileNet/tflite,
  Farbhistogramm, Thumbnail) und Klassifikatoren (kNN, NearestCentroid, LogReg), Train/Test-Split,
  **Confusion-Matrix**, Persistenz; Projekte (`Projekt`).
- **Arm:** Posen speichern/anfahren, Bewegungsaufnahme/-wiedergabe, Tempo pro Bewegung, IK `gehe_zu`.
- **Service:** REST-API für Vision, KI, Projekte, Posen, Aufnahme, **Code-Ausführung** (Subprozess
  mit Stop), MJPEG-Stream, CORS; High-Level-Verhalten-Endpunkte.
- **Web-SPA:** Tabs Manuell, Vision, KI-Studio, Code-Editor, Aufnahme/Posen (offline, ohne CDN).
- **Scratch-3-Extension** + EduBlocks-/Thonny-Brücke (drei Ebenen, eine API).
- **Deployment:** `install.sh`, systemd-Unit, Hardware-Doku; Test-Suite, Packaging, CI.

## 0.1.0
- Erste Version: Kern-API (`Arm`), PCA9685-Servotreiber + Simulation, USB-Kamera + Sim-Kamera,
  Ball-Farberkennung, einfaches kNN, Web-„Manuell"-Panel, Beispiele.
