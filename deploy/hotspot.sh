#!/usr/bin/env bash
# roboterarm — Station als eigenen WLAN-Hotspot einrichten (offline-tauglich).
#
# Jede Station macht ein eigenes WLAN auf (z.B. "Roboterarm-1"). Die Kinder-Laptops
# verbinden sich direkt damit und öffnen die Oberfläche unter  http://arm1.local:8765
# (Rückfall-Adresse: http://10.42.0.1:8765). Kein Schulnetz nötig, keine IP-Tipperei.
#
# Voraussetzung: NetworkManager (Standard auf aktuellen Radxa-/Debian-Images) + WLAN.
#
# Aufruf:
#   sudo ./deploy/hotspot.sh 1                 # Station 1 → SSID Roboterarm-1, Host arm1
#   sudo ./deploy/hotspot.sh 2 MeinWLAN geheim # SSID + Passwort selbst wählen
#   sudo ./deploy/hotspot.sh --aus             # Hotspot wieder abschalten
set -euo pipefail

CON="roboterarm-hotspot"

# ---- Hotspot abschalten? ----
if [[ "${1:-}" == "--aus" || "${1:-}" == "--off" ]]; then
  nmcli connection down "$CON" 2>/dev/null || true
  nmcli connection modify "$CON" connection.autoconnect no 2>/dev/null || true
  echo "Hotspot '$CON' deaktiviert (Autostart aus). Board hängt wieder am normalen WLAN/LAN."
  exit 0
fi

NUMMER="${1:-1}"
NN="$(printf '%02d' "$((10#$NUMMER))")"   # 1 -> 01 …
SSID="${2:-Roboterarm-${NN}}"
PSK="${3:-roboterarm}"            # WPA2 braucht mind. 8 Zeichen
HOSTNAME_NEU="roboterarm-${NN}"  # gleiches Schema wie setup_station.sh

if [[ ${#PSK} -lt 8 ]]; then
  echo "FEHLER: Passwort muss mindestens 8 Zeichen haben (war: '${PSK}')." >&2
  exit 1
fi
if ! command -v nmcli >/dev/null 2>&1; then
  echo "FEHLER: NetworkManager (nmcli) nicht gefunden." >&2
  echo "  Installieren:  sudo apt-get install -y network-manager" >&2
  echo "  (Alternativ Hotspot manuell per hostapd+dnsmasq einrichten.)" >&2
  exit 1
fi
if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo ausführen:  sudo $0 $*" >&2
  exit 1
fi

# ---- WLAN-Gerät finden ----
WIFI_DEV="$(nmcli -t -f DEVICE,TYPE device | awk -F: '$2=="wifi"{print $1; exit}')"
if [[ -z "${WIFI_DEV}" ]]; then
  echo "FEHLER: Kein WLAN-Gerät gefunden (nmcli device)." >&2
  exit 1
fi
echo "WLAN-Gerät: ${WIFI_DEV}"

# ---- avahi für arm<N>.local ----
if ! command -v avahi-daemon >/dev/null 2>&1; then
  echo "-- avahi-daemon installieren (für ${HOSTNAME_NEU}.local) --"
  apt-get install -y avahi-daemon >/dev/null 2>&1 || \
    echo "  (avahi-Installation übersprungen — .local funktioniert evtl. nicht, IP geht immer)"
fi
systemctl enable --now avahi-daemon 2>/dev/null || true

# ---- Hostname setzen (→ ${HOSTNAME_NEU}.local) ----
echo "-- Hostname → ${HOSTNAME_NEU} --"
hostnamectl set-hostname "${HOSTNAME_NEU}" || true

# ---- Hotspot-Verbindung (neu) anlegen ----
echo "-- Hotspot '${SSID}' einrichten --"
nmcli connection delete "$CON" 2>/dev/null || true
nmcli connection add type wifi ifname "${WIFI_DEV}" con-name "$CON" \
  autoconnect yes ssid "${SSID}" >/dev/null
nmcli connection modify "$CON" \
  802-11-wireless.mode ap \
  802-11-wireless.band bg \
  ipv4.method shared \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "${PSK}" \
  connection.autoconnect yes \
  connection.autoconnect-priority 100
nmcli connection up "$CON"

IP="$(nmcli -g IP4.ADDRESS device show "${WIFI_DEV}" 2>/dev/null | head -n1 | cut -d/ -f1)"
echo
echo "== Hotspot aktiv =="
echo "  WLAN-Name (SSID): ${SSID}"
echo "  Passwort:         ${PSK}"
echo "  Oberfläche:       http://${HOSTNAME_NEU}.local:8765   (Rückfall: http://${IP:-10.42.0.1}:8765)"
echo "  Startet künftig automatisch beim Booten."
echo
echo "Abschalten:  sudo $0 --aus"
