# Capture and sharing

Screenshots and recording are under Main > Tools > Capture; Color, OCR Text, QR Code and Transcode sit directly in Main > Tools. Control Center > Tools offers the same actions.

## Screenshots and extraction

- **Print:** full screenshot in the floating editor.
- **SUPER + Print:** frozen selection in the floating editor.
- **SUPER + Shift + Print:** active-window screenshot in the editor.
- **SUPER + Ctrl + Print:** OCR text from a selection.
- **SUPER + Alt + Print:** decode a QR code from a selection.
- **SUPER + =:** pick a color and copy it.

A screenshot ends with a brief lightning flash that strikes what you captured.
It starts after the image is taken, so it never appears in the screenshot.

Review the selected content before saving or sharing. OCR results may be wrong;
QR codes can contain private credentials or untrusted URLs. A screenshot editor
is not a guarantee that sensitive background text has been removed.

Saved screenshots offer notification actions to open the image, edit it in the screenshot editor (saving over it), beautify it, pin it on screen or open its screenshots folder.

**Beautify** sets the screenshot on a background (the theme's gradient, a few presets, the accent colour or none) with adjustable padding, rounded corners and a shadow; **Copy picture** puts the full-size picture on the clipboard and **Save picture** writes it beside the original as `NAME-beautified.png`.

**Pin on screen** floats the screenshot above every window and on every workspace as a reference. Drag it to move it and scroll over it to resize it; close it with its × button, Escape or a middle click.

## Recording and streaming

Screen Recording opens OBS controls. They use your configured OBS scene and saved
Wayland capture permission; the scene must include a visible monitor source. Starting capture prepares OBS and closes the panel before capture begins. The controls use OBS's WebSocket, which OBS ships turned off: Eitr turns it on,
with a password, the first time while OBS is closed.

If OBS is open then, close
it once and try again. Recordings go to **Videos/Records** in your home folder. OBS's own default is
the home folder itself; Eitr changes only that default, so a folder you pick in
OBS > Settings > Output stays. While OBS records or streams, a red dot sits just left of the clock.

Click it for the
elapsed time and file size, pause/resume, stop, a chapter marker (needs OBS's
Hybrid MP4 format), the OBS microphone and camera, and the scene; a stream shows
a LIVE timer with its own stop. When a recording stops, a notification offers
Play recording, Open folder and Copy path.

Check audio/mic choices
and the selected monitor before starting. Webcam requires an OBS camera source. Recording audio switches affect OBS inputs, not your system volume.

The handbook never starts a recording or stream. Screen sharing and capture
remain explicit actions. Transcode offers the existing image/video conversion
workflow; review output paths before replacing a file.

When OBS is closed, Record captures the display you are focused on: Eitr answers OBS's screen request itself, with no picker, and sets OBS's canvas to that display's size (a scaled-down output keeps its ratio). An OBS window you opened yourself keeps recording what it already captures; after the recording stops, Eitr closes the OBS it started, so the next one follows your focus again. Other apps that share your screen, such as a video call, still show Hyprland's share picker. A `~/.config/hypr/xdph.conf` you changed yourself is kept, so the picker may then ask every time.

For a new OBS configuration, Eitr creates an Untitled collection with one Scene: screen capture, a hidden camera, and default desktop and microphone audio. The camera stays off until you enable it. Existing collections are never changed.

## Share

Main > Tools > Share provides LocalSend and the existing transfer tools. Sending a file
requires choosing the destination/device. Verify recipients and avoid sharing
private keys, recovery codes, tokens or a complete unreviewed home/config folder.
