#!/usr/bin/env bash
# Bezugsquellen für die EEZYbotARM-MK2-Druckdateien.
# Die Originaldateien werden NICHT in diesem Repo mitgeliefert (siehe CREDITS.md:
# Urheber Carlo Franciscone, Lizenz CC BY-NC-SA). Bitte einmalig herunterladen
# und in den Ordner ./eezybotarm legen.
set -e
ZIEL="$(cd "$(dirname "$0")" && pwd)/eezybotarm"
mkdir -p "$ZIEL"

cat <<EOF
EEZYbotARM MK2 — Druckdateien beziehen
======================================
Bitte die STL-Dateien von einer der Originalquellen laden und nach
  $ZIEL
entpacken:

  Thingiverse : https://www.thingiverse.com/thing:1454048
  Cults3D     : https://cults3d.com/en/3d-model/tool/eezybotarm-mk2
  Projektseite: http://www.eezyrobots.it/eba_mk2.html
  CAD-Quelle  : Onshape (Link auf der Projektseite)

Lizenz/Attribution: siehe CREDITS.md (nicht-kommerzielle, schulische Nutzung).
Danach Druckliste & Einstellungen in README.md befolgen.
EOF
