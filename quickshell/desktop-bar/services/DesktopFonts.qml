pragma Singleton
import ".."
import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io

QtObject {
    id: fonts
    property string family: "JetBrainsMono Nerd Font"
    property PreferenceWatch preferenceWatch: PreferenceWatch {
        path: fonts.preference.path
        ancestor: Eitr.Paths.config("")
        onChanged: fonts.preference.reload()
    }
    property FileView preference: FileView {
        path: Eitr.Paths.config("eitr/font.json")
        printErrors: false
        onLoadFailed: fonts.family = "JetBrainsMono Nerd Font"
        onLoaded: {
            try {
                let choice = Eitr.Paths.settings(text()).family;
                fonts.family = typeof choice === "string" && choice.length ? choice : "JetBrainsMono Nerd Font";
            } catch (error) { console.warn("Invalid font settings:", error); }
        }
    }
}
