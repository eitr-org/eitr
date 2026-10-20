import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    implicitWidth: 468
    implicitHeight: 528
    property var devices: []
    readonly property var device: devices.length ? devices[0] : null
    readonly property var details: device ? device.details : ({})
    readonly property var connected: device ? device.networks.find(n => n.connected) : null
    readonly property var groups: [
        {title: Eitr.I18n.tr("CONNECTED"), networks: device ? device.networks.filter(n => n.connected) : []},
        {title: Eitr.I18n.tr("KNOWN NETWORKS"), networks: device ? device.networks.filter(n => n.known && !n.connected) : []},
        {title: Eitr.I18n.tr("OTHER NETWORKS"), networks: device ? device.networks.filter(n => !n.known && !n.connected) : []}
    ]
    property var selectedNetwork: null
    property string message: ""
    property string secret: ""
    property string backend: "iwd"
    property string connectDevicePath: ""
    property var credentials: ({})
    readonly property bool enterprise: selectedNetwork !== null && selectedNetwork.type === "8021x"
    property string eapMethod: "peap"
    function clearEnterprise() {
        identity.text = ""; anonymousIdentity.text = ""; serverDomain.text = "";
        caCertificate.text = ""; enterprisePassword.text = ""; credentials = ({});
    }
    property string pendingRemoval: ""
    property bool sharing: false
    property var shareNetwork: null
    property string qrImage: ""
    property string qrError: ""
    property string qrSecret: ""
    function closeShare() { sharing = false; qrImage = ""; qrSecret = ""; qrPassword.text = ""; shareNetwork = null; }
    function generateQr() { if (!qrQuery.running && shareNetwork) { qrSecret = qrPassword.text; qrQuery.running = true; } }
    function openShare() {
        shareNetwork = connected;
        qrImage = ""; qrError = ""; qrPassword.text = "";
        sharing = true;
        if (shareNetwork.type === "open") generateQr();
        else qrPassword.forceActiveFocus();
    }
    property bool busy: operation ? operation.running : false
    property var latency: ({})
    property string helper: Quickshell.shellDir + "/scripts/wifi-popup.py"
    function refresh() { if (!query.running) query.running = true; }
    function act(kind, path, extra) {
        if (busy) return;
        message = "";
        operation.command = ["python3", helper, kind, path];
        if (extra !== undefined) operation.command = operation.command.concat([extra]);
        operation.running = true;
    }
    function choose(network) {
        if (network.connected || network.available === false) return;
        connectDevicePath = network.devicePath || "";
        if (network.type === "unsupported") { message = "This network needs advanced security configuration."; return; }
        if (network.type === "open" || network.known) { secret = ""; act("connect", network.path); }
        else {
            clearEnterprise(); selectedNetwork = network; password.text = "";
            if (enterprise) identity.forceActiveFocus(); else password.forceActiveFocus();
        }
    }
    function probe() { if (visible && device && device.state === "connected" && !pingQuery.running) { pingQuery.command = ["python3", helper, "probe", device.name]; pingQuery.running = true; } }
    onOpenedChanged: {
        if (opened) { message = ""; latency = ({}); refresh(); }
        else { selectedNetwork = null; secret = ""; pendingRemoval = ""; password.text = ""; clearEnterprise(); closeShare(); }
    }
    Timer { interval: 2000; running: menu.opened; repeat: true; onTriggered: menu.refresh() }
    Timer { interval: 15000; running: menu.opened; repeat: true; onTriggered: menu.probe() }
    Process {
        id: query
        command: ["python3", menu.helper, "status"]
        stdout: StdioCollector { id: snapshot }
        onExited: {
            try {
                var result = JSON.parse(snapshot.text);
                if (result.error) menu.message = result.error;
                else {
                    menu.devices = result.devices;
                    menu.backend = result.backend || "iwd";
                    if (menu.device && menu.latency.ping === undefined) menu.probe();
                }
            } catch (e) { menu.message = "WiFi unavailable"; }
        }
    }
    Process {
        id: operation
        stdinEnabled: true
        onStarted: {
            write(JSON.stringify(Object.assign({password: menu.secret, devicePath: menu.connectDevicePath}, menu.credentials)) + "\n");
            menu.secret = ""; menu.clearEnterprise();
        }
        stdout: StdioCollector { id: operationOutput }
        onExited: {
            try { var result = JSON.parse(operationOutput.text); menu.message = result.error || ""; }
            catch (e) { menu.message = "Could not complete request"; }
            menu.refresh();
        }
    }
    Process {
        id: qrQuery
        command: ["python3", Quickshell.shellDir + "/scripts/wifi-qr.py"]
        stdinEnabled: true
        onStarted: { write(JSON.stringify({network: menu.shareNetwork, password: menu.qrSecret}) + "\n"); menu.qrSecret = ""; qrPassword.text = ""; }
        stdout: StdioCollector { id: qrOutput }
        onExited: {
            if (!menu.sharing) return;
            try { var result = JSON.parse(qrOutput.text); menu.qrImage = result.image || ""; menu.qrError = result.error || ""; }
            catch (e) { menu.qrError = "Could not generate QR code"; }
        }
    }
    Process {
        id: pingQuery
        stdout: StdioCollector { id: pingOutput }
        onExited: { try { menu.latency = JSON.parse(pingOutput.text); } catch (e) {} }
    }
    Item {
        anchors.fill: parent
        anchors.margins: 0
        Column {
            id: wifiHeaderContent
            visible: !menu.sharing && !menu.enterprise
            width: parent.width
            spacing: 14
            Item {
                width: parent.width
                height: 42
                PanelHeading {
                    width: parent.width - 166
                    anchors.verticalCenter: parent.verticalCenter
                    text: menu.connected ? menu.connected.name : Eitr.I18n.tr("WiFi")
                    subtitle: menu.busy ? Eitr.I18n.tr("UPDATING...") : menu.device ? String(menu.device.state).toUpperCase() : Eitr.I18n.tr("NO ADAPTER")
                    foreground: menu.foreground; accent: menu.accent; rune: "connectivity"
                }
                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 12
                    PanelButton {
                        id: qrButton
                        text: "󰐲"; icon: true; compactIconBackground: true; height: 32; foreground: menu.foreground
                        available: !!menu.connected && ["open", "psk"].indexOf(menu.connected.type) >= 0 && !qrQuery.running
                        onClicked: menu.openShare()
                        HoverHandler { id: qrHover }
                        BarTooltip { target: qrButton; hovered: qrHover.hovered; text: Eitr.I18n.tr("Share WiFi"); foreground: menu.foreground; background: menu.background }
                    }
                    PanelButton {
                        id: scanButton
                        text: "󰑓"; icon: true; compactIconBackground: true; height: 32; foreground: menu.foreground
                        loading: operation.running && operation.command[2] === "scan"
                        available: !!menu.device && menu.device.powered && !menu.busy && !menu.device.scanning
                        onClicked: menu.act("scan", menu.device.path)
                        HoverHandler { id: scanHover }
                        BarTooltip { target: scanButton; hovered: scanHover.hovered; text: Eitr.I18n.tr("Scan"); foreground: menu.foreground; background: menu.background }
                    }
                    PanelSwitch { checked: !!menu.device && menu.device.powered; enabled: !!menu.device && !menu.busy; foreground: menu.foreground; accent: menu.accent; onClicked: menu.act("power", menu.device.path, checked ? "true" : "false") }
                }
            }
            Column {
                width: parent.width
                spacing: PanelStyle.selectionRowGap
                Repeater {
                    model: [
                        ["Ping", menu.latency.ping != null ? Math.round(menu.latency.ping) + " ms" : "--", "Wi-Fi Band", menu.details.band || "--"],
                        ["IP Address", menu.details.ip || "--", "Gateway", menu.details.gateway || "--"]
                    ]
                    Item {
                        required property var modelData
                        width: wifiHeaderContent.width; height: 16
                        Text { text: parent.modelData[0]; color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { x: 70; width: 125; horizontalAlignment: Text.AlignRight; text: parent.modelData[1]; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { x: 210; text: parent.modelData[2]; color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { anchors.right: parent.right; text: parent.modelData[3]; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                    }
                }
            }
            Column {
                visible: menu.selectedNetwork !== null; width: parent.width; spacing: PanelStyle.selectionRowGap
                PanelHeading { width: parent.width; elide: Text.ElideRight; text: menu.selectedNetwork ? menu.selectedNetwork.name : ""; foreground: menu.foreground; accent: menu.accent; rune: "connectivity"; }
                TextField {
                    id: password; width: parent.width; placeholderText: Eitr.I18n.tr("Password"); echoMode: TextInput.Password; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    placeholderTextColor: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.5)
                    background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08); border.color: password.activeFocus ? menu.accent : "transparent" }
                    HoverHandler { cursorShape: Qt.IBeamCursor }
                    onAccepted: connectButton.clicked()
                }
                Row {
                    spacing: PanelStyle.selectionRowGap
                    PanelButton { id: connectButton; text: Eitr.I18n.tr("Connect"); width: 90; foreground: menu.foreground; available: !menu.busy && password.text.length > 0; onClicked: { if (!available) return; menu.secret = password.text; menu.act("connect", menu.selectedNetwork.path); menu.selectedNetwork = null; password.text = ""; } }
                    PanelButton { text: Eitr.I18n.tr("Cancel"); foreground: menu.foreground; onClicked: { menu.selectedNetwork = null; password.text = ""; } }
                }
            }
            Text { visible: menu.message !== ""; width: parent.width; text: menu.message; wrapMode: Text.Wrap; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
            PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
        }
        Flickable {
            visible: !menu.sharing && !menu.enterprise
            anchors.top: wifiHeaderContent.bottom
            anchors.topMargin: 14
            anchors.bottom: parent.bottom
            width: parent.width
            contentHeight: networks.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: networks
                width: parent.width
                spacing: 14
                Repeater {
                    model: menu.groups
                    Column {
                        required property var modelData
                        width: networks.width; spacing: PanelStyle.selectionRowGap
                        Text { text: parent.modelData.title; color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { visible: parent.modelData.networks.length === 0; text: menu.device && menu.device.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No networks"); color: menu.foreground; opacity: 0.5; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                        Repeater {
                            model: parent.modelData.networks
                            Rectangle {
                                id: network
                                required property var modelData
                                width: networks.width; height: PanelStyle.selectionRowHeight; radius: DesktopStyle.radius(PanelStyle.controlRadius)
                                color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(modelData.connected, networkMouse.containsMouse))
                                border.width: PanelStyle.selectionBorderWidth(modelData.connected)
                                border.color: Qt.alpha(menu.foreground, PanelStyle.selectionBorderAlpha)
                                activeFocusOnTab: true
                                Keys.onReturnPressed: if (!menu.busy) menu.choose(modelData)
                                Text { x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter; text: "󰤨"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize }
                                Column {
                                    x: PanelStyle.selectionTextInset; width: parent.width - networkActions.width - 52; anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionDetailGap
                                    Text { width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText; text: network.modelData.name; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                                    Text { visible: network.modelData.connected || network.modelData.available === false; text: network.modelData.connected ? Eitr.I18n.tr("Connected") : Eitr.I18n.tr("Offline"); color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                                }
                                MouseArea { id: networkMouse; anchors.fill: parent; hoverEnabled: true; enabled: !menu.busy && !network.modelData.connected && network.modelData.available !== false; cursorShape: Qt.PointingHandCursor; onClicked: menu.choose(network.modelData) }
                                Row {
                                    id: networkActions
                                    anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionActionGap
                                    Text { visible: network.modelData.available !== false; anchors.verticalCenter: parent.verticalCenter; text: Math.round(network.modelData.strength) + "%"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                                    Text { visible: network.modelData.type !== "open"; anchors.verticalCenter: parent.verticalCenter; text: "󰌾"; color: menu.foreground; opacity: 0.65; font.family: DesktopFonts.family; font.pixelSize: 14 }
                                    PanelButton {
                                        id: disconnectButton
                                        visible: network.modelData.connected
                                        text: "󰖪"; icon: true; width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
                                        iconOffsetX: -2
                                        foreground: menu.foreground; available: !menu.busy
                                        Accessible.name: Eitr.I18n.tr("Disconnect")
                                        onClicked: menu.act("disconnect", menu.device.path)
                                        HoverHandler { id: disconnectHover }
                                        BarTooltip { target: disconnectButton; hovered: disconnectHover.hovered; text: Eitr.I18n.tr("Disconnect"); foreground: menu.foreground; background: menu.background }
                                    }
                                    PanelButton {
                                        id: removeButton
                                        visible: network.modelData.known && !network.modelData.connected
                                        text: menu.pendingRemoval === network.modelData.knownPath ? "" : "󰆴"
                                        icon: true; width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight; foreground: menu.foreground
                                        Accessible.name: menu.pendingRemoval === network.modelData.knownPath ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Remove")
                                        available: !menu.busy && !!network.modelData.knownPath
                                        onClicked: {
                                            if (menu.pendingRemoval === network.modelData.knownPath) {
                                                menu.act("forget", network.modelData.knownPath);
                                                menu.pendingRemoval = "";
                                            } else menu.pendingRemoval = network.modelData.knownPath;
                                        }
                                        HoverHandler { id: removeHover }
                                        BarTooltip { target: removeButton; hovered: removeHover.hovered; text: menu.pendingRemoval === network.modelData.knownPath ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Remove"); foreground: menu.foreground; background: menu.background }
                                    }
                                }
                                BarTooltip { target: network; hovered: networkMouse.containsMouse && !removeHover.hovered; text: network.modelData.connected || network.modelData.available === false ? "" : Eitr.I18n.tr("Connect"); foreground: menu.foreground; background: menu.background }
                            }
                        }
                    }
                }
            }
        }
        Flickable {
            visible: menu.enterprise
            anchors.fill: parent
            contentHeight: enterpriseFields.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: enterpriseFields
                width: parent.width
                spacing: PanelStyle.selectionRowGap
                PanelHeading { width: parent.width; text: menu.selectedNetwork ? menu.selectedNetwork.name : ""; elide: Text.ElideRight; foreground: menu.foreground; accent: menu.accent; rune: "connectivity"; }
                Text { width: parent.width; text: Eitr.I18n.tr("ENTERPRISE WI-FI"); color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                Row {
                    spacing: 8
                    PanelButton { width: 190; text: Eitr.I18n.tr("PEAP / MSCHAPv2"); selected: menu.eapMethod === "peap"; foreground: menu.foreground; onClicked: menu.eapMethod = "peap" }
                    PanelButton { width: 150; text: Eitr.I18n.tr("TTLS / PAP"); selected: menu.eapMethod === "ttls"; foreground: menu.foreground; onClicked: menu.eapMethod = "ttls" }
                }
                TextField { id: identity; width: parent.width; placeholderText: Eitr.I18n.tr("Username"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(menu.foreground, 0.08) } }
                TextField { id: anonymousIdentity; width: parent.width; placeholderText: Eitr.I18n.tr("Anonymous identity (optional)"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(menu.foreground, 0.08) } }
                TextField { id: enterprisePassword; width: parent.width; placeholderText: Eitr.I18n.tr("Password"); echoMode: TextInput.Password; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(menu.foreground, 0.08) } }
                TextField { id: serverDomain; width: parent.width; placeholderText: Eitr.I18n.tr("Authentication server domain"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(menu.foreground, 0.08) } }
                TextField { id: caCertificate; width: parent.width; placeholderText: Eitr.I18n.tr("CA certificate path (.pem)"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(menu.foreground, 0.08) } }
                Text { width: parent.width; wrapMode: Text.Wrap; text: Eitr.I18n.tr("Use the certificate and server domain supplied by your network administrator. Certificate validation is required."); color: menu.foreground; opacity: 0.65; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                Row {
                    spacing: 8
                    PanelButton {
                        text: Eitr.I18n.tr("Connect"); foreground: menu.foreground
                        available: !menu.busy && identity.text.length > 0 && enterprisePassword.text.length > 0 && serverDomain.text.length > 0 && caCertificate.text.length > 0
                        onClicked: {
                            if (!available) return;
                            menu.credentials = {name: menu.selectedNetwork.name, eap: menu.eapMethod, identity: identity.text,
                                anonymous: anonymousIdentity.text, password: enterprisePassword.text,
                                domain: serverDomain.text, ca: caCertificate.text};
                            menu.act("connect", menu.selectedNetwork.path);
                            menu.selectedNetwork = null;
                        }
                    }
                    PanelButton { text: Eitr.I18n.tr("Cancel"); foreground: menu.foreground; onClicked: { menu.selectedNetwork = null; menu.clearEnterprise(); } }
                }
            }
        }
        Column {
            visible: menu.sharing
            width: parent.width
            spacing: 14
            Row {
                width: parent.width; spacing: 8
                PanelHeading { width: parent.width - 42; anchors.verticalCenter: parent.verticalCenter; text: menu.shareNetwork ? menu.shareNetwork.name : ""; elide: Text.ElideRight; textFormat: Text.PlainText; foreground: menu.foreground; accent: menu.accent; rune: "connectivity"; }
                PanelButton { text: "×"; width: 34; height: 34; foreground: menu.foreground; onClicked: menu.closeShare() }
            }
            TextField {
                id: qrPassword
                visible: menu.qrImage === "" && menu.shareNetwork && menu.shareNetwork.type !== "open"
                width: parent.width; placeholderText: Eitr.I18n.tr("WiFi password"); echoMode: TextInput.Password
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                color: menu.foreground; placeholderTextColor: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.5)
                background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08); border.color: qrPassword.activeFocus ? menu.accent : "transparent" }
                HoverHandler { cursorShape: Qt.IBeamCursor }
                onAccepted: if (text.length > 0) menu.generateQr()
            }
            PanelButton { visible: qrPassword.visible; text: Eitr.I18n.tr("Show QR"); width: 100; foreground: menu.foreground; available: qrPassword.text.length > 0 && !qrQuery.running; onClicked: menu.generateQr() }
            Image { visible: menu.qrImage !== ""; anchors.horizontalCenter: parent.horizontalCenter; width: 300; height: 300; source: menu.qrImage; fillMode: Image.PreserveAspectFit; smooth: false }
            Text { width: parent.width; text: menu.qrError; visible: text !== ""; color: menu.foreground; wrapMode: Text.Wrap; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
        }
    }
}
