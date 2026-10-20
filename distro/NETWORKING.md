# Network backends

System > Connectivity > Network Backend selects iwd (the fresh-install default) or
NetworkManager with wpa_supplicant. Both use systemd-resolved for DNS. The
shared WiFi panel detects the running backend, not the saved next-boot choice.
The current connection is not restarted: the root-owned helper prepares files
and enables/disables boot services without `--now`, then asks whether to reboot.
Declining leaves the choice queued until your next reboot.

Saved WiFi profiles remain in each backend's own storage. They are not deleted
or automatically converted; reconnect on the first switch, and switching back
reuses the old profiles. Review custom static IP, VPN, bridge, networkd files or
other network managers before switching. Masked services, another active manager
or a custom resolver are refused rather than silently replaced. Original managed
files and service enable states are saved privately under
`/var/lib/eitr/network-backend`; Restore Original Network Configuration restores
them for the next boot, without stopping current networking.

The `eitr-desktop` package includes both backends and the root-owned helper
`/usr/lib/eitr/eitr-network`; install the package rather than copying the helper
by hand (see the distro README). A helper installed by hand earlier blocks the
package install until `distro/system/adopt-unowned-files.sh --apply` archives it.
Never elevate a helper from a user-writable path. Installing the helper does not
select a backend.

## Enterprise WiFi

The panel supports PEAP/MSCHAPv2 and TTLS/PAP, with username, optional anonymous
identity, password, authentication server domain and a PEM CA certificate path.
Ask the network administrator for these settings. Server certificate validation
is mandatory; EAP-TLS/client certificates, SIM/AKA and other advanced methods
still require external provisioning. Impala remains an optional fallback for
these configurations; do not remove it based on common-method support alone.

Credentials travel over process stdin and D-Bus, never command-line arguments.
NetworkManager stores its normal connection profile; iwd provisioning uses
PolicyKit authentication and a private root-owned `.8021x` profile with the CA
embedded. Existing enterprise profiles are not overwritten: forget the profile
explicitly before replacing it. Only root-owned, non-group/world-writable
helpers are accepted. No real backend switch, WiFi connection or enterprise
authentication is exercised by automated tests; validate both on spare hardware
or an isolated VM before describing them as hardware-tested.
