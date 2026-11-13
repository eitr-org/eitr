import QtQuick
import QtQuick.Window
import "LoginDisplay.js" as LoginDisplay

// SDDM opens this on every display. The design (Design.qml) runs only on the main one;
// the others stay black, so the greeter draws and animates a single screen.
Rectangle {
    id: display
    color: "#000000"
    focus: true
    // SDDM loads this before moving the window to its display: decide once it is shown there.
    readonly property bool shown: !!Window.window && Window.window.visible
    readonly property bool main: shown && LoginDisplay.isMain(Screen.name, Qt.application.screens)
    // X11's own main display may be another one: take the keyboard to the login screen.
    onMainChanged: if (main) Window.window.requestActivate()
    // Designs hand focus to their password field when their root gains it, as in the
    // session lockscreen (shell.qml); inside a Loader nothing gives it to them.
    readonly property bool windowActive: Window.active
    onWindowActiveChanged: if (windowActive && design.item) design.item.forceActiveFocus()
    Loader {
        id: design
        anchors.fill: parent
        focus: true
        active: display.main
        source: "Design.qml"
        onLoaded: item.forceActiveFocus()
    }
}
