# WiFi, Bluetooth and airplane mode

Open Settings > Connections and choose Wi-Fi or Bluetooth. The bar icons open quick panels for the same devices. Opening either view does not switch the backend or disconnect anything.

## Connect to Wi-Fi

Open Settings > Connections > Wi-Fi, turn Wi-Fi on and choose a network under Other networks. Enter its password if asked. Use Scan to look again. Connected network shows the current connection; Known networks keeps saved networks, including offline ones. Disconnect ends the connection; Forget removes a saved network after confirmation. Progress and errors appear beside the network.

The top section shows the network status, ping, the WiFi band, the IP address
and the gateway. The QR sharing control uses a supplied WiFi password and
keeps the generated image in memory. Enterprise credentials are not shared as
a personal-network QR code.

For enterprise networks, the panel supports PEAP/MSCHAPv2 and TTLS/PAP. Ask your
administrator for username, CA certificate and authentication-server domain;
do not disable certificate validation. Other authentication methods need
advanced provisioning. See [Network Backends](handbook:network-backends).

To choose the WiFi backend, use Settings > Connections > Wi-Fi > WiFi backend; Walker > Settings > Connectivity > Network Backend is an alternative. Read [Network Backends](handbook:network-backends) before switching. The saved choice applies after reboot and leaves the current connection running.

## Pair a Bluetooth device

Open Settings > Connections > Bluetooth and turn Bluetooth on. Choose Scan, then select a device to pair and connect. Connected devices, Known devices and Other devices are separate lists. Use Show unnamed devices if your device has no name. Disconnect keeps the pairing; Forget removes it. Scanning stops after 20 seconds or when you leave the page or close the panel.

Pairing may need a PIN or confirmation agent. EITR's current desktop relies on
the Blueman agent for those dialogs; reconnecting an already-paired device does
not prove new-pairing support. Keep that agent until a PIN/confirmation pairing
has been tested. Clean-install pairing-agent coverage remains a known check.

## Airplane mode

Control Center > General blocks WiFi/Bluetooth using rfkill. Turning it off
restores only the radios it originally blocked. Hardware or externally applied
blocks are not silently overridden. Enable a radio individually if needed.

## VPN

Open Install > VPN for Tailscale, WireGuard or NetworkManager VPN. Tailscale keeps its existing remote-access panel and setup flow.

WireGuard installs the official `wireguard-tools` package through the normal pending-update check. Choose Import a WireGuard configuration…, enter a profile name and the full path to a `.conf` file, then review the name, endpoints and peer count. Keys are never shown. Executable hooks and SaveConfig are refused. On NetworkManager the profile is imported there; on iwd it is saved privately under `/etc/wireguard` for wg-quick. Existing wg-quick profiles are never overwritten.

NetworkManager VPN installs `networkmanager-openvpn` and `networkmanager-openconnect`. WireGuard support is built into NetworkManager and needs no separate plugin. On iwd this workflow explains the requirement and opens the existing backend choice; it never switches backends itself. See [Network Backends](handbook:network-backends). Import a VPN file… accepts `.ovpn` for OpenVPN and other provider files supported by the OpenConnect importer. Unsupported files fail without displaying their contents.

Imports remain disconnected unless you explicitly choose Connect after import. Automatic connection at boot is disabled. Reopen WireGuard or NetworkManager VPN and choose Connect or Disconnect with the saved profile name. No VPN toggle is added to Control Center. Import and connection behavior has automated mock coverage; real VPN connectivity has not been verified on hardware.
