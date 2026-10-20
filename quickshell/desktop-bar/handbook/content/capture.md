# Capture and sharing

Capture tools are under Main > Tools > Capture and Control Center > Tools.

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

## Recording and streaming

Screen Recording opens OBS controls. They use your configured OBS scene and saved
Wayland capture permission; the scene must include a visible monitor source.
Starting capture prepares OBS and closes the panel before capture begins.
The controls use OBS's WebSocket, which OBS ships turned off: Eitr turns it on,
with a password, the first time while OBS is closed. If OBS is open then, close
it once and try again.
Recordings go to **Videos/Records** in your home folder. OBS's own default is
the home folder itself; Eitr changes only that default, so a folder you pick in
OBS > Settings > Output stays.
While OBS records or streams, a red dot sits beside the weather. Click it for the
elapsed time and file size, pause/resume, stop, a chapter marker (needs OBS's
Hybrid MP4 format), the OBS microphone and camera, and the scene; a stream shows
a LIVE timer with its own stop. When a recording stops, a notification offers
Open folder and Copy path. Check audio/mic choices
and the selected monitor before starting. Webcam requires an OBS camera source.
Recording audio switches affect OBS inputs, not your system volume.

The handbook never starts a recording or stream. Screen sharing and capture
remain explicit actions. Transcode offers the existing image/video conversion
workflow; review output paths before replacing a file.

For a new OBS configuration, Eitr creates an Untitled collection with one Scene: screen capture, a hidden camera, and default desktop and microphone audio. The system asks which screen to share on first use; OBS saves that permission. The camera stays off until you enable it. Existing collections are never changed.

## Share

Main > Tools > Share provides LocalSend and the existing transfer tools. Sending a file
requires choosing the destination/device. Verify recipients and avoid sharing
private keys, recovery codes, tokens or a complete unreviewed home/config folder.
