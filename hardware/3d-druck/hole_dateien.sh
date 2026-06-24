#!/usr/bin/env bash
# Bezugsquellen für die EEZYbotARM-MK1-Druckdateien.
# Die Originaldateien werden NICHT in diesem Repo mitgeliefert (siehe CREDITS.md:
# Urheber Carlo Franciscone, Lizenz CC BY-NC-SA). Bitte einmalig herunterladen
# und in den Ordner ./eezybotarm legen.
set -e
ZIEL="$(cd "$(dirname "$0")" && pwd)/eezybotarm"
mkdir -p "$ZIEL"

cat <<EOF
EEZYbotARM MK1 — Druckdateien beziehen
======================================
Bitte die STL-Dateien von einer der Originalquellen laden und nach
  $ZIEL
entpacken:

  Thingiverse : https://www.thingiverse.com/thing:1015238
  Projektseite: http://www.eezyrobots.it/eba_mk1.html
  CAD-Quelle  : Onshape (Link auf der Projektseite)

Lizenz/Attribution: siehe CREDITS.md (nicht-kommerzielle, schulische Nutzung).
Danach Druckliste & Einstellungen in README.md befolgen.
EOF
