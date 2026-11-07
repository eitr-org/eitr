import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../NetworkStatus.js" as NetworkStatus

// Settings > Connections > Wi-Fi: the same network service and actions as the bar's WiFi
// panel, laid out for the wide Settings window.
Column {
    id: page
    objectName: "settings-wifi-page"
    required property var networkService
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property string message: ""
    property var selectedNetwork: null
    property string pendingRemoval: ""
    // The network a row click is connecting to, and the row that shows a failure.
    property string connectingPath: ""
    property string failedPath: ""
    property string failure: ""
    readonly property var snapshot: networkService ? networkService.details.data || {} : {}
    readonly property var devices: snapshot.devices || []
    readonly property var device: devices[0] || null
    readonly property var connected: device ? (device.networks || []).find(network => network.connected) || null : null
    readonly property var details: device ? device.details || {} : {}
    readonly property var latency: networkService ? networkService.latency.data || {} : {}
    readonly property bool busy: !!networkService && networkService.busy
    readonly property bool scanning: (busy && networkService.actionKind === "scan") || (!!device && !!device.scanning)
    readonly property var securityLabels: ({open: Eitr.I18n.tr("Open"), psk: Eitr.I18n.tr("WPA Personal"), sae: Eitr.I18n.tr("WPA3 Personal"), "8021x": Eitr.I18n.tr("Enterprise (802.1X)")})
    readonly property var fields: connected ? [
        {label: Eitr.I18n.tr("Signal"), value: connected.strength == null ? "" : NetworkStatus.signalGlyph(connected.strength, snapshot.backend) + "  " + Math.round(connected.strength) + "%"},
        {label: Eitr.I18n.tr("Security"), value: details.security || securityLabels[connected.type] || connected.type || ""},
        {label: Eitr.I18n.tr("Wi-Fi standard"), value: details.standard},
        {label: Eitr.I18n.tr("Wi-Fi Band"), value: details.band},
        {label: Eitr.I18n.tr("Channel"), value: details.channel ? String(details.channel) + (details.frequency ? " · " + details.frequency + " MHz" : "") : ""},
        {label: Eitr.I18n.tr("Link speed"), value: details.speed ? details.speed + " Mbit/s" : ""},
        {label: Eitr.I18n.tr("IPv4"), value: details.ip},
        {label: Eitr.I18n.tr("IPv6"), value: details.ipv6},
        {label: Eitr.I18n.tr("Gateway"), value: details.gateway},
        {label: Eitr.I18n.tr("DNS"), value: details.dns},
        {label: Eitr.I18n.tr("MAC address"), value: details.mac},
        {label: Eitr.I18n.tr("Interface"), value: details.interface || device.name},
        {label: Eitr.I18n.tr("WiFi backend"), value: snapshot.backend === "networkmanager" ? "NetworkManager" : snapshot.backend},
        {label: Eitr.I18n.tr("Ping"), value: latency.ping == null ? "" : Math.round(latency.ping) + " ms"}
    ].filter(field => field.value !== undefined && field.value !== null && field.value !== "") : []
    width: parent ? parent.width : 0
    spacing: 18
    function demand() {
        if (!networkService) return;
        networkService.detach(page);
        if (active && live) { networkService.observe(page); networkService.observe(page, "latency"); }
    }
    onActiveChanged: demand()
    Component.onDestruction: if (networkService) networkService.detach(page)
    function networkActionFinished(error, code) {
        const text = error ? networkService.actionMessage(error) : "";
        if (connectingPath !== "") {
            failedPath = text ? connectingPath : "";
            failure = text;
            message = "";
        } else message = text;
    }
    function act(kind, path, extra, input) {
        if (!live || !networkService) return;
        connectingPath = kind === "connect" ? path : "";
        if (kind === "connect") { failedPath = ""; failure = ""; }
        networkService.act(page, kind, path, extra || "", input || {});
    }
    function connect(network, input) {
        act("connect", network.path, "", Object.assign({devicePath: network.devicePath || ""}, input || {}));
    }
    // A row click: known and open networks connect at once; others ask for credentials first.
    function choose(network) {
        if (network.connected || network.available === false || busy) return;
        if (network.known || network.type === "open") connect(network);
        else selectedNetwork = network;
    }
    function connecting(network) { return busy && connectingPath === network.path; }
    function scan() { if (device && device.powered && !scanning && !busy) act("scan", device.path); }
    function dismiss() {
        if (selectedNetwork) { selectedNetwork = null; return true; }
        if (pendingRemoval) { pendingRemoval = ""; return true; }
        return false;
    }
    function backendAction(title) {
        if (live) Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), "network-backend", title]);
    }
    ToggleRow {
        objectName: "settings-wifi-power"
        text: Eitr.I18n.tr("Wi-Fi")
        description: !page.device ? Eitr.I18n.tr("No WiFi adapter")
            : Eitr.I18n.tr("Turn Wi-Fi on or off") + (page.details.interface || page.device.name ? " · " + (page.details.interface || page.device.name) : "")
        foreground: page.foreground
        accent: page.accent
        checked: !!page.device && page.device.powered
        available: !!page.device && !page.busy
        onToggled: checked => page.act("power", page.device.path, checked ? "true" : "false")
    }
    ControlCard {
        title: Eitr.I18n.tr("Connected network")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        spacing: 12
        Item {
            width: parent.width
            height: Math.max(connectedName.implicitHeight, disconnectButton.height)
            SettingsText {
                id: connectedName
                width: parent.width - disconnectButton.width - 12
                anchors.verticalCenter: parent.verticalCenter
                text: page.connected ? page.connected.name : Eitr.I18n.tr("Not connected")
                textFormat: Text.PlainText
                font.pixelSize: PanelStyle.headingSize
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }
            PanelButton {
                id: disconnectButton
                visible: !!page.connected
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                width: 120; foreground: page.foreground; text: Eitr.I18n.tr("Disconnect"); available: !page.busy
                onClicked: page.act("disconnect", page.device.path)
            }
        }
        Grid {
            id: detailsGrid
            objectName: "settings-wifi-details"
            width: parent.width
            columns: 2
            columnSpacing: 24
            rowSpacing: 8
            Repeater {
                model: page.fields
                Row {
                    required property var modelData
                    width: (detailsGrid.width - detailsGrid.columnSpacing) / 2
                    spacing: 12
                    SettingsText {
                        width: 116
                        text: parent.modelData.label
                        font.pixelSize: PanelStyle.captionSize
                        opacity: PanelStyle.secondaryTextOpacity
                        wrapMode: Text.NoWrap
                        elide: Text.ElideRight
                    }
                    SettingsText {
                        width: parent.width - 128
                        text: String(parent.modelData.value)
                        textFormat: Text.PlainText
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }
        }
    }
    Repeater {
        model: [{title: Eitr.I18n.tr("Known networks"), known: true}, {title: Eitr.I18n.tr("Other networks"), known: false}]
        ControlCard {
            id: group
            required property var modelData
            readonly property var networks: page.device ? (page.device.networks || []).filter(network => !network.connected && !!network.known === modelData.known) : []
            objectName: modelData.known ? "settings-wifi-known" : "settings-wifi-other"
            width: page.width
            title: modelData.title
            foreground: page.foreground
            surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
            spacing: PanelStyle.selectionRowGap
            headerActions: PanelButton {
                objectName: "settings-wifi-scan"
                visible: !group.modelData.known
                width: 84; height: 26
                text: Eitr.I18n.tr("Scan"); leadingIcon: "\uF021"
                textSize: PanelStyle.captionSize
                foreground: page.foreground
                leadingSpin: page.scanning
                available: !!page.device && page.device.powered && !page.busy && !page.scanning
                Accessible.name: page.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("Scan")
                onClicked: page.scan()
            }
            Repeater {
                model: group.networks
                ConnectionRow {
                    id: networkRow
                    required property var modelData
                    text: modelData.name
                    glyph: modelData.available === false ? "󰤮" : NetworkStatus.signalGlyph(modelData.strength || 0, page.snapshot.backend)
                    detail: modelData.available === false ? Eitr.I18n.tr("Offline")
                        : [modelData.strength == null ? "" : Math.round(modelData.strength) + "%", page.securityLabels[modelData.type] || ""].filter(part => part !== "").join(" · ")
                    error: page.failedPath === modelData.path ? page.failure : ""
                    loading: page.connecting(modelData)
                    activatable: !page.busy && modelData.available !== false
                    foreground: page.foreground
                    onActivated: page.choose(modelData)
                    PanelButton {
                        visible: !!networkRow.modelData.known
                        width: 80; height: 28; foreground: page.foreground
                        text: Eitr.I18n.tr("Forget"); available: !page.busy && !!networkRow.modelData.knownPath
                        onClicked: page.pendingRemoval = networkRow.modelData.knownPath
                    }
                }
            }
            SettingsText {
                visible: !group.networks.length
                text: !group.modelData.known && page.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No networks")
                opacity: PanelStyle.secondaryTextOpacity
            }
        }
    }
    SettingsWifiCredentials {
        width: parent.width
        visible: !!page.selectedNetwork
        network: page.selectedNetwork
        foreground: page.foreground; background: page.background; accent: page.accent
        busy: page.busy
        onCancelled: page.selectedNetwork = null
        onSubmitted: input => {
            page.connect(page.selectedNetwork, input);
            page.selectedNetwork = null;
        }
    }
    ControlCard {
        visible: page.pendingRemoval !== ""
        title: Eitr.I18n.tr("Forget network?")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        Row {
            spacing: 8
            PanelButton { width: 100; text: Eitr.I18n.tr("Cancel"); foreground: page.foreground; onClicked: page.pendingRemoval = "" }
            PanelButton { width: 100; text: Eitr.I18n.tr("Forget"); foreground: page.foreground; onClicked: { page.act("forget", page.pendingRemoval); page.pendingRemoval = ""; } }
        }
    }
    ControlCard {
        title: Eitr.I18n.tr("WiFi backend")
        foreground: page.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        ControlRow {
            text: Eitr.I18n.tr("WiFi backend")
            description: Eitr.I18n.tr("Applies after reboot; saved profiles are kept.")
            foreground: page.foreground
            ChoiceSegmented {
                width: parent.width
                foreground: page.foreground; gold: SettingsInk.gold; background: SettingsInk.background
                choices: [{id: "iwd", label: "iwd"}, {id: "NetworkManager", label: "NetworkManager"}]
                current: page.snapshot.backend === "networkmanager" ? "NetworkManager" : page.snapshot.backend || ""
                onChosen: value => page.backendAction(value)
            }
        }
        PanelButton {
            width: Math.min(parent.width, 320)
            text: Eitr.I18n.tr("Restore Original Network Configuration")
            foreground: page.foreground
            onClicked: page.backendAction("Restore Original Network Configuration")
        }
    }
    SettingsText {
        visible: text !== ""
        text: page.message || (page.networkService ? page.networkService.details.error || "" : "")
    }
}
