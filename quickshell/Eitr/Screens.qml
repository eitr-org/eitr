pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

// Where a window opened from a shortcut, Walker or IPC belongs: the display Hyprland has
// focused, else FALLBACK (usually the bar's main display), else the first one.
Singleton {
    function focused(fallback) {
        const monitor = Hyprland.focusedMonitor;
        const screens = Quickshell.screens || [];
        return screens.find(screen => monitor && screen && screen.name === monitor.name) || fallback || screens[0] || null;
    }
}
