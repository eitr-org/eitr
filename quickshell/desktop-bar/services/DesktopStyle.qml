pragma Singleton
import ".."
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io
import "../ChoiceLists.js" as ChoiceLists

// Shared motion policy, corners, window gaps and critical-notification color.
// desktop-style.py reloads the saved preferences; theme refresh supplies criticalColor.
QtObject {
    id: style
    property var styles: ({})
    property string defaultStyle: "rounded"
    property string gaps: "default"
    function selectGaps(value) {
        if (save.running || !ChoiceLists.ids(ChoiceLists.windowGaps).includes(value)) return;
        save.command = ["python3", Quickshell.shellDir + "/scripts/desktop-style.py", "set", "gaps", value];
        save.running = true;
    }
    property string corners: defaultStyle
    property color criticalColor: "#e05c68"
    property string preferenceText: ""
    readonly property var options: Object.keys(styles).map(key => ({key: key, label: styles[key].label}))
    readonly property real scale: styles[corners] ? styles[corners].scale : 1

    property bool reduceMotion: false
    // Set by the bar: the Website appearance (site palette and gold labels).
    property bool website: false
    function motionDuration(milliseconds) { return reduceMotion || FocusMode.enabled ? 0 : milliseconds; }

    function radius(value) { return value * scale; }
    function select(value) {
        if (save.running || !styles[value]) return;
        corners = value;
        save.command = ["python3", Quickshell.shellDir + "/scripts/desktop-style.py", "set", value];
        save.running = true;
    }
    function apply(text) {
        try {
            const preference = JSON.parse(text);
            gaps = ChoiceLists.ids(ChoiceLists.windowGaps).includes(preference.gaps) ? preference.gaps : "default";
            let value = preference.corners;
            corners = styles[value] ? value : defaultStyle;
        } catch (error) { corners = defaultStyle; gaps = "default"; }
    }

    property Process save: Process {}
    property FileView definitions: FileView {
        path: Quickshell.shellDir + "/corner-styles.json"
        printErrors: false
        onLoaded: {
            try {
                let data = JSON.parse(text());
                style.styles = data.styles;
                style.defaultStyle = data.default;
                style.apply(style.preferenceText);
            } catch (error) { console.warn("Invalid corner-styles.json:", error); }
        }
    }
    property FileView preference: FileView {
        path: Eitr.Paths.config("eitr/style.json")
        watchChanges: true; printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                Eitr.Paths.settings(text());
                style.preferenceText = text();
                style.apply(style.preferenceText);
            } catch (error) { console.warn("Invalid corner settings:", error); }
        }
        onLoadFailed: { style.preferenceText = ""; style.corners = style.defaultStyle; style.gaps = "default"; }
    }
    property IpcHandler ipc: IpcHandler {
        target: "style"
        function reload(): void { style.preference.reload(); }
    }
}
