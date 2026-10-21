#!/usr/bin/env bash
# roboterarm — Installation & Inbetriebnahme (Radxa ROCK Pi 4 / Raspberry Pi, Debian/Armbian).
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"
echo "== roboterarm Installation =="
echo "Projektordner: $HIER"

# 1) Systempakete
if command -v apt-get >/dev/null 2>&1; then
  echo "-- Systempakete (apt) --"
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv i2c-tools libgl1 \
                          network-manager avahi-daemon || true
fi

# 2) Python-Abhängigkeiten (in virtualenv, kompatibel mit Debian Bookworm)
echo "-- Python-Abhängigkeiten (venv: $HIER/.venv) --"
python3 -m venv "$HIER/.venv"
"$HIER/.venv/bin/pip" install --upgrade pip -q
"$HIER/.venv/bin/pip" install -r "$HIER/requirements.txt"
"$HIER/.venv/bin/pip" install -e "$HIER" -q 2>/dev/null || echo "(editierbare Installation übersprungen)"

# 2b) Skripte ausführbar machen
chmod +x "$HIER/deploy/"*.sh 2>/dev/null || true

# 3) I2C aktivieren & Servotreiber suchen
echo "-- I2C --"
if command -v raspi-config >/dev/null 2>&1; then sudo raspi-config nonint do_i2c 0 || true; fi
BUS="${I2C_BUS:-7}"
echo "Suche PCA9685 (erwartet 0x40) auf Bus $BUS:"
sudo i2cdetect -y "$BUS" 2>/dev/null || echo "  (i2cdetect fehlgeschlagen — Bus/Verkabelung prüfen; Bus per I2C_BUS=… vorgeben)"

# 4) Optionaler Autostart über systemd
read -rp "Dienst beim Booten automatisch starten (systemd)? [j/N] " a || a=N
if [[ "${a:-N}" =~ ^[jJyY]$ ]]; then
  SVC=/etc/systemd/system/roboterarm.service
  sudo cp "$HIER/deploy/roboterarm.service" "$SVC"
  sudo sed -i "s#__ROOT__#$HIER#g; s#__USER__#${SUDO_USER:-$USER}#g" "$SVC"
  sudo systemctl daemon-reload
  sudo systemctl enable --now roboterarm
  echo "Dienst aktiv (Autostart)."
fi

# 5) Optionaler WLAN-Hotspot (jede Station ein eigenes WLAN, offline-tauglich)
read -rp "Diese Station als eigenen WLAN-Hotspot einrichten? [j/N] " h || h=N
if [[ "${h:-N}" =~ ^[jJyY]$ ]]; then
  read -rp "  Stationsnummer (1/2/3 …) [1]: " NR || NR=1
  sudo bash "$HIER/deploy/hotspot.sh" "${NR:-1}"
fi

cat <<EOF

== Fertig ==
Oberfläche:        http://10.42.0.1:8765/   (am Hotspot) bzw. http://roboterarm-<N>.local:8765/
                   Vier Reiter: Regler · Eigene Blöcke · Scratch · Python · roter NOT-AUS oben rechts
Manuell starten:   ROBOTERARM_BACKEND=hardware "$HIER/.venv/bin/python" "$HIER/service/robot_service.py"
Kalibrieren:       "$HIER/.venv/bin/python" "$HIER/calibrate.py"
Test (Simulation): ROBOTERARM_BACKEND=sim "$HIER/.venv/bin/python" "$HIER/service/robot_service.py"
Hotspot später:    sudo "$HIER/deploy/hotspot.sh" 1     (Abschalten: --aus)
Scratch offline:   ./deploy/turbowarp_holen.sh         (einmalig mit Internet, für den Scratch-Tab)
Doku Betreuer:     docs/hardware.md      Doku Kinder: docs/anleitung_kinder.md
EOF
