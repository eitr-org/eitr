pragma Singleton
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io

QtObject {
    id: fonts
    property string family: "JetBrainsMono Nerd Font"
    property bool waitingForPreference: true
    // On a fresh installation the preference directory may not exist yet.
    // Retry until the first selection creates it, then rely on file watching.
    property Timer firstSelection: Timer {
        interval: 500; repeat: true; running: fonts.waitingForPreference
        onTriggered: fonts.preference.reload()
    }
    property FileView preference: FileView {
        path: Eitr.Paths.config("eitr/font.json")
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoadFailed: function(error) {
            fonts.family = "JetBrainsMono Nerd Font";
            fonts.waitingForPreference = error === FileViewError.FileNotFound;
        }
        onLoaded: {
            fonts.waitingForPreference = false;
            try {
                let choice = Eitr.Paths.settings(text()).family;
                fonts.family = typeof choice === "string" && choice.length ? choice : "JetBrainsMono Nerd Font";
            } catch (error) { console.warn("Invalid font settings:", error); }
        }
    }
}
