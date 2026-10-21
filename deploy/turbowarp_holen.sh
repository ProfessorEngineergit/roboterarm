#!/usr/bin/env bash
# roboterarm — lokale Scratch-Oberfläche (TurboWarp) ins Board legen.
#
# Der Scratch-Tab der Weboberfläche lädt eine *lokal* ausgelieferte TurboWarp-
# Oberfläche unter  web/turbowarp/ . Damit läuft Scratch im Workshop komplett
# OFFLINE (eigener Hotspot, kein Internet). Dieses Skript muss EINMALIG mit
# Internet laufen — danach nie wieder.
#
# Aufruf:
#   ./deploy/turbowarp_holen.sh
#
# Schon ein fertiges Build (build.zip/ build-Ordner) vorhanden? Dann ohne Bauen:
#   TURBOWARP_DIST_URL="https://…/turbowarp-build.tar.gz" ./deploy/turbowarp_holen.sh
set -euo pipefail

HIER="$(cd "$(dirname "$0")/.." && pwd)"
ZIEL="$HIER/web/turbowarp"
EXT_REL="roboterarm_extension.js"

echo "== TurboWarp lokal einrichten -> $ZIEL =="
mkdir -p "$ZIEL"

# ---- Variante A: fertiges Build per URL (schnell, kein Node nötig) ----
if [[ -n "${TURBOWARP_DIST_URL:-}" ]]; then
  echo "-- Lade fertiges Build von: $TURBOWARP_DIST_URL"
  TMP="$(mktemp -d)"
  curl -fL "$TURBOWARP_DIST_URL" -o "$TMP/tw.tar.gz"
  tar -xzf "$TMP/tw.tar.gz" -C "$TMP"
  # Ordner mit index.html finden und dessen Inhalt kopieren
  SRC="$(dirname "$(find "$TMP" -name index.html | head -n1)")"
  [[ -n "$SRC" ]] || { echo "FEHLER: keine index.html im Archiv gefunden." >&2; exit 1; }
  cp -r "$SRC"/. "$ZIEL"/
  rm -rf "$TMP"
  echo "== Fertig. Scratch-Tab ist jetzt offline nutzbar. =="
  exit 0
fi

# ---- Variante B: aus Quelltext bauen (braucht git + node + npm) ----
for cmd in git node npm; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "FEHLER: '$cmd' fehlt. Bitte installieren:" >&2
    echo "  sudo apt-get install -y git nodejs npm" >&2
    echo "  (Node >= 18 empfohlen — auf dem ROCK Pi dauert der Build einige Minuten.)" >&2
    exit 1
  }
done

BUILD="${TURBOWARP_SRC:-$HOME/scratch-gui}"
if [[ ! -d "$BUILD/.git" ]]; then
  echo "-- TurboWarp/scratch-gui klonen nach $BUILD"
  git clone --depth 1 https://github.com/TurboWarp/scratch-gui "$BUILD"
else
  echo "-- scratch-gui vorhanden, hole Updates"
  git -C "$BUILD" pull --ff-only || true
fi

echo "-- Abhängigkeiten installieren (dauert)"
( cd "$BUILD" && npm install --no-audit --no-fund )

echo "-- Bauen (statische Oberfläche)"
( cd "$BUILD" && NODE_OPTIONS="--max-old-space-size=2048" npm run build )

[[ -f "$BUILD/build/index.html" ]] || { echo "FEHLER: Build fehlgeschlagen (keine build/index.html)." >&2; exit 1; }
echo "-- Build nach $ZIEL kopieren"
cp -r "$BUILD/build/." "$ZIEL"/

echo
echo "== Fertig. =="
echo "  Scratch-Tab lädt jetzt /turbowarp/ direkt vom Board — komplett offline."
echo "  Die Roboterarm-Blöcke werden automatisch über $EXT_REL eingebunden."
