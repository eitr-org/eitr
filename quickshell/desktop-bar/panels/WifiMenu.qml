import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle
import QtQuick.Controls.Basic
import Quickshell

ThemedPopup {
    id: menu
    waitForFreshData: true
    implicitWidth: 468
    implicitHeight: 528
    required property var networkService
    property string detailsToken: ""
    property string latencyToken: ""
    function syncDemand() {
        if (opened && !detailsToken) detailsToken = networkService.observe(menu);
        if (!opened && detailsToken) { networkService.release(detailsToken); detailsToken = ""; }
        if (opened && visible && !latencyToken) latencyToken = networkService.observe(menu, "latency");
        if ((!opened || !visible) && latencyToken) { networkService.release(latencyToken); latencyToken = ""; }
    }
    onVisibleChanged: syncDemand()
    Component.onDestruction: {
        networkService.release(detailsToken);
        networkService.release(latencyToken);
        networkService.detach(menu);
    }
    function receiveDetails() {
        const state = networkService.details;
        updateContent(function() {
            if (state.updatedAt) {
                menu.applySnapshot("devices", state.data.devices);
                menu.backend = state.data.backend || "iwd";
            }
        });
    }
    Connections {
        target: menu.networkService
        function onDetailsChanged() { menu.receiveDetails(); }
    }
    property string networkErrorCode: ""
    function networkActionFinished(error, code) { networkErrorCode = code || ""; message = error; }
    function networkQrFinished(result) {
        if (!sharing) return;
        qrImage = result.image || "";
        qrError = result.error || "";
    }
    property var devices: []
    readonly property var device: devices.length ? devices[0] : null
    readonly property var details: device ? device.details : ({})
    readonly property var connected: device ? device.networks.find(network => network.connected) : null
    readonly property var groups: [
        {title: Eitr.I18n.tr("CONNECTED"), networks: device ? device.networks.filter(network => network.connected) : []},
        {title: Eitr.I18n.tr("KNOWN NETWORKS"), networks: device ? device.networks.filter(network => network.known && !network.connected) : []},
        {title: Eitr.I18n.tr("OTHER NETWORKS"), networks: device ? device.networks.filter(network => !network.known && !network.connected) : []}
    ]
    property var selectedNetwork: null
    property string message: ""
    readonly property string displayMessage: message ? networkService.actionMessage(message) : (networkService.details.error || "")
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
    function closeShare() { sharing = false; qrImage = ""; qrPassword.text = ""; shareNetwork = null; }
    function generateQr() {
        if (shareNetwork && networkService.generateQr(menu, shareNetwork, qrPassword.text)) qrPassword.text = "";
    }
    function openShare() {
        shareNetwork = connected;
        qrImage = ""; qrError = ""; qrPassword.text = "";
        sharing = true;
        if (shareNetwork.type === "open") generateQr();
        else qrPassword.forceActiveFocus();
    }
    readonly property bool busy: networkService.busy
    readonly property var latency: networkService.latency.data
    function refresh() { networkService.refresh(); }
    function act(kind, path, extra) {
        if (networkService.act(menu, kind, path, extra,
            Object.assign({password: secret, devicePath: connectDevicePath}, credentials))) {
            message = "";
            secret = "";
            clearEnterprise();
        }
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
    onOpenedChanged: {
        syncDemand();
        if (opened) { message = ""; receiveDetails(); }
        else { selectedNetwork = null; secret = ""; pendingRemoval = ""; password.text = ""; clearEnterprise(); closeShare(); networkService.detach(menu); }
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
                    width: parent.width - 156
                    anchors.verticalCenter: parent.verticalCenter
                    text: menu.connected ? menu.connected.name : Eitr.I18n.tr("WiFi")
                    subtitle: menu.busy ? Eitr.I18n.tr("UPDATING...") : menu.device ? String(menu.device.state).toUpperCase() : Eitr.I18n.tr("NO ADAPTER")
                    foreground: menu.foreground; accent: menu.accent; rune: "connectivity"
                }
                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 12
                    // While a scan runs, its own icon spins here; the "…" button stays still.
                    PanelLoadingIndicator {
                        busy: (menu.busy && menu.networkService.actionKind === "scan") || (!!menu.device && menu.device.scanning)
                        label: Eitr.I18n.tr("Scanning")
                        foreground: menu.foreground; background: menu.background
                    }
                    PanelMoreButton {
                        foreground: menu.foreground; background: menu.background
                        actions: [
                            {title: Eitr.I18n.tr("Scan"), glyph: "\uF021", available: !!menu.device && menu.device.powered && !menu.busy && !menu.device.scanning, run: () => menu.act("scan", menu.device.path)},
                            {title: Eitr.I18n.tr("Share WiFi"), glyph: "󰐲", available: !!menu.connected && ["open", "psk"].indexOf(menu.connected.type) >= 0 && !menu.networkService.qrBusy, run: () => menu.openShare()}
                        ]
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
                        Text { text: parent.modelData[0]; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { x: 70; width: 125; horizontalAlignment: Text.AlignRight; text: parent.modelData[1]; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.features: PanelStyle.tabularFigures }
                        Text { x: 210; text: parent.modelData[2]; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { anchors.right: parent.right; text: parent.modelData[3]; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.features: PanelStyle.tabularFigures }
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
            Text { visible: menu.displayMessage !== ""; width: parent.width; text: menu.displayMessage; wrapMode: Text.Wrap; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
            PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
        }
        PanelFooterLink {
            id: wifiFooter
            visible: !menu.sharing && !menu.enterprise
            anchors.bottom: parent.bottom
            text: Eitr.I18n.tr("Network Settings…")
            foreground: menu.foreground
            onClicked: { menu.opened = false; Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:system-connectivity"]); }
        }
        Flickable {
            visible: !menu.sharing && !menu.enterprise
            anchors.top: wifiHeaderContent.bottom
            anchors.topMargin: 14
            anchors.bottom: wifiFooter.top
            anchors.bottomMargin: 8
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
                        Text { text: parent.modelData.title; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { visible: parent.modelData.networks.length === 0; text: menu.device && menu.device.scanning ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No networks"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                        Repeater {
                            model: parent.modelData.networks
                            Rectangle {
                                id: network
                                required property var modelData
                                width: networks.width; height: PanelStyle.selectionRowHeight; radius: DesktopStyle.radius(PanelStyle.controlRadius)
                                color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(modelData.connected, networkMouse.containsMouse || network.activeFocus))
                                border.width: PanelStyle.selectionBorderWidth(modelData.connected)
                                border.color: Qt.alpha(menu.foreground, PanelStyle.selectionBorderAlpha)
                                activeFocusOnTab: true
                                Keys.onReturnPressed: if (!menu.busy) menu.choose(modelData)
                                Text { x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter; text: "󰤨"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize }
                                Item {
                                    x: PanelStyle.selectionTextInset
                                    width: parent.width - networkActions.width - 52
                                    height: 20
                                    anchors.verticalCenter: parent.verticalCenter
                                    Text {
                                        id: networkName
                                        width: Math.min(implicitWidth, Math.max(0, parent.width - networkStatus.width - (networkStatus.visible ? 8 : 0)))
                                        anchors.verticalCenter: parent.verticalCenter
                                        elide: Text.ElideRight
                                        textFormat: Text.PlainText
                                        text: network.modelData.name
                                        color: menu.foreground
                                        font.family: DesktopFonts.family
                                        font.pixelSize: PanelStyle.bodySize
                                    }
                                    Row {
                                        id: networkStatus
                                        x: networkName.width + 8
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 6
                                        visible: network.modelData.connected || network.modelData.available === false
                                        width: visible ? implicitWidth : 0
                                        Rectangle {
                                            width: 4; height: 4; radius: 2
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: menu.foreground
                                            opacity: 0.6
                                        }
                                        Text {
                                            text: network.modelData.connected ? Eitr.I18n.tr("Connected") : Eitr.I18n.tr("Offline")
                                            color: menu.foreground
                                            opacity: PanelStyle.secondaryTextOpacity
                                            font.family: DesktopFonts.family
                                            font.pixelSize: PanelStyle.captionSize
                                        }
                                    }
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
                Text { width: parent.width; text: Eitr.I18n.tr("ENTERPRISE WI-FI"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
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
            PanelButton { visible: qrPassword.visible; text: Eitr.I18n.tr("Show QR"); width: 100; foreground: menu.foreground; available: qrPassword.text.length > 0 && !menu.networkService.qrBusy; onClicked: menu.generateQr() }
            Image { visible: menu.qrImage !== ""; anchors.horizontalCenter: parent.horizontalCenter; width: 300; height: 300; source: menu.qrImage; fillMode: Image.PreserveAspectFit; smooth: false }
            Text { width: parent.width; text: menu.qrError; visible: text !== ""; color: menu.foreground; wrapMode: Text.Wrap; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
        }
    }
}
