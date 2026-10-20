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
