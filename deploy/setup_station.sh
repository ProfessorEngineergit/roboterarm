#!/usr/bin/env bash
# roboterarm — eine Station standardisieren: fester Gerätename, SSH + avahi an,
# optional ein einheitliches Login-Passwort. So sind alle Boards bis auf die Nummer gleich.
#
#   sudo ./deploy/setup_station.sh 1                  # -> Hostname roboterarm-01
#   sudo ./deploy/setup_station.sh 2 MeinPasswort     # zusätzlich Login-Passwort setzen
#
# Hinweis: Hostnamen dürfen keine Unterstriche enthalten (sonst bricht .local/DNS),
# deshalb "roboterarm-01" statt "roboterarm_01".
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo ausführen:  sudo $0 $*" >&2
  exit 1
fi

NR="${1:?Stationsnummer angeben, z.B.:  sudo $0 1}"
NN="$(printf '%02d' "$((10#$NR))")"      # 1 -> 01, 2 -> 02 …
HOST="roboterarm-${NN}"
PW="${2:-}"
USER_REAL="${SUDO_USER:-$(id -un)}"

echo "-- Gerätename -> ${HOST} --"
hostnamectl set-hostname "${HOST}"
if grep -q '^127\.0\.1\.1' /etc/hosts 2>/dev/null; then
  sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t${HOST}/" /etc/hosts
else
  printf '127.0.1.1\t%s\n' "${HOST}" >> /etc/hosts
fi

echo "-- avahi (für ${HOST}.local) --"
command -v avahi-daemon >/dev/null 2>&1 || apt-get install -y avahi-daemon >/dev/null 2>&1 || \
  echo "  (avahi nicht installiert — .local evtl. nicht erreichbar, IP geht immer)"
systemctl enable --now avahi-daemon >/dev/null 2>&1 || true

echo "-- SSH aktivieren --"
systemctl enable --now ssh  >/dev/null 2>&1 || \
systemctl enable --now sshd >/dev/null 2>&1 || \
  echo "  (SSH-Dienst nicht gefunden — ggf. 'sudo apt-get install -y openssh-server')"

if [[ -n "${PW}" ]]; then
  echo "-- Login-Passwort für Benutzer '${USER_REAL}' setzen --"
  echo "${USER_REAL}:${PW}" | chpasswd
fi

echo
echo "== Station bereit: ${HOST} =="
echo "  SSH:   ssh ${USER_REAL}@${HOST}.local        (oder weiter per IP)"
[[ -z "${PW}" ]] && echo "  Tipp:  einheitliches Passwort setzen mit  passwd"
echo "  WLAN-Hotspot zusätzlich einrichten:  sudo ./deploy/hotspot.sh ${NR}"
