# Security and locking

**SUPER + M** locks now. Click the Idle Lock icon on the left of the bar (after
AI Usage) to turn automatic idle locking on or off; its tooltip shows which.
When on, the screen locks after 15 minutes idle, turns off after 30 and the
computer sleeps after 60. The Control Center has the same Idle Lock toggle and
a Lock button.

Twenty seconds before locking, supported displays dim to about 30% of their previous brightness (never zero). Activity restores the exact previous level, even after locking; turning Idle Lock off also restores it. External monitors without DDC brightness control are skipped.

## Password and alternative authentication

**System > Security > Update Password** changes your account password.
Fingerprint and FIDO2 have their own enrollment/enable workflows. A FIDO2
security key is a physical security device, not a laptop fingerprint reader.
Enroll first, then enable authentication. The helper backs up PAM settings;
keep a working password and a way to reach a TTY.

Return to Password Authentication restores password-only behavior. These
changes affect supported lockscreen/login/sudo PAM services; hardware support
and installed helpers are required. Fingerprint authentication may delay a
password prompt briefly. Reading this page does not modify PAM.

## Firewall

New installations start with the firewall on. It refuses incoming connections
except replies to something your computer started, local name discovery, and the
sharing apps Eitr installs: KDE Connect (ports 1714-1764) and LocalSend (53317).
Virtual machines and containers on your computer still reach it, and outgoing
traffic is never filtered. When SSH is enabled, SSH stays reachable too.

**System > Security > Firewall** shows whether it is on and switches it after you
confirm. Computers set up before the firewall existed start with it off. To let
another app accept connections, add a file to `/etc/eitr/firewall.d/`, for
example `game.nft` containing:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

then turn the firewall off and on again.

## Disk encryption and TPM

Disk encryption is an installer choice. TPM Disk Unlock can add a TPM2 slot to
a supported existing LUKS2 root; it is not automatically enrolled by the
installer. Keep a passphrase/recovery key offline. Never save it in screenshots
or repository files. Firmware/Secure Boot changes can require the passphrase
at the next boot.

Read [Recovery & Snapshots](handbook:recovery) before changing authentication or
TPM setup. [Secure Boot](handbook:secure-boot) is an advanced, manual process:
EITR does not enroll firmware keys or sign boot files for you. A mistake can
prevent booting or even reaching firmware setup on some hardware.
