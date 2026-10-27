# WiFi, Bluetooth and airplane mode

Open the bar icons or **System > Connectivity**. Opening a panel never changes
the selected backend or disconnects a device by itself.

## WiFi

The panel separates Connected, Known Networks and Other Networks. Choose an
available network to connect; password fields hide the password. Saved offline
networks remain visible without a fake signal percentage. Disconnect is on the
connected row; forgetting a saved network asks for confirmation.

The top section shows the network status, ping, the WiFi band, the IP address
and the gateway. The QR sharing control uses a supplied WiFi password and
keeps the generated image in memory. Enterprise credentials are not shared as
a personal-network QR code.

For enterprise networks, the panel supports PEAP/MSCHAPv2 and TTLS/PAP. Ask your
administrator for username, CA certificate and authentication-server domain;
do not disable certificate validation. Other authentication methods need
advanced provisioning. See [Network Backends](handbook:network-backends).

## Bluetooth

Toggle adapter power, scan, pair/connect, disconnect or forget devices. Connected,
known and newly discovered devices are grouped separately. Panel-started discovery
stops after 20 seconds or when the panel closes.

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
