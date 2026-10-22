# Finding your way around System

Open **SUPER + F > System**. Actions are grouped alphabetically; global search
still finds them directly, without making you navigate every group.

## Connectivity

**Bluetooth**, **Network Backend**, **WiFi**. The device entries open the same
panels as the bar. Backend selection prepares the next boot, not a live restart.

## Devices & Input

**Audio**, **Battery Charge Limit**, **Display**, **Keyboard**, **Lighting**,
**Microphone**. Charge-limit controls require supported laptop firmware. Display
contains brightness, Night Light, monitor selection and supported laptop power
profiles.

**Lighting** decides whether theme changes recolour fans, keyboards and other
devices that OpenRGB controls. It is off by default, so EITR leaves your
lighting alone; choose **Follow Theme** to give them the theme's colour now and
at every theme change.

## Information

**About**, **AI Usage**, **Hardware**, **Report a Problem**, **Weather**. About
opens the EITR system summary; Report a Problem collects a private report you
read before sending. The others use native panels. Calendar and Workspace Overview remain
available from the bar and global search rather than crowding this menu. Search
for **Ragnarök** to let Fenrir bite the screen; click or Escape ends it early.

## Maintenance

**Cleanup**, **Factory Reset**, **Snapshots**, **Update**. Update offers
System Update and Update Channel. Factory Reset is destructive and
requires two warnings; read [Factory Reset](handbook:factory-reset) first.

## Security

**FIDO2 Security Key**, **Fingerprint**, **TPM Disk Unlock**, **Firewall**, **Return
to Password Authentication**, **Update Password**. Secure Boot documentation is in
**Learn > EITR Handbook > Secure Boot**, not a separate menu or security-setting action.

## Dotfiles

Opens your configuration directory in VS Code, or in LazyVim when VS Code is
not installed. Keep machine-specific monitor
and hardware overrides in `~/.config/hypr/local.lua`, not the shared defaults.
Do not paste tokens, recovery keys or passwords into configuration backups.

Use the chapters that follow for the detailed workflows and safety limits.

## Language

**Walker > System > Language** lists the languages, with the current one
checked; see the [Language guide](handbook:language).
English menu names remain searchable alongside translated names. Submenus sort
first, then actions, by their translated titles. Main and Apps retain their
existing order.
