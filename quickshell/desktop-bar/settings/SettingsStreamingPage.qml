import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Eitr as Eitr

Flickable {
    id: view
    ScrollBar.vertical: PanelScrollBar { foreground: view.foreground }
    objectName: "settings-streaming-page"
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var snapshot: DesktopData.topics["remote.status"] || ({})
    readonly property var remoteState: snapshot.data || ({})
    readonly property var streaming: remoteState.streaming || ({})
    function demand() {
        DesktopData.releaseOwner(view);
        if (active && live) DesktopData.observe("remote.status", view);
    }
    onActiveChanged: demand()
    onLiveChanged: demand()
    Component.onDestruction: DesktopData.releaseOwner(view)
    function action(sourceMenu, source) {
        if (live && remoteState.allowed === true)
            Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), sourceMenu, source]);
    }
    contentHeight: content.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    Column {
        id: content
        width: view.width
        spacing: 18
        SettingsPageHeader { page: "streaming"; foreground: view.foreground }
        ControlCard {
            title: "Sunshine"
            foreground: view.foreground
            surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
            RemoteAccessContent {
                width: parent.width
                kind: "streaming"
                settingsMode: true
                state: ({streaming: Object.assign({}, view.streaming, {actions: (view.streaming.actions || []).filter(entry => entry.source !== "Connect to another PC")})})
                busy: !!view.snapshot.inFlight
                foreground: view.foreground; background: view.background; accent: view.accent
                enabled: view.remoteState.allowed === true
                onActionRequested: (sourceMenu, source) => view.action(sourceMenu, source)
            }
        }
        ControlCard {
            title: "Moonlight"
            foreground: view.foreground
            surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
            ControlRow {
                text: Eitr.I18n.tr("Connect to another PC")
                description: view.streaming.moonlightInstalled === undefined ? Eitr.I18n.tr("Status unavailable") : view.streaming.moonlightInstalled ? Eitr.I18n.tr("Installed") : Eitr.I18n.tr("Not installed")
                foreground: view.foreground
                PanelButton {
                    width: parent.width
                    text: view.streaming.moonlightInstalled ? Eitr.I18n.tr("Open") : Eitr.I18n.tr("Install")
                    foreground: view.foreground
                    available: view.remoteState.allowed === true && !view.snapshot.inFlight
                    onClicked: view.action("remote-access", "Connect to another PC")
                }
            }
        }
        PanelButton {
            objectName: "settings-page-handbook"
            width: 160
            text: Eitr.I18n.tr("Learn more")
            foreground: view.foreground
            onClicked: if (view.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", "remote-access"])
        }
    }
}
