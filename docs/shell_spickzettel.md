# 🐢 Shell-Spickzettel — Terminal-Schule

Zum Ausdrucken oder Danebenlegen. Die interaktive Version: **`/lernen/`** (am Board:
`http://10.42.0.1:8765/lernen/`) mit Übungs-Trainer.

## Terminal öffnen
- **Windows:** `Windows-Taste + R` → `cmd` → Enter. Oder Start → „Terminal".
- **Mac:** `Cmd + Leertaste` → `Terminal` → Enter.
- **Am Roboter:** `ssh radxa@roboterarm-01.local` (Passwort fragen).

## Die wichtigsten Befehle

| Befehl | Bedeutung | Beispiel |
|---|---|---|
| `pwd` | Wo bin ich? (print working directory) | `pwd` |
| `ls` | Was ist hier? (list) | `ls` · `ls roboterarm` |
| `cd ordner` | In einen Ordner gehen (change directory) | `cd roboterarm` |
| `cd ..` | Einen Ordner zurück | `cd ..` |
| `cd` oder `cd ~` | Nach Hause | `cd` |
| `cat datei` | Datei-Inhalt anzeigen | `cat README.md` |
| `mkdir name` | Neuen Ordner anlegen | `mkdir posen` |
| `touch name` | Leere Datei anlegen | `touch idee.txt` |
| `rm datei` | Datei löschen (`rm -r` für Ordner) | `rm idee.txt` |
| `clear` | Bildschirm leeren | `clear` |
| `help` | Hilfe (im Trainer) | `help` |

> 💡 **Tab-Taste** vervollständigt Namen automatisch. **Pfeil hoch** holt den letzten Befehl zurück.

## Roboterarm — alle Befehle

```bash
# 1) Projekt holen & einrichten
git clone https://github.com/ProfessorEngineergit/roboterarm ~/roboterarm
cd ~/roboterarm
./install.sh

# 2) Server starten  ->  Browser: http://10.42.0.1:8765
cd ~/roboterarm
python3 service/robot_service.py

# 3) Neueste Version laden
cd ~/roboterarm
git pull
sudo systemctl restart roboterarm

# 4) Servos kalibrieren (oder im Web-Tab "⚙ Kalibrieren")
python3 calibrate.py

# 5) Station als WLAN-Hotspot
sudo ./deploy/hotspot.sh 1
```

## 🎬 Video (braucht Internet)
- Deutsch, 20 Min: <https://www.youtube.com/watch?v=4xjaPQCiBfM>
- English, Crash Course (Traversy): <https://www.youtube.com/results?search_query=Traversy+Command+Line+Crash+Course>
