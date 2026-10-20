pragma Singleton
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io

// Corner style and the critical-notification color. Styles come from
// corner-styles.json; desktop-style.py calls `style reload` after a change,
// and the bar's theme refresh supplies criticalColor, so nothing polls here.
QtObject {
    id: style
    property var styles: ({})
    property string defaultStyle: "rounded"
    property string corners: defaultStyle
    property color criticalColor: "#e05c68"
    property string preferenceText: ""
    readonly property var options: Object.keys(styles).map(key => ({key: key, label: styles[key].label}))
    readonly property real scale: styles[corners] ? styles[corners].scale : 1

    function radius(value) { return value * scale; }
    function select(value) {
        if (!styles[value]) return;
        corners = value;
        save.command = ["python3", Quickshell.shellDir + "/scripts/desktop-style.py", "set", value];
        save.running = true;
    }
    function apply(text) {
        try {
            let value = JSON.parse(text).corners;
            corners = styles[value] ? value : defaultStyle;
        } catch (error) { corners = defaultStyle; }
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
        onLoadFailed: { style.preferenceText = ""; style.corners = style.defaultStyle; }
    }
    property IpcHandler ipc: IpcHandler {
        target: "style"
        function reload(): void { style.preference.reload(); }
    }
}
