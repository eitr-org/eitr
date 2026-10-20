# Remote access packaging and security

The user guide is the Handbook's Remote Access chapter. Fresh installs include Moonlight, Sunshine and Tailscale; hosting and away
access remain inactive until explicitly set up.

`software.json` installs official Arch `moonlight-qt` and `tailscale` packages,
and Eitr's signed native `eitr-sunshine` package on demand when missing.
Sunshine is listed in `local-packages.txt` for fresh-install payloads and in
`optional-local-packages.txt` so desktop publishing builds it when needed.
Existing machines need network access to install missing packages.

The Sunshine recipe builds the selected upstream release in the maintainer's
build environment. Native capture supports KMS; Flatpak/AppImage cannot provide
that backend. The client never runs yay or makepkg. Only the executable and
assets are packaged, excluding upstream install hooks, autostart, udev rules,
units and capabilities. Permission setup is solely an explicit eitr-system action.
The native package build and runtime ABI must be checked in the release build
environment before publishing; mocked workflow tests do not establish that.

`eitr-system remote-setup USER` saves a private journal before granting KMS
capability and uinput access. Its scoped sudoers rule permits only `remote-open
USER` and `remote-close USER`, used by eitr-sunshine.service. These fixed actions
cannot run arbitrary commands or grant new permission types. The first service
start is local-only. After the browser password step, `remote-arm USER` asks for
confirmation before allowing stream ports. Later starts reuse that decision.

The priority -10 nftables guard rejects remote TCP 47990 before connection tracking
or broad rules in the base firewall. It rejects streaming outside connected private
LAN scopes and tailscale0, even when the base firewall has other allowances. The
base firewall must be active to enable streams. Runtime openings live under /run,
so reboot cannot leave them enabled without a new service start. ExecStopPost
revokes them after normal exit, startup failure or a crash; the early guard also
blocks established streams. Do not remove it while Sunshine is running. Existing
independent Sunshine services must be stopped by their owner before using Eitr's
service. There is no router forwarding or automatic UPnP.

Undo actions retain installed packages, Sunshine settings, paired clients and
Tailscale sign-in credentials. Restore Sharing Setup first stops/disables the Eitr
user service, then restores saved udev/module/sudoers files, binary capabilities
and device ACLs, removes its nftables guard and runtime openings, and deletes its
journal. If setup loaded uinput, undo unloads it after Sunshine has stopped. A busy module
causes a reported failure and retains the journal for retry after closing the
application using it. Restore Away Access Setup restores
the previous Tailscale operator and original enabled/active service states.
