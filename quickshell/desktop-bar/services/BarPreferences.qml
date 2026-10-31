import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

// The bar's saved settings and workspace palette: read at start and when their
// files change, written after a short delay, and the bar IPC that edits them.
Scope {
    id: preferences
    property var host
    function updateBarSetting(key, value) {
        var choices = {appearance: ["transparent", "solid"], layout: ["unified", "centered", "notch", "islands"], edge: ["top", "bottom", "left", "right"], pinned: ["yes", "no"], screens: ["main", "all"], autohide: ["yes", "no"], dock: ["yes", "no"], reduceMotion: ["yes", "no"], mediaStyle: ["bars", "line"], clock: ["12h", "24h"]};
        if (!choices[key] || choices[key].indexOf(value) === -1) return;
        if (key === "appearance") host.barAppearance = value;
        else if (key === "layout") host.barLayout = value;
        else if (key === "pinned") host.barPinned = value === "yes";
        else if (key === "mediaStyle") host.barMediaStyle = value;
        else if (key === "clock") host.barClock = value;
        else if (key === "screens") host.barScreens = value;
        else if (key === "reduceMotion") DesktopStyle.reduceMotion = value === "yes";
        else if (key === "dock") host.barDock = value === "yes";
        else if (key === "autohide") host.barAutoHide = value === "yes";
        else host.barEdge = value;
        host.settingsDirty = true;
        settingsSaveDelay.restart();
    }

    IpcHandler {
        target: "bar"
        function idleLock(enabled: bool): void { host.idleLockEnabled = enabled; }
        function workspaces(): string { return JSON.stringify({count: host.workspaceCount, limit: 10}); }
        function visibility(): void { host.barVisible = !host.barVisible; }
        function update(key: string, value: string): void { preferences.updateBarSetting(key, value) }
        function toggle(kind: string): void {
            if (kind === "appearance") preferences.updateBarSetting(kind, host.barAppearance === "solid" ? "transparent" : "solid");
            else if (kind === "layout") preferences.updateBarSetting(kind, host.barLayout === "unified" ? "centered" : host.barLayout === "centered" ? "notch" : host.barLayout === "notch" ? "islands" : "unified");
        }
    }

    Process {
        id: barSettingsQuery
        command: ["python3", Quickshell.shellDir + "/scripts/bar-settings.py", "status"]
        running: true
        stdout: StdioCollector { id: barSettingsOutput }
        onExited: function(code) {
            if (code !== 0 || host.settingsDirty || saveBarSettings.running) return;
            try {
                var settings = JSON.parse(barSettingsOutput.text);
                host.barAppearance = settings.appearance;
                host.barLayout = ["unified", "centered", "notch", "islands"].indexOf(settings.layout) >= 0 ? settings.layout : "unified";
                host.barEdge = settings.edge;
                host.barPinned = settings.pinned === "yes";
                host.barMediaStyle = settings.mediaStyle === "line" ? "line" : "bars";
                host.barClock = settings.clock === "24h" ? "24h" : "12h";
                host.barScreens = settings.screens || "main";
                host.barAutoHide = settings.autohide === "yes";
                host.barDock = settings.dock !== "no";
                DesktopStyle.reduceMotion = settings.reduceMotion === "yes";
            } catch (e) {}
        }
    }

    PreferenceWatch {
        path: Eitr.Paths.config("quickshell/desktop-bar/bar-settings.json")
        onChanged: settingsReload.restart()
    }
    Timer {
        id: settingsReload
        interval: 40
        onTriggered: {
            if (barSettingsQuery.running || saveBarSettings.running || host.settingsDirty) restart();
            else barSettingsQuery.running = true;
        }
    }

    Timer {
        id: settingsSaveDelay
        interval: 100
        onTriggered: preferences.persistBarSettings()
    }

    function persistBarSettings() {
        if (saveBarSettings.running) return;
        host.settingsDirty = false;
        saveBarSettings.command = ["python3", Quickshell.shellDir + "/scripts/bar-settings.py",
            "set-all", host.barAppearance, host.barLayout, host.barEdge, host.barPinned ? "yes" : "no", host.barScreens, host.barAutoHide ? "yes" : "no", DesktopStyle.reduceMotion ? "yes" : "no", host.barMediaStyle, host.barDock ? "yes" : "no", host.barClock];
        saveBarSettings.running = true;
    }

    Process {
        id: saveBarSettings
        onExited: {
            if (host.settingsDirty) preferences.persistBarSettings();
            else if (!barSettingsQuery.running) barSettingsQuery.running = true;
        }
    }

    function setWorkspaceStyle(style) {
        host.workspaceStyle = style;
        saveWorkspaceStyle.command = ["python3", Quickshell.shellDir + "/scripts/workspace-style.py", style];
        saveWorkspaceStyle.running = true;
    }

    Process {
        id: saveWorkspaceStyle
        onExited: if (!workspacePalette.running) workspacePalette.running = true
    }

    Process {
        id: workspacePalette
        command: ["python3", Quickshell.shellDir + "/scripts/workspace-color.py"]
        running: true
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var palette = JSON.parse(text);
                    PluginRegistry.palette = palette.palette || ({});
                    host.activeBg = palette.background;
                    host.activeFg = palette.foreground;
                    if (!saveWorkspaceStyle.running) host.workspaceStyle = palette.style;
                    host.workspaceMenuBg = palette.menuBackground;
                    host.workspaceMenuFg = palette.menuForeground;
                    host.fg = palette.menuForeground;
                    DesktopStyle.criticalColor = palette.critical;
                    var background = host.workspaceMenuBg;
                    host.bg = Qt.rgba(background.r, background.g, background.b, 0.38);
                    host.hoverBg = Qt.rgba(host.fg.r, host.fg.g, host.fg.b, 0.15);
                } catch (e) {}
            }
        }
    }

    PreferenceWatch {
        path: Eitr.Paths.config("theme/current/colors.toml")
        ancestor: Eitr.Paths.config("theme")
        onChanged: paletteReload.restart()
    }
    PreferenceWatch {
        path: Eitr.Paths.config("quickshell/desktop-bar/workspace-style.json")
        onChanged: paletteReload.restart()
    }
    Timer {
        id: paletteReload
        interval: 40
        onTriggered: {
            if (workspacePalette.running || saveWorkspaceStyle.running) restart();
            else workspacePalette.running = true;
        }
    }
}
