# Mitmachen

Danke fürs Interesse! Dieses Projekt ist eine Bildungs-Plattform — Klarheit und
kindgerechte, deutschsprachige API stehen über Cleverness.

## Entwicklung

Alles läuft ohne Hardware in **Simulation**:

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 examples/find_ball.py
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 service/robot_service.py
```

## Tests

```bash
ROBOTERARM_BACKEND=sim PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Bitte neue Funktionen mit einem Test in `tests/` absichern (Simulation, kein Hardware-Zwang).

## Aufbau

- `roboterarm/` — die Bibliothek (die *eine* veröffentlichte API). Hardware vs. Simulation
  wird per Backend-Factory entschieden; neue Fähigkeiten so kapseln, dass beide Pfade existieren.
- `service/` — Standardbibliothek-HTTP-Dienst (kein Flask), CORS offen für Scratch.
- `web/` — Vanilla-JS-Oberfläche, **offline** (keine CDNs).
- `scratch/` — Scratch-3-Extension (ruft den Dienst).

## Stil

- Deutsch in API, Kommentaren und UI (Zielgruppe: deutschsprachige Schüler:innen).
- Schwergewichtige Importe (numpy/cv2/tflite) **lazy** halten, damit der Sim-Kern leicht bleibt.
- Keine neuen Pflicht-Abhängigkeiten ohne guten Grund.
