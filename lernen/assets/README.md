# Bilder & Grafiken für die Lern-Website

Die Seite nutzt bewusst **scharfe SVG-Mockups** (Terminal-Fenster, Windows-Dialoge) statt Fotos —
die sind gestochen scharf, on-theme und funktionieren **komplett offline**.

## Echte Screenshots ergänzen (optional)

Willst du echte Fotos/Screenshots zeigen, leg sie hier ab und binde sie ein, z. B.:

```html
<img src="assets/terminal-windows.png" alt="Terminal unter Windows öffnen"
     style="width:100%;border-radius:12px;border:1px solid var(--outline);">
```

Empfohlene Aufnahmen (jeweils ~1200 px breit, PNG):

| Datei | Motiv |
|---|---|
| `terminal-windows.png` | Windows: „Ausführen"-Dialog mit `cmd` |
| `terminal-app.png`     | Windows-Terminal-App geöffnet |
| `terminal-mac.png`     | Mac: Spotlight → Terminal |
| `ssh-arm.png`          | Per `ssh` am Roboterarm angemeldet |

Tipp: Screenshots mit großem Schriftgrad aufnehmen (im Terminal `Strg`+`+`), damit Kinder alles lesen.
Wo ein `<img>` steht, kannst du das danebenliegende `<svg>`-Mockup entfernen — oder beides lassen.
