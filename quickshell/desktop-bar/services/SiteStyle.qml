pragma Singleton
import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr

Scope {
    id: style
    property bool light: false
    readonly property string mono: "JetBrainsMono Nerd Font"
    readonly property string carved: cinzel.name
    readonly property string serif: cormorant.name
    FontLoader { id: cinzel; source: "../assets/fonts/Cinzel-500.ttf" }
    FontLoader { source: "../assets/fonts/Cinzel-700.ttf" }
    FontLoader { id: cormorant; source: "../assets/fonts/CormorantGaramond-500.ttf" }
    PreferenceWatch {
        path: Eitr.Paths.config("theme/current/light.mode")
        ancestor: Eitr.Paths.config("theme")
        onChanged: marker.reload()
    }
    FileView {
        id: marker
        path: Eitr.Paths.config("theme/current/light.mode")
        printErrors: false
        onLoaded: style.light = true
        onLoadFailed: style.light = false
    }
    readonly property color bg: light ? "#f2ecdf" : "#000000"
    readonly property color night: light ? "#e8e0d2" : "#0a0909"
    readonly property color surface: light ? "#fbf6ed" : "#131111"
    readonly property color raised: light ? "#e5daca" : "#1e1a1a"
    readonly property color fg: light ? "#292521" : "#e4dcd2"
    readonly property color muted: light ? "#625b53" : "#9a8f86"
    readonly property color accent: light ? "#9c303b" : "#d4545c"
    readonly property color aurora: light ? "#356d68" : "#6f9590"
    readonly property color violet: light ? "#75425e" : "#9a5a7a"
    readonly property color bronze: light ? "#795823" : "#b08d57"
    readonly property color line: light ? "#2531271b" : "#14ffffff"
    readonly property color lineStrong: light ? "#4531271b" : "#26ffffff"
    readonly property color glow: light ? "#209c303b" : "#40a8323a"
    readonly property color primaryStart: light ? "#91313b" : "#c8424b"
    readonly property color primaryEnd: light ? "#91313b" : "#8f2830"
    readonly property color primaryInk: light ? "#fff3e7" : "#f6ece2"
}
