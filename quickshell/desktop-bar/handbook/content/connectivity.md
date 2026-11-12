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

To choose the WiFi backend, use Settings > Connections > Wi-Fi > WiFi backend; Walker > Settings > Devices > Connections > Network Backend is an alternative. Read [Network Backends](handbook:network-backends) before switching. The saved choice applies after reboot and leaves the current connection running.

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

Walker has no VPN menu. WireGuard and NetworkManager VPN are planned as plugins (Install > Plugins). Tailscale is the official Tailscale plugin (Themes & Plugins > Plugins); see [Remote access](handbook:remote-access).
