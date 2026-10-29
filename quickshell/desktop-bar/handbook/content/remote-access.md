# Remote access

Detailed Status opens a diagnostic terminal that stays open until you press Esc.

Use System > Connectivity > Remote Access. Hosting is off until you enable it.
This milestone controls your signed-in, awake Eitr desktop. Headless use, access
before login and wake on LAN are separate future work. While sharing, the remote
screen shows the lockscreen when this PC locks; anyone connected sees it and can
type the password, so stop sharing before stepping away when privacy matters.

## Sunshine on Eitr

Choose Share this PC > Set Up Sharing. Installation uses Eitr's signed native
Sunshine package, built from upstream sources by the release maintainer. There
is no AUR build on first click. Flatpak and AppImage lack KMS capture. Existing
Sunshine configuration and paired devices are kept; do not run another Sunshine
instance at the same time.

Read the full-control warning and type `yes` only if you accept KMS screen
capture and virtual keyboard, mouse and controller input. Setup saves the
original permissions privately in `/var/lib/eitr/remote-access`. It adds a uinput
udev rule, loads uinput at boot, grants the desktop user device access and gives
Sunshine `cap_sys_admin+p`. These are powerful permissions. Restore Sharing Setup
stops sharing, restores the saved files and device ACL, and removes capture permissions. If setup loaded uinput, undo unloads it too. If another application still uses it,
undo reports the failure and keeps the journal so you can close that application
and retry.

Start Sharing asks before giving remote devices control. The local web settings
open at `https://localhost:47990`. On first use, streaming stays blocked while you
set the password. Return to the terminal and confirm that it is set; your
administrator password then enables remote control. Accept the local self-signed certificate only
at that address. Set Sunshine's username and a strong password before pairing.
Open Settings returns here; Pair a Device opens the PIN page. Enter only the PIN
shown on your own Moonlight device. Keep automatic router configuration off;
Eitr enforces `upnp=off`. Do not configure router port forwarding.

TCP 47984, 47989 and 48010 and UDP 47998-48000 are permitted only from directly
connected private LAN subnets and `tailscale0`. TCP 47990 is restricted to this PC,
even when another firewall rule would permit it. LAN scopes are captured at each
start; stop and start sharing after changing networks. Use only trusted home
networks. Stop Sharing also disables start at login and closes streaming ports,
including established streams. Service failure closes them too; runtime openings
do not survive a reboot. After the first start, Start Sharing and Stop Sharing switch at once, without
questions or a password. Start at Login is optional and switches at once from the
Streaming panel or the menu; Turn Off Start at Login keeps manual sharing. Sharing Status shows service errors.

A Sunshine package update clears the executable’s capture capability. If sharing
then refuses to start, run Set Up Sharing again and confirm the capture grant;
the original undo record is retained.

Sunshine runs with the KMS capability only as root or the sharing account: setup sets the executable to `root:eitr-sharing` mode `0750` and adds your account to that system group. Sign out and back in before starting sharing so the user service receives the new group. Setup leaves any running sharing process active; a restart before the next login can fail. Stop Sharing retains setup permissions. Restore Sharing Setup removes group membership and all binary capabilities and returns the executable to `root:root` mode `0755`, including when restoring older setup records. After a package update, Set Up Sharing repairs ownership and mode before granting the capability again.

## Moonlight on a Mac

Install Moonlight from [the Moonlight project](https://moonlight-stream.org/).
Keep Eitr and the Mac on the same home network for the first test. Add Eitr's LAN
address manually if discovery does not find it. Select the PC, read its PIN,
then use Pair a Device on Eitr. Select Desktop to control applications and games.
Sunshine settings select the captured display; verify each monitor separately.
Gaming > Moonlight and Connect to another PC install or open the Eitr client for
connecting in the opposite direction. Fresh installs include these apps; sharing stays off until explicitly enabled.

SUPER shortcuts from the Mac: in Moonlight's settings, turn on **Capture system keyboard shortcuts** (in fullscreen or always). Only then does Moonlight send the Mac's Command key as SUPER; otherwise Command shortcuts stay on the Mac. Ctrl+Alt+Shift+K turns the capture on or off during a session.

## Tailscale on both computers

Choose Access away from home > Set Up Away Access. After installing Tailscale,
the confirmed root helper enables and starts `tailscaled.service`, then makes
your desktop user its operator, so Sign In, Connect and Disconnect need no
password. A Tailscale set up some other way asks for the administrator password
instead. Sign In
opens the URL printed by `tailscale login` in your browser. Connect brings the
PC online; Disconnect takes it offline without deleting sign-in credentials.
Connection Status shows this PC's Tailscale address, signed-out states and whether
active peers are Direct, Relayed or idle. Ping a Peer uses `tailscale ping` to
check a specific connection. Relay paths can increase latency and reduce quality.

Install [Tailscale on the Mac](https://tailscale.com/download/mac), sign in to the
same tailnet, and connect both computers. Add Eitr's Tailscale address in Moonlight;
use the same Sunshine pairing procedure. Tailnet access policy must allow the
streaming ports. The Sunshine web settings remain local to Eitr.

Restore Away Access Setup restores the previous operator and original service
startup/running state; it retains Tailscale account state and installed packages.
If the service was already active it stays active. Disconnect first if you want
to stop a connection. Failed installs or commands stay visible in the task terminal;
retry the failed step after resolving its error. No package removal is implicit.

## What has been tested

Automated tests use mocks. On a real desktop (one and then two monitors) with a
MacBook running Moonlight: setup, start sharing, pairing by address, video,
keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start at login,
Stop Sharing and Restore Sharing Setup on the home network, and Tailscale setup,
sign-in and connection from away. Controllers, other GPUs and other clients have
not been tested.
