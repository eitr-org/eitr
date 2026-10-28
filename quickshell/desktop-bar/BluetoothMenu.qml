import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Bluetooth

ThemedPopup {
    id: menu
    implicitWidth: 468
    implicitHeight: Math.min(508, Math.max(248, groups.height + 122))
    property var adapter: Bluetooth.defaultAdapter
    property var scanningAdapter: null
    property var sections: []
    onAvailableSectionsChanged: menu.updateContent(function() {
        const next = menu.availableSections;
        if (menu.sections.length !== next.length || next.some((group, index) => {
            const previous = menu.sections[index];
            return previous.title !== group.title || previous.devices.length !== group.devices.length
                || group.devices.some((device, deviceIndex) => device !== previous.devices[deviceIndex]);
        })) menu.sections = next;
    })
    Component.onCompleted: sections = availableSections
    readonly property var availableSections: [
        {title: Eitr.I18n.tr("CONNECTED"), devices: adapter ? adapter.devices.values.filter(d => d.connected) : []},
        {title: Eitr.I18n.tr("KNOWN DEVICES"), devices: adapter ? adapter.devices.values.filter(d => !d.connected && d.paired) : []},
        {title: Eitr.I18n.tr("SCANNED DEVICES"), devices: adapter ? adapter.devices.values.filter(d => !d.connected && !d.paired) : []}
    ]
    function scan() {
        if (!adapter) return;
        if (scanningAdapter) { scanningAdapter.discovering = false; scanningAdapter = null; }
        else { scanningAdapter = adapter; adapter.discovering = true; scanTimer.restart(); }
    }
    onOpenedChanged: if (!opened && scanningAdapter) {
        scanningAdapter.discovering = false;
        scanningAdapter = null;
    }
    Timer {
        id: scanTimer
        interval: 20000
        onTriggered: if (menu.scanningAdapter) { menu.scanningAdapter.discovering = false; menu.scanningAdapter = null; }
    }
    Item {
        anchors.fill: parent
        anchors.margins: 0
        Item {
            id: header
            width: parent.width
            height: 40
            PanelHeading { anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Bluetooth"); foreground: menu.foreground; accent: menu.accent; rune: "connectivity" }
            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                PanelButton {
                    id: scanButton
                    width: 34; height: 32
                    text: menu.scanningAdapter ? "\uF04D" : "\uF021"; icon: true; compactIconBackground: true
                    foreground: menu.foreground
                    available: !!menu.adapter && menu.adapter.enabled
                    Accessible.name: menu.scanningAdapter ? Eitr.I18n.tr("Stop scan") : Eitr.I18n.tr("Scan")
                    onClicked: menu.scan()
                    HoverHandler { id: scanHover }
                    BarTooltip { target: scanButton; hovered: scanHover.hovered; text: scanButton.Accessible.name; foreground: menu.foreground; background: menu.background }
                }
                PanelSwitch { checked: !!menu.adapter && menu.adapter.enabled; enabled: !!menu.adapter; foreground: menu.foreground; accent: menu.accent; onClicked: menu.adapter.enabled = checked }
            }
        }
        Flickable {
            anchors.top: header.bottom
            anchors.topMargin: 18
            anchors.bottom: parent.bottom
            width: parent.width
            contentHeight: groups.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: groups
                width: parent.width
                spacing: 20
                Text { visible: !menu.adapter || !menu.adapter.enabled; text: menu.adapter ? Eitr.I18n.tr("Bluetooth is off") : Eitr.I18n.tr("No Bluetooth adapter"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                Repeater {
                    model: menu.sections
                    Column {
                        required property var modelData
                        width: groups.width
                        spacing: PanelStyle.selectionRowGap
                        PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
                        Text { text: parent.modelData.title; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { visible: parent.modelData.devices.length === 0; text: parent.modelData.title === "SCANNED DEVICES" && menu.scanningAdapter ? Eitr.I18n.tr("Scanning...") : Eitr.I18n.tr("No devices"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                        Repeater {
                            model: parent.modelData.devices
                            Item {
                                id: device
                                required property var modelData
                                property bool confirmingForget: false
                                width: groups.width
                                height: PanelStyle.selectionRowHeight
                                Rectangle {
                                    anchors.fill: parent; radius: DesktopStyle.radius(PanelStyle.controlRadius)
                                    color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(device.modelData.connected, deviceHover.hovered))
                                    border.width: PanelStyle.selectionBorderWidth(device.modelData.connected)
                                    border.color: Qt.alpha(menu.foreground, PanelStyle.selectionBorderAlpha)
                                }
                                HoverHandler { id: deviceHover }
                                Text { x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter; text: device.modelData.connected ? "󰂱" : "󰂯"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 18 }
                                Column {
                                    x: PanelStyle.selectionTextInset
                                    width: Math.max(0, actions.x - x - 8)
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: PanelStyle.selectionDetailGap
                                    Text { width: parent.width; elide: Text.ElideRight; textFormat: Text.PlainText; text: device.modelData.name; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                                    Text { width: parent.width; elide: Text.ElideRight; text: BluetoothDeviceState.toString(device.modelData.state) + (device.modelData.batteryAvailable ? " · " + Math.round(device.modelData.battery * 100) + "%" : ""); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                                }
                                Row {
                                    id: actions
                                    anchors.right: parent.right
                                    anchors.rightMargin: PanelStyle.selectionActionInset
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: PanelStyle.selectionActionGap
                                    PanelButton {
                                        id: connectionButton
                                        readonly property string actionLabel: device.confirmingForget || device.modelData.pairing ? "Cancel" : device.modelData.connected ? "Disconnect" : device.modelData.paired ? "Connect" : "Pair"
                                        width: PanelStyle.selectionActionWidth
                                        height: PanelStyle.selectionActionHeight
                                        icon: true
                                        text: device.confirmingForget || device.modelData.pairing ? "" : device.modelData.connected ? "󰂲" : device.modelData.paired ? "󰂱" : "󰂯"
                                        Accessible.name: actionLabel
                                        foreground: menu.foreground
                                        available: !!menu.adapter && menu.adapter.enabled
                                        onClicked: {
                                            if (device.confirmingForget) device.confirmingForget = false;
                                            else if (device.modelData.pairing) device.modelData.cancelPair();
                                            else if (device.modelData.connected) device.modelData.disconnect();
                                            else if (device.modelData.paired) device.modelData.connect();
                                            else device.modelData.pair();
                                        }
                                        HoverHandler { id: connectionHover }
                                        BarTooltip { target: connectionButton; hovered: connectionHover.hovered; text: connectionButton.actionLabel; foreground: menu.foreground; background: menu.background }
                                    }
                                    PanelButton {
                                        id: forgetButton
                                        visible: device.modelData.paired
                                        width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight; icon: true
                                        text: device.confirmingForget ? "" : "󰆴"
                                        Accessible.name: device.confirmingForget ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Remove")
                                        foreground: menu.foreground
                                        onClicked: { if (device.confirmingForget) device.modelData.forget(); else device.confirmingForget = true; }
                                        HoverHandler { id: forgetHover }
                                        BarTooltip { target: forgetButton; hovered: forgetHover.hovered; text: device.confirmingForget ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Remove"); foreground: menu.foreground; background: menu.background }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
