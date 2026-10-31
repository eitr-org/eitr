"""Remove the notification activation file older Eitr releases installed.

It points D-Bus activation of org.freedesktop.Notifications at the desktop bar,
so a notification sent early in a login starts a second bar beside the one the
session starts. The bar owns the name itself once it runs. A file that starts
anything other than the desktop bar is the user's and stays.
"""
from eitr_paths import data

service = data('dbus-1/services/org.erikreider.swaync.service')
try:
    lines = [line.strip() for line in service.read_text().splitlines() if line.strip()]
except FileNotFoundError:
    lines = []
if (lines[:2] == ['[D-BUS Service]', 'Name=org.freedesktop.Notifications'] and len(lines) == 3
        and lines[2].startswith('Exec=') and 'desktop-bar' in lines[2]):
    service.unlink()
