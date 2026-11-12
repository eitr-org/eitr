# Remote access

Open Settings > Streaming for Sunshine and Moonlight, or Walker > Settings > Devices > Streaming for the same actions. Hosting is off until you enable it.
This milestone controls your signed-in, awake Eitr desktop. Headless use, access
before login and wake on LAN are separate future work. While sharing, the remote
screen shows the lockscreen when this PC locks; anyone connected sees it and can
type the password, so stop sharing before stepping away when privacy matters.

Setup folders group the configuration actions. Streaming > Sharing Setup contains Set Up Sharing, Sharing Settings, Start at Login, Turn Off Start at Login, Detailed Status and Restore Sharing Setup. Everyday sharing actions (Start Sharing, Stop Sharing, Pair a Device, Sharing Status and Connect to another PC) stay directly in Streaming.

Detailed Status opens a diagnostic terminal that stays open until you press Esc.

## Sunshine on Eitr

Choose Share This PC > Setup > Set Up Sharing. Installation uses Eitr's signed native
Sunshine package, built from upstream sources by the release maintainer. There
is no AUR build on first click. Flatpak and AppImage lack KMS capture. Existing
Sunshine configuration and paired devices are kept; do not run another Sunshine
instance at the same time.

Read the full-control warning and type `yes` only if you accept KMS screen
capture and virtual keyboard, mouse and controller input. Setup saves the
original permissions privately in `/var/lib/eitr/remote-access`. It adds a uinput
udev rule, loads uinput at boot, grants the desktop user device access and gives
Sunshine `cap_sys_admin+p`. These are powerful permissions.

Restore Sharing Setup
stops sharing, restores the saved files and device ACL, and removes capture permissions. If setup loaded uinput, undo unloads it too. If another application still uses it,
undo reports the failure and keeps the journal so you can close that application
and retry.

Start Sharing asks before giving remote devices control. The local web settings
open at `https://localhost:47990`. On first use, streaming stays blocked while you
set the password. Return to the terminal and confirm that it is set; your
administrator password then enables remote control. Accept the local self-signed certificate only
at that address.

Set Sunshine's username and a strong password before pairing. Sharing Settings in Setup returns here; Pair a Device opens the PIN page. Enter only the PIN
shown on your own Moonlight device. Keep automatic router configuration off;
Eitr enforces `upnp=off`. Do not configure router port forwarding.

TCP 47984, 47989 and 48010 and UDP 47998-48000 are permitted only from directly
connected private LAN subnets and `tailscale0`. TCP 47990 is restricted to this PC,
even when another firewall rule would permit it. LAN scopes are captured at each
start; stop and start sharing after changing networks. Use only trusted home
networks.

Stop Sharing also disables start at login and closes streaming ports,
including established streams. Service failure closes them too; runtime openings
do not survive a reboot. After the first start, Start Sharing and Stop Sharing switch at once, without
questions or a password. Start at Login is optional and switches at once from the
Streaming panel or the menu; Turn Off Start at Login keeps manual sharing.

Sharing Status shows service errors.

A Sunshine package update replaces the executable, which clears its capture
capability; the update then gives it back to the account that set up sharing. If
sharing still cannot start, the Streaming toggle says why: run Set Up Sharing
again, or sign out and back in after a first setup. The original undo record is
retained.

Sunshine runs with the KMS capability only as root or the sharing account: setup sets the executable to `root:eitr-sharing` mode `0750` and adds your account to that system group. Sign out and back in before starting sharing so the user service receives the new group. Setup leaves any running sharing process active; a restart before the next login can fail.

Stop Sharing retains setup permissions. Restore Sharing Setup removes group membership and all binary capabilities and returns the executable to `root:root` mode `0755`, including when restoring older setup records. After a package update, Set Up Sharing repairs ownership and mode before granting the capability again.

## Moonlight on a Mac

Install Moonlight from [the Moonlight project](https://moonlight-stream.org/).
Keep Eitr and the Mac on the same home network for the first test. Add Eitr's LAN
address manually if discovery does not find it. Select the PC, read its PIN,
then use Pair a Device on Eitr. Select Desktop to control applications and games.
Sunshine settings select the captured display; verify each monitor separately.
Gaming > Moonlight and Connect to another PC install or open the Eitr client for
connecting in the opposite direction. Fresh installs include these apps; sharing stays off until explicitly enabled.

SUPER shortcuts from the Mac: in Moonlight's settings, turn on **Capture system keyboard shortcuts** (in fullscreen or always). Only then does Moonlight send the Mac's Command key as SUPER; otherwise Command shortcuts stay on the Mac. Ctrl+Alt+Shift+K turns the capture on or off during a session.

## What has been tested

Automated tests use mocks. On a real desktop (one and then two monitors) with a
MacBook running Moonlight: setup, start sharing, pairing by address, video,
keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start at login,
Stop Sharing and Restore Sharing Setup on the home network and from away through a VPN. Controllers, other GPUs and other clients have
not been tested.

Streaming sits beside Connections under Devices. Sunshine shows sharing status, setup, start/stop, start at login, pairing, settings, diagnostics and restore setup. Moonlight shows installation status and an install/open button.
