pragma Singleton
import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

QtObject {
    id: settingsPalette
    property string palette: "theme"
    property color themeBackground: "#191b25"
    property color themeForeground: "#e4e5ef"
    property color themeAccent: "#b08d57"
    readonly property bool website: palette === "website"
    readonly property color background: website ? SiteStyle.bg : themeBackground
    readonly property color surface: website ? SiteStyle.card : Qt.tint(background, Qt.alpha(foreground, 0.025))
    readonly property color raised: website ? SiteStyle.raised : Qt.tint(background, Qt.alpha(foreground, 0.08))
    readonly property color foreground: website ? SiteStyle.fg : themeForeground
    readonly property color muted: website ? SiteStyle.muted : Qt.alpha(foreground, 0.72)
    readonly property color gold: SiteStyle.bronze
    readonly property color accent: website ? SiteStyle.accent : themeAccent
    readonly property color line: website ? SiteStyle.line : Qt.alpha(foreground, 0.12)
    property string error: ""
    function select(value, persist) {
        if (!["theme", "website"].includes(value)) return;
        settingsPalette.palette = value;
        if (persist !== false) file.setText(JSON.stringify({version: 1, palette: value}) + "\n");
    }
    property FileView file: FileView {
        path: Eitr.Paths.config("eitr/settings-app.json")
        atomicWrites: true
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                const data = Eitr.Paths.settings(text());
                settingsPalette.palette = data.version === 1 && data.palette === "website" ? "website" : "theme";
                settingsPalette.error = "";
            } catch (error) { settingsPalette.palette = "theme"; settingsPalette.error = String(error); }
        }
        onLoadFailed: settingsPalette.palette = "theme"
    }
}
