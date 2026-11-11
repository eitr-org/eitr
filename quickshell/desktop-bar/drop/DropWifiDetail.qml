import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// WiFi opened in Drop's quick controls: networks grouped as in the WiFi panel (shared
// WifiNetworkRow), a scan when it opens, and a password field for a new secured network.
// Enterprise networks are set up in Settings › Connections, which owns their credentials form.
Column {
    id: detail
    required property var barHost
    required property var wifi
    required property color foreground
    required property color background
    required property color accent
    required property bool shown
    property var asking: null
    property string pendingRemoval: ""
    readonly property var device: wifi.device
    readonly property var groups: [
        {title: Eitr.I18n.tr("CONNECTED"), networks: device ? device.networks.filter(network => network.connected) : []},
        {title: Eitr.I18n.tr("KNOWN NETWORKS"), networks: device ? device.networks.filter(network => network.known && !network.connected) : []},
        {title: Eitr.I18n.tr("OTHER NETWORKS"), networks: device ? device.networks.filter(network => !network.known && !network.connected) : []}
    ]
    onShownChanged: {
        asking = null; pendingRemoval = "";
        if (shown && device && device.powered && !wifi.busy) act("scan", device.path);
    }
    function act(kind, path, extra, password) {
        wifi.act(detail, kind, path, extra, {password: password || "", devicePath: asking ? asking.devicePath || "" : ""});
    }
    function choose(network) {
        if (network.connected || network.available === false) return;
        if (network.type === "open" || network.known) { act("connect", network.path); return; }
        if (network.type === "8021x" || network.type === "unsupported") { barHost.closePanels(); barHost.host.showSettings("connections"); return; }
        asking = network;
        Qt.callLater(() => password.forceActiveFocus());
    }
    spacing: 10

    Row {
        visible: !!detail.asking
        width: parent.width; spacing: 8
        PanelTextField {
            id: password
            width: parent.width - connect.width - parent.spacing; height: 32
            echoMode: TextInput.Password
            foreground: detail.foreground; accent: detail.accent
            placeholderText: detail.asking ? Eitr.I18n.tr("Password for {name}", {name: detail.asking.name}) : ""
            onAccepted: connect.clicked()
            Keys.onEscapePressed: { detail.asking = null; text = ""; }
        }
        PanelButton {
            id: connect
            width: 90; height: 32
            text: Eitr.I18n.tr("Connect"); foreground: detail.foreground
            available: password.text.length > 0 && !detail.wifi.busy
            onClicked: {
                if (!available) return;
                detail.act("connect", detail.asking.path, undefined, password.text);
                detail.asking = null; password.text = "";
            }
        }
    }
    Text {
        visible: !!detail.device && !detail.device.powered
        text: Eitr.I18n.tr("WiFi is off")
        color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    Repeater {
        model: detail.device && detail.device.powered ? detail.groups : []
        Column {
            id: group
            required property var modelData
            width: detail.width; spacing: PanelStyle.selectionRowGap
            visible: modelData.networks.length > 0 || modelData.title === Eitr.I18n.tr("OTHER NETWORKS")
            Text { text: group.modelData.title; color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            Text {
                visible: group.modelData.networks.length === 0
                text: detail.device && detail.device.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No networks")
                color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize
            }
            Repeater {
                model: group.modelData.networks
                WifiNetworkRow {
                    width: detail.width
                    foreground: detail.foreground; background: detail.background
                    busy: detail.wifi.busy; pendingRemoval: detail.pendingRemoval
                    onChosen: detail.choose(modelData)
                    onDisconnectRequested: detail.act("disconnect", detail.device.path)
                    onRemoveRequested: confirmed => {
                        if (confirmed) { detail.act("forget", modelData.knownPath); detail.pendingRemoval = ""; }
                        else detail.pendingRemoval = modelData.knownPath;
                    }
                }
            }
        }
    }
}
