# Plymouth splash and local preview

The logo contains a horizontal Bifröst gradient. Bands move left to right at
80 logical pixels per second (one virtual terminal column per 12 pixels), with
the same palette, phase advance and 9.6-second cycle as System Update text.
The 64 masked gradient phases blend at 50 Hz, including across the loop seam.
The exported images preserve the wordmark's alpha mask.

Boot and shutdown retain the runestone-gold rune ring (`#c4914f`). Asking for the
disk passphrase immediately hides every rune. Only the animated logo, neutral
prompt, field and password bullets remain; loading returns after acceptance.

Regenerate with `python3 distro/plymouth/eitr/export.py`; verify with `--check`.
`--preview-dir PATH` creates static illustrative frames without running Plymouth.

## Windowed review

From this checkout in a graphical terminal, run:

```sh
sudo bash tools/plymouth-preview.sh
```

Plymouth's installed X11 test renderer opens two decorated windows (800×600 and
640×480). It does not use fullscreen. Keep the terminal open: Ctrl+C cancels.
The sequence is six seconds of boot loading, a password prompt, six seconds of
post-password loading and five seconds in shutdown mode. Enter any demo text
in a preview window; it is accepted and discarded, never printed or saved.
Do not enter a real password for this demonstration.

The script copies only this checkout's theme into `eitr-preview`. It uses the
per-daemon `plymouth.splash=eitr-preview` override, so neither the installed
`eitr` theme nor the system's default-theme configuration is changed. It never
rebuilds an initramfs or changes a bootloader. A preexisting `eitr-preview` is
refused rather than overwritten.

Private mount and network namespaces isolate the daemon's state and control
socket. Only `x11.so` is visible in its renderer directory, preventing fallback
to DRM or framebuffer rendering. The X11 filesystem socket and session's
XAUTHORITY remain available. The script requires local X11/Xwayland, `unshare`,
`mount`, `setsid`, `timeout` and Python 3; if namespace creation or X11 access fails it
stops and cleans up. All mounts disappear with the private namespace. Exit,
startup failure and Ctrl+C remove the temporary theme and files and stop only
the preview's own processes. It never quits an existing system Plymouth daemon.

The windowed preview is for visual review. Actual boot, shutdown and encrypted
unlock still require a VM check before publishing the revised theme.
