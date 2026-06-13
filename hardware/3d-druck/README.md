# Bauen & Drucken — Anleitung

Diese Anleitung steht für sich: Sie führt vom leeren Druckbett zum fertig montierten
Roboterarm. **Es wird nichts zusätzlich gekauft** — alles entsteht aus vorhandenem
3D-Drucker und Filament.

> **Prinzip:** Die Betreuer:innen drucken die Arm-Teile **vorab** (das dauert lange).
> Jedes Kind druckt im Workshop **genau ein eigenes Teil** als 3D-Druck-Erlebnis —
> sein **Namensschild** (oder den Kamera-Clip). So ist jede:r dran, ohne dass die
> Drucker zum Engpass werden.

## Was du brauchst (alles vorhanden)
- 3D-Drucker (FDM) + **PLA**-Filament
- Slicer (z. B. PrusaSlicer, Cura) — kostenlos
- Python 3 (für den Namensschild-Generator; ohne Zusatzpakete)

---

## Teil 1 — Der Arm (vorab, durch Betreuer:innen)

Wir verwenden den **EEZYbotARM MK2** von Carlo Franciscone (offen, bewährt).
Die Dateien sind **nicht** im Repo enthalten — einmalig beziehen:

```bash
./hole_dateien.sh        # zeigt die Quellen; STLs nach ./eezybotarm/ legen
```
Quellen & Lizenz/Attribution: siehe [CREDITS.md](CREDITS.md).

**Druckeinstellungen (Richtwerte):**

| Einstellung | Wert |
|---|---|
| Material | PLA |
| Schichthöhe | 0,2 mm |
| Infill | 25–35 % (tragende Teile eher 35 %) |
| Wände/Perimeter | 3 |
| Stützen | nur wo nötig (Greifer-/Gelenkteile mit Überhang) |
| Ausrichtung | größte flache Fläche aufs Bett |

**Mengen:** ein Arm besteht aus mehreren Teilen (Basis, Drehturm, Ober-/Unterarm,
Greifer, Hebel). Pro Arm grob **150–250 g PLA** und **viele Stunden** Druck → für
**3 Arme rechtzeitig (1–2 Wochen) vorher** starten und über Nacht laufen lassen.

> Tipp: Bewegliche Gelenkbolzen leichtgängig drucken (etwas Spiel). Servohörner erst
> in Grundstellung montieren — Details zur Elektronik/Kalibrierung in
> [`../../docs/hardware.md`](../../docs/hardware.md).

---

## Teil 2 — Das Kinder-Teil (live im Workshop)

Klein, schnell (~10–20 min), **ohne Stützen** — perfekt fürs erste Erlebnis.

### A) Namensschild (empfohlen)
Eigenes Schild aus dem Namen erzeugen und drucken:

```bash
python3 namensschild.py MAX            # -> namensschild_MAX.stl
python3 namensschild.py "TEAM 1" ANNA  # auch mehrere auf einmal
```

Beispiel-Dateien liegen bei: `namensschild_MAX.stl`, `namensschild_ANNA.stl`,
`namensschild_TEAM-1.stl`. Im Slicer öffnen → PLA, 0,2 mm, 15–20 % Infill,
**keine Stützen** → drucken. Anschließend an die Station kleben/klemmen.

### B) Kamera-Clip (Alternative)
Hält die USB-Kamera an der drehenden Säule. Quelle: [`kamera_clip.scad`](kamera_clip.scad)
(parametrisch). Mit OpenSCAD exportieren:

```bash
openscad -o kamera_clip.stl kamera_clip.scad
```

---

## Drucktipps
- Erste Schicht zählt: Bett sauber/nivelliert, ggf. Brim für kleine Teile.
- Namensschild liegt flach → keine Stützen, kein Warping bei PLA.
- Mehrere Namensschilder passen gleichzeitig aufs Bett (Sammeldruck spart Zeit).

## Danach
Zusammenbau, Verkabelung (PCA9685 + **separates Servo-Netzteil**), Kalibrierung und
Inbetriebnahme: **[../../docs/hardware.md](../../docs/hardware.md)**.
Software-Überblick: **[../../README.md](../../README.md)**.
