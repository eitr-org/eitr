# Devices and input

Find these controls under **System > Devices & Input** or the corresponding bar
icons. The Control Center provides their everyday toggles and sliders too.

## Audio and microphone

Volume selects the default output and controls both master volume and playback
applications. Devices appear by readable name with a type icon; click the current
device to choose another, and use a device's pencil button to rename it on this
computer. Microphone selects the default input, gain and mute. The mic
panel's live level meter runs only while that panel is open; it writes no audio
to disk. Opening other settings does not start microphone monitoring.

Sliders adjust to 100%; an existing higher value is not changed until moved.
Changing your default audio device can affect a call: do it deliberately.
Media playback controls are separate from default device selection.

## Display and brightness

The Display panel lists active monitors. Click one to open its settings inside
its card; click it again to close them. The **Main** display holds the bar,
panels and notifications: turn on **Main display** in another monitor's settings
to move them there. If the main monitor disconnects, another display shows as
**Main** and takes the bar until it returns; your choice is kept.

A monitor's settings are its resolution, refresh rate, scale and, with more than
one monitor, its position beside another or mirroring. The main display stays
where it is and the others are placed around it, so its Position just says so;
a monitor can be placed beside any display except one already placed beside it.

Each setting is one row showing its current value; click it to see the choices.
Position, alignment, scale, mirroring and the main display apply and are saved at
once. A new **resolution or refresh rate** could leave a screen black, so for
those the panel asks **Keep these settings?** at its bottom edge: without
**Keep** within 15 seconds it goes back by itself, even if the panel is closed.
Settings are saved for this computer in `~/.config/hypr/displays.json`.

Any number of monitors can be arranged this way: place each one left of, right
of, above or below another, then align it with that monitor's top, middle or
bottom (left, center or right when stacked). The arrangement is remembered, so
when a monitor changes resolution or scale, the ones beside it move with it. A
choice that would make two monitors overlap is refused with a message. Every
connected monitor is given its exact place, so changing one never makes Hyprland
move the others.

**Edit layout by hand** opens `~/.config/hypr/local.lua` for what the panel does
not cover, such as rotated screens or workspaces pinned to a monitor. A new file
starts with commented examples (three monitors, portrait, stacked, mirroring,
a docked laptop); nothing changes until you uncomment one and run
`hyprctl reload`. Monitors set there take precedence over the panel; remove
them to manage those monitors here again.

Brightness prefers a usable native backlight; otherwise it tries an external
monitor through DDC. DDC availability depends on the monitor and permissions.
Night Light has a manual switch and an optional schedule with editable times.

**HDR** appears only on monitors whose EDID reports PQ or HLG support. It shows the desktop in HDR; games can use HDR even when it is off. Turning HDR on or off also asks you to keep the change within 15 seconds, otherwise it reverts. While HDR is on, **SDR content brightness** adjusts SDR content from 1.0× to 2.0× and saves immediately. Fullscreen HDR games can still switch the monitor automatically when desktop HDR is off.

## Keyboard

Add and remove layouts in Walker: System > Devices & Input > Keyboard. Add Layout
lists every language and variant (type to search); select a layout and press
Delete to remove it. Up to four layouts are supported, duplicates are rejected
and at least one layout must remain. **Alt + Shift** cycles them. With two or
more, the bar shows the active layout's code (such as US or BR); click it, or use
the Control Center, to switch. A keyboard layout is not the system language or locale.

The desktop starts with the keyboard you chose in the installer. Choosing US
gives both US and US International, so accents are one Alt + Shift away.

### Optional Caps Lock navigation

The optional keyd configuration in `distro/keyd/navigation.conf.example` makes
Caps Lock send Escape when tapped. Hold Caps Lock and press H/J/K/L for
Left/Down/Up/Right. Other keys keep their normal behavior.

To restore this preference after reinstalling, install that example as
`/etc/keyd/navigation.conf` and enable `keyd.service`. It applies to all keyboards,
including outside Hyprland, and is not enabled by default. To undo it, remove
that configuration and reload keyd; disable the service if no other mappings
use it. Keyboard language/layout selection remains separate.

## Laptop power and battery

Battery and power-profile controls appear only when a system battery exists,
not merely a wireless headset or mouse. Power Saver/Balanced/Performance need
power-profiles-daemon; unsupported profiles stay unavailable. Battery estimates
and health appear only when supplied by hardware.

Battery Charge Limit requires a supported firmware sysfs interface and typed
confirmation. Off allows charging to 100%. Do not assume every laptop supports it.

A notification warns at 10% battery and again, urgently, at 5%, once each time
the battery runs down. On laptops the installer also adds the audio firmware
most recent laptops need (`sof-firmware`) and, on Intel laptops, `thermald` to
manage heat.

These laptop features are **experimental** until early users confirm them on
real laptops: the keyboard backlight keys, and closing the lid while an external
monitor is connected, which turns the laptop screen off so the desktop moves to
the monitor (opening it brings the screen back). Without an external monitor,
closing the lid suspends as usual. Hibernation is not set up automatically.
