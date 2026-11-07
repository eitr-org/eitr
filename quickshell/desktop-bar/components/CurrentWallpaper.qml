import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

// The wallpaper saved in eitr/appearance.json, for pictures of the current theme's art.
// `live` reads the file at all; `watching` follows later changes.
FileView {
    id: wallpaper
    property bool live: true
    property bool watching: live
    property url source: ""
    path: live ? Eitr.Paths.config("eitr/appearance.json") : ""
    printErrors: false
    watchChanges: watching
    onFileChanged: if (watching) reload()
    onLoaded: {
        try { const path = Eitr.Paths.settings(text()).wallpaper || ""; wallpaper.source = path ? "file://" + path : ""; }
        catch (error) { console.warn("Invalid appearance settings:", error); }
    }
}
