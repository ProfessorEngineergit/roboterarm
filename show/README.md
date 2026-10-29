# Show-Modus — mehrere Arme tanzen synchron

Der **Dirigent** (`dirigent.py`) schickt jeden Choreografie-Schritt *gleichzeitig* an
alle Arme über die schon vorhandene HTTP-API. Er läuft mit purem `python3` — auf
deinem **Mac/Laptop** oder auf einem der Boards.

## Voraussetzung: alle Arme in EINEM Netz

Im normalen Workshop macht jedes Board sein eigenes, abgeschottetes WLAN — dann können
sie sich nicht sehen. Für die Show müssen alle im **selben** Netz hängen. Zwei Wege:

### Variante A — ein kleiner (Reise-)Router  ← am einfachsten
1. Router einschalten, ein WLAN aufmachen (egal welcher Name).
2. Auf **jedem** Board den eigenen Hotspot ausschalten und ins Router-WLAN gehen:
   ```bash
   sudo ./deploy/hotspot.sh --aus
   sudo nmcli device wifi connect "<ROUTER-WLAN>" password "<PW>"
   ```
3. Dein Laptop verbindet sich mit demselben Router-WLAN.
4. Adressen sind dann `roboterarm-01.local`, `roboterarm-02.local`, `roboterarm-03.local`.

### Variante B — ein Board ist der Haupt-Hotspot (kein Extra-Gerät)
1. **Board 1** bleibt Hotspot (`Roboterarm-01`, läuft schon).
2. **Board 2 + 3** ins WLAN von Board 1 holen:
   ```bash
   sudo ./deploy/hotspot.sh --aus
   sudo nmcli device wifi connect "Roboterarm-01" password "roboterarm"
   ```
3. Dein Laptop verbindet sich ebenfalls mit `Roboterarm-01`.
4. Board 1 ist `10.42.0.1`; Board 2 + 3 bekommen eine `10.42.0.x` (oder per
   `roboterarm-02.local` / `-03.local` erreichbar).

> Adressen prüfen: vom Laptop `ping roboterarm-02.local`. Wenn `.local` nicht geht,
> die IP nehmen (auf dem Board: `hostname -I`).

## Show starten

```bash
# Demo abspielen (Adressen stehen in der JSON)
python3 show/dirigent.py show/tanz_demo.json

# Adressen direkt vorgeben (überschreibt die JSON)
python3 show/dirigent.py show/tanz_demo.json --arme roboterarm-01.local roboterarm-02.local

# Dreimal hintereinander, etwas langsamer
python3 show/dirigent.py show/tanz_demo.json --wiederhole 3 --tempo 3
```

**Strg+C** löst sofort bei **allen** Armen NOT-AUS aus (`/api/panik`).

## Eigene Choreografie schreiben

Kopiere `tanz_demo.json` und passe `schritte` an. Ein Schritt ist eines davon:

| Schritt | Wirkung |
|---|---|
| `{"home": true}` | alle in Grundstellung |
| `{"gelenk": "basis", "winkel": 45}` | ein Gelenk auf Winkel (`basis` 0–180, `schulter`/`ellbogen` 20–160, `greifer` 30–110) |
| `{"greifer": "auf"}` / `{"greifer": "zu"}` | Greifer öffnen/schließen |
| `{"pose": "winken"}` | gespeicherte Pose anfahren (muss auf **jedem** Board unter dem Namen existieren) |
| `{"tempo": 8}` | Grad pro Schritt (größer = schneller/ruckiger) |
| `{"warte": 0.5}` | nur Pause in Sekunden |
| `{"per_arm": { "roboterarm-01.local": {...}, ... }}` | jeder Arm ein eigener Befehl (echte Choreo) |

Jeder Schritt darf zusätzlich `"warte": <Sekunden>` haben — so lange wird vor dem
nächsten Schritt gewartet.

> **Tipp:** Posen sind am bequemsten — in der Weboberfläche pro Arm ein paar Posen
> mit gleichem Namen speichern (z. B. `winken`, `hoch`, `tief`), dann in der Choreo
> nur noch `{"pose": "winken"}` aneinanderreihen.
