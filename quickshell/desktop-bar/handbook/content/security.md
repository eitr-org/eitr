# Security and locking

**SUPER + M** locks now. Click the Idle Lock icon on the left of the bar (after
AI Usage) to turn automatic idle locking on or off; its tooltip shows which.
When on, the screen locks after 15 minutes idle, turns off after 30 and the
computer sleeps after 60. The Control Center has the same Idle Lock toggle and
a Lock button.

Twenty seconds before locking, supported displays dim to about 30% of their previous brightness (never zero). Activity restores the exact previous level, even after locking; turning Idle Lock off also restores it. External monitors without DDC brightness control are skipped.

## Password and alternative authentication

**Settings > Users > Change password** changes your account password and keeps the login keyring opening with it.
Fingerprint and FIDO2 Security Key have their own enrollment/enable workflows. A FIDO2
security key is a physical security device, not a laptop fingerprint reader.
Enroll first, then enable authentication. The helper backs up PAM settings;
keep a working password and a way to reach a TTY.

Return to Password Authentication restores password-only behavior. These
changes affect supported lockscreen/login/sudo PAM services; hardware support
and installed helpers are required. Fingerprint authentication may delay a
password prompt briefly. Reading this page does not modify PAM.

## Administrator password prompts

When an app or Eitr itself needs administrator rights (installing software, changing
system settings), a password prompt drawn in the bar's theme covers the screen you are
using. It shows what is asking, which account authenticates (with a choice when more
than one may), and Request details with the polkit action. Enter authenticates, Escape
or Cancel declines; clicking beside the prompt does nothing. A wrong password shows an
error and lets you try again. Several requests wait their turn, one prompt at a time.
The password goes straight to the system and is never saved or logged.

If the bar cannot provide this prompt shortly after login, KDE's password dialog takes
its place for the session, so administrator requests keep working.

## Firewall

New installations start with the firewall on. It refuses incoming connections
except replies to something your computer started, local name discovery, and the
sharing apps Eitr installs: KDE Connect (ports 1714-1764) and LocalSend (53317).
Virtual machines and containers on your computer still reach it, and outgoing
traffic is never filtered. When SSH is enabled, SSH stays reachable too.

**Settings > Security > Protection > Firewall** shows whether it is on and switches it after you
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

## User accounts

**Settings > Users > Create User…** creates a separate login. Enter a username, optional full name, account type and password, then review and press Enter to create it. Esc cancels before applying. Standard accounts cannot use sudo; Administrator accounts join wheel and receive a password-protected sudo rule.

The new home contains no files from your account. At its first Hyprland login through UWSM, Eitr runs the installer’s per-user desktop setup and adopts the package layout under the new user’s identity. Shell setup may require internet access. Failed setup keeps its pending marker for the next login; successful setup runs only once. Account creation failures leave an incomplete account locked and expired for manual review.

Administrators see **Users** and **Manage** tabs in Settings > Users; standard accounts see only the Users list. An Administrator belongs to wheel and has an Eitr sudo rule; a Standard account has neither. Manage can create accounts, change their type, set another account’s password, and remove accounts. Each action opens a confirmation sheet, then a task terminal: Enter continues and Esc cancels. Password resets ask for the new password twice in the terminal; the other account’s login keyring cannot be updated and keeps its old password. Use Change password on Users for your own account. Removal keeps the home folder by default; choose Delete home folder to delete its files. You cannot remove yourself, an account with an active login session, or the last administrator; the last administrator also cannot be demoted. Only human accounts (UID 1000–65533) can be managed. The list refreshes when you return from the terminal.

Accounts whose primary group is wheel cannot be demoted here; change their primary group through manual administration first.

## Profile pictures

Settings > Users lists every account on this PC. Click your picture there to change it, or use the trash icon below it to remove it. See [Settings](handbook:system) for choosing an image and adjusting its crop. The Control Center only displays your picture.
