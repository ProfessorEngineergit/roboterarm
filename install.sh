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
  sudo apt-get install -y python3 python3-pip python3-venv i2c-tools libgl1 || true
fi

# 2) Python-Abhängigkeiten
echo "-- Python-Abhängigkeiten --"
python3 -m pip install --upgrade pip
python3 -m pip install -r "$HIER/requirements.txt"
python3 -m pip install -e "$HIER" 2>/dev/null || echo "(editierbare Installation übersprungen)"

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
  echo "Dienst aktiv. Oberfläche: http://<board-ip>:8765/"
fi

cat <<EOF

== Fertig ==
Manuell starten:   ROBOTERARM_BACKEND=hardware PYTHONPATH="$HIER" python3 "$HIER/service/robot_service.py"
Kalibrieren:       PYTHONPATH="$HIER" python3 "$HIER/calibrate.py"
Test (Simulation): ROBOTERARM_BACKEND=sim PYTHONPATH="$HIER" python3 "$HIER/examples/find_ball.py"
Doku:              docs/hardware.md
EOF
