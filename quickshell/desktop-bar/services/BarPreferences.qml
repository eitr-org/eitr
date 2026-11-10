import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

// The bar's saved settings and workspace palette: read at start and when their
// files change, written after a short delay, and the bar IPC that edits them.
Scope {
    id: preferences
    property var host
    // Empty-bar double-click cycles follow tools/choice-lists.json (left: appearances, right: layouts).
    function nextAppearance(current) { return ChoiceLists.next(ChoiceLists.barAppearances, current); }
    function nextLayout(current) { return ChoiceLists.next(ChoiceLists.barLayouts, current); }
    function updateBarSetting(key, value) {
        var choices = {appearance: ChoiceLists.ids(ChoiceLists.barAppearances), layout: ChoiceLists.ids(ChoiceLists.barLayouts), edge: ["top", "bottom", "left", "right"], pinned: ["yes", "no"], screens: ["main", "all"], autohide: ["yes", "no"], dock: ["yes", "no"], glow: ["yes", "no"], reduceMotion: ["yes", "no"], mediaStyle: ["bars", "line"], clock: ["12h", "24h"]};
        if (!choices[key] || choices[key].indexOf(value) === -1) return;
        if (key === "appearance") host.barAppearance = value;
        else if (key === "layout") host.barLayout = value;
        else if (key === "pinned") host.barPinned = value === "yes";
        else if (key === "mediaStyle") host.barMediaStyle = value;
        else if (key === "clock") host.barClock = value;
        else if (key === "screens") host.barScreens = value;
        else if (key === "reduceMotion") DesktopStyle.reduceMotion = value === "yes";
        else if (key === "glow") host.barGlow = value === "yes";
        else if (key === "dock") host.barDock = value === "yes";
        else if (key === "autohide") host.barAutoHide = value === "yes";
        else host.barEdge = value;
        host.settingsDirty = true;
        settingsSaveDelay.restart();
    }

    IpcHandler {
        target: "bar"
        function idleLock(enabled: bool): void { host.idleLockEnabled = enabled; }
        function workspaces(): string { return JSON.stringify({count: host.workspaceCount, limit: DesktopStyle.workspaceCount}); }
        function visibility(): void { host.barVisible = !host.barVisible; }
        function update(key: string, value: string): void { preferences.updateBarSetting(key, value) }
        function toggle(kind: string): void {
            if (kind === "appearance") preferences.updateBarSetting(kind, preferences.nextAppearance(host.barAppearance));
            else if (kind === "layout") preferences.updateBarSetting(kind, preferences.nextLayout(host.barLayout));
            // A bar hidden from the Control Center comes back first; otherwise auto-hide switches.
            else if (kind === "autohide") {
                if (!host.barVisible) host.barVisible = true;
                else preferences.updateBarSetting(kind, host.barAutoHide ? "no" : "yes");
            }
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
                host.barLayout = ChoiceLists.ids(ChoiceLists.barLayouts).indexOf(settings.layout) >= 0 ? settings.layout : ChoiceLists.barLayouts[0].id;
                host.barEdge = settings.edge;
                host.barPinned = settings.pinned === "yes";
                host.barMediaStyle = settings.mediaStyle === "line" ? "line" : "bars";
                host.barClock = settings.clock === "24h" ? "24h" : "12h";
                host.barScreens = settings.screens || "main";
                host.barAutoHide = settings.autohide === "yes";
                host.barDock = settings.dock !== "no";
                host.barGlow = settings.glow === "yes";
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
            "set-all", host.barAppearance, host.barLayout, host.barEdge, host.barPinned ? "yes" : "no", host.barScreens, host.barAutoHide ? "yes" : "no", DesktopStyle.reduceMotion ? "yes" : "no", host.barMediaStyle, host.barDock ? "yes" : "no", host.barClock, host.barGlow ? "yes" : "no"];
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
                    host.themeActiveBg = palette.background;
                    host.themeActiveFg = palette.foreground;
                    if (!saveWorkspaceStyle.running) host.workspaceStyle = palette.style;
                    host.themeMenuBg = palette.menuBackground;
                    host.themeMenuFg = palette.menuForeground;
                    host.themeFg = palette.menuForeground;
                    DesktopStyle.criticalColor = palette.critical;
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
