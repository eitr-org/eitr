import QtQuick
import Eitr as Eitr
import Quickshell

ThemedPopup {
    id: menu
    required property var service
    property string kind: "tailscale"
    property int maximumHeight: 700
    implicitWidth: 468
    implicitHeight: Math.min(content.implicitHeight + verticalContentInset, maximumHeight)
    onOpenedChanged: if (opened) service.refresh()
    Flickable {
        anchors.fill: parent
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        RemoteAccessContent {
            id: content
            width: parent.width
            kind: menu.kind
            state: menu.service.state
            busy: menu.service.busy
            foreground: menu.foreground
            accent: menu.accent
            background: menu.background
            onSettingsRequested: {
                menu.opened = false;
                Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:remote-access"]);
            }
            onActionRequested: function(sourceMenu, source) {
                menu.opened = false;
                Quickshell.execDetached(["python3", Quickshell.shellDir + "/scripts/menu-action.py", sourceMenu, source]);
            }
        }
    }
}
