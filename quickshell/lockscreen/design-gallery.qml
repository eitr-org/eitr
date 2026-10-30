import Eitr as Eitr
import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import Quickshell.Io

ShellRoot {
    id: gallery
    property bool light: false
    property bool controlsVisible: true
    property int selectedIndex: 0
    readonly property var designs: [
        {id: "clockwork/neo-orbital", title: Eitr.I18n.tr("Clockwork Neo Orbital")},
        {id: "clockwork/tape", title: Eitr.I18n.tr("Clockwork Tape")},
        {id: "eitr", title: Eitr.I18n.tr("Eitr")},
        {id: "girl-coffee", title: Eitr.I18n.tr("Girl · Coffee")},
        {id: "girl-pillow", title: Eitr.I18n.tr("Girl · Pillow")},
        {id: "material-you-dark", title: Eitr.I18n.tr("Material Dark")},
        {id: "material-you", title: Eitr.I18n.tr("Material Light")},
        {id: "nothing", title: Eitr.I18n.tr("Nothing")},
        {id: "theme-wallpaper", title: Eitr.I18n.tr("Theme Wallpaper")}
    ]
    readonly property var backgrounds: ({"material-you": "background.svg", "material-you-dark": "background.svg", "girl-coffee": "background.png", "girl-pillow": "background.png"})
    property var wallpaperConfig: ({})
    property var eitrSettings: ({})
    readonly property bool isLockPreview: true
    readonly property var config: designs[selectedIndex].id === "theme-wallpaper" ? wallpaperConfig : ({themeMode: light ? "light" : "dark", reduceMotion: eitrSettings.reduceMotion === true, clock: eitrSettings.clock || "24h", background: backgrounds[designs[selectedIndex].id] || ""})
    Process {
        running: true
        command: ["python3", decodeURIComponent(Qt.resolvedUrl("scripts/settings.py").toString().replace("file://", "")), "config", "eitr"]
        stdout: StdioCollector { onStreamFinished: gallery.eitrSettings = JSON.parse(text) }
    }
    Process {
        id: wallpaperSettings
        running: true
        command: ["python3", decodeURIComponent(Qt.resolvedUrl("scripts/settings.py").toString().replace("file://", "")), "config", "theme-wallpaper"]
        stdout: StdioCollector { onStreamFinished: gallery.wallpaperConfig = JSON.parse(text) }
    }
    readonly property var sddm: mockAuth
    readonly property var userModel: users
    readonly property var sessionModel: sessions
    readonly property var keyboard: keyboardState
    QtObject { id: keyboardState; property bool numLock: false }
    function choose(index) {
        if (index < 0 || index >= designs.length) return;
        selectedIndex = index;
        light = designs[index].id === "material-you";
        if (designs[index].id === "theme-wallpaper") wallpaperSettings.running = true;
    }
    function stop() { window.visible = false; quitDelay.start(); }
    Timer { id: quitDelay; interval: 500; onTriggered: Qt.quit() }
    Timer { interval: 1200000; running: true; onTriggered: gallery.stop() }
    QtObject {
        id: mockAuth
        readonly property bool quickshellLock: false
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) {}
        function reboot() {}
        function powerOff() {}
        function suspend() {}
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "EITR"; function rowCount() { return count; } ListElement { name: "astrid"; realName: "Astrid Solberg" } ListElement { name: "bjorn"; realName: "Bjørn Lund" } ListElement { name: "freya"; realName: "Freya Lind" } }
    ListModel { id: sessions; property int lastIndex: 0; function rowCount() { return count; } ListElement { name: "Current session" } }
    PanelWindow {
        id: window
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "eitr-lockscreen-gallery"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        color: "transparent"
        Loader {
            id: designLoader
            anchors.fill: parent
            source: Qt.resolvedUrl("themes/" + gallery.designs[gallery.selectedIndex].id + "/Main.qml")
            onLoaded: {
                item.forceActiveFocus();
                if (item.previewFinished) item.previewFinished.connect(function() { gallery.stop(); });
            }
        }
        Row {
            visible: gallery.controlsVisible
            anchors.horizontalCenter: parent.horizontalCenter; y: 24; spacing: 10
            ComboBox {
                width: 350; height: 38; model: gallery.designs; textRole: "title"; currentIndex: gallery.selectedIndex
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 12
                onActivated: index => gallery.choose(index)
            }
            Button { text: Eitr.I18n.tr("Previous"); height: 38; onClicked: gallery.choose((gallery.selectedIndex + gallery.designs.length - 1) % gallery.designs.length) }
            Button { text: Eitr.I18n.tr("Next"); height: 38; onClicked: gallery.choose((gallery.selectedIndex + 1) % gallery.designs.length) }
            Button { text: gallery.light ? Eitr.I18n.tr("Dark") : Eitr.I18n.tr("Light"); height: 38; onClicked: gallery.light = !gallery.light }
            Button { text: Eitr.I18n.tr("Close"); height: 38; onClicked: gallery.stop() }
        }
        Text {
            visible: gallery.controlsVisible
            anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 20
            text: Eitr.I18n.tr("EITR DESIGN PREVIEW · AUTHENTICATION DISABLED · ESC TO CLOSE")
            color: gallery.light ? "#302d3b" : "#e9e1d5"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 11
        }
        Shortcut { sequence: "Escape"; onActivated: gallery.stop() }
        Shortcut { sequence: "Alt+Right"; onActivated: gallery.choose((gallery.selectedIndex + 1) % gallery.designs.length) }
        Shortcut { sequence: "Alt+Left"; onActivated: gallery.choose((gallery.selectedIndex + gallery.designs.length - 1) % gallery.designs.length) }
    }
    IpcHandler {
        target: "gallery"
        function show(index: int): void { gallery.choose(index); }
        function controls(enabled: bool): void { gallery.controlsVisible = enabled; }
        function stop(): void { gallery.stop(); }
        function status(): string { return JSON.stringify({design: gallery.designs[gallery.selectedIndex].id, error: !window.visible ? "closed" : designLoader.status === Loader.Error ? "Loading failed" : ""}); }
    }
}
