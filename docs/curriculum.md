# 3-Tage-Workshop (Kurzfassung)

Zielgruppe gemischt (Grundschule bis Oberstufe); 3 Arme, je 2–4 Kinder. Die drei Ebenen
(Scratch → EduBlocks/Python → voller Python) laufen parallel, jedes Kind nach Tempo.

## Tag 1 — Bauen & erstes Lebenszeichen
- Intro, Demo-Arm vorführen, Teams (Bau / Code / Doku).
- 3D-Druck-Erlebnis: jedes Kind druckt ein kleines eigenes Teil (Rest ist vorgedruckt).
- Zusammenbau, Servos + PCA9685 verkabeln, Kamera montieren.
- `install.sh`, `calibrate.py` → Home/Grenzen je Station.
- **Tagessieg:** „Manuell"-Tab — Arm winkt.

## Tag 2 — Programmieren + KI
- **Scratch:** Sequenzen, Schleifen — winken, Pick-and-Place, „Tanz".
- **Brücke:** dasselbe in EduBlocks/Thonny als Python sehen & anpassen (Rosetta-Tabelle in
  [scratch_edublocks.md](scratch_edublocks.md)).
- **KI-Studio:** beliebiges Objekt fotografieren → Klassen anlegen → trainieren → live erkennen;
  Oberstufe: Train/Test, **Confusion-Matrix**.
- Routine „finden → zentrieren → greifen → ablegen".
- **Tagessieg:** Arm holt selbstständig ein gewähltes Objekt.

## Tag 3 — Projekte, Videos, Demo-Day
- Eigenes Mini-Projekt (Sortieren, Wächter, Choreografie, …).
- Doku (README/Bericht), Demo-Video drehen.
- Demo-Day mit Bewertungsraster; Portfolio sichern.

## Software-Bezug
- **Bewegung/Greifer/Posen:** Tab *Manuell*, `arm.basis/…`, `arm.pose_*`.
- **Sehen:** Tab *Vision*, `arm.finde/sieht`.
- **KI:** Tab *KI-Studio*, `arm.lerne/erkenne`, `arm.modell.bewerte`.
- **Eigener Code:** Tab *Code* (Editor + Ausführung) oder Thonny, `examples/`.

> Der ausführliche didaktische Plan (Hardware, Stückliste, Differenzierung, Demo-Day-Raster,
> Risiken) liegt im Workshop-Plandokument; dieses Repo ist die zugehörige Software.
