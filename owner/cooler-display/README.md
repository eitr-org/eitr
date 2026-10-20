# Cooler display (owner's machine only)

Shows the CPU temperature on the owner's liquid cooler, whose pump has a
two-digit °C display driven by a USB HID device `aa88:8666` (东莞铭研电子科技 /
Dongguan Mingyan, "温度显示HID设备"). Other coolers use other devices, so this is
not part of the EITR package; `owner/` is never packaged.

Protocol, found by probing (no vendor documentation exists): the device has no
report IDs and 10-byte input/output reports. It shows the first output byte as
the temperature in °C (0-99), sends nothing back, and keeps the last value, so
the script rewrites it every two seconds from the CPU package sensor (Intel
coretemp `Package id 0`, AMD `Tctl`/`Tdie`).

Install or update (asks for sudo once, for the udev rule):

```sh
bash owner/cooler-display/install.sh
```

It installs `~/.local/bin/cooler-display`, the user service
`cooler-display.service` (starts with every desktop session) and
`/etc/udev/rules.d/70-cooler-display.rules`, which lets the logged-in user
write to the display. `cooler-display status` shows the device and reading;
`journalctl --user -u cooler-display` shows errors.
