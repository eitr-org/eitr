import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

// One WiFi network in a list (the WiFi panel and Drop's quick controls): its name and
// state, signal and lock, and Disconnect or a two-step Remove. A click asks to connect.
Rectangle {
    id: network
    required property var modelData
    required property color foreground
    required property color background
    property bool busy: false
    // The known network whose removal waits for a second click.
    property string pendingRemoval: ""
    signal chosen()
    signal disconnectRequested()
    signal removeRequested(bool confirmed)
    height: PanelStyle.selectionRowHeight; radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(network.foreground, PanelStyle.selectionAlpha(modelData.connected, networkMouse.containsMouse || network.activeFocus))
    border.width: PanelStyle.selectionBorderWidth(modelData.connected)
    border.color: Qt.alpha(network.foreground, PanelStyle.selectionBorderAlpha)
    activeFocusOnTab: true
    Keys.onReturnPressed: if (!network.busy) network.chosen()
    Text { x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter; text: "󰤨"; color: network.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize }
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
            color: network.foreground
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
                color: network.foreground
                opacity: 0.6
            }
            Text {
                text: network.modelData.connected ? Eitr.I18n.tr("Connected") : Eitr.I18n.tr("Offline")
                color: network.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
        }
    }
    MouseArea { id: networkMouse; anchors.fill: parent; hoverEnabled: true; enabled: !network.busy && !network.modelData.connected && network.modelData.available !== false; cursorShape: Qt.PointingHandCursor; onClicked: network.chosen() }
    Row {
        id: networkActions
        anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter; spacing: PanelStyle.selectionActionGap
        Text { visible: network.modelData.available !== false; anchors.verticalCenter: parent.verticalCenter; text: Math.round(network.modelData.strength) + "%"; color: network.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
        Text { visible: network.modelData.type !== "open"; anchors.verticalCenter: parent.verticalCenter; text: "󰌾"; color: network.foreground; opacity: 0.65; font.family: DesktopFonts.family; font.pixelSize: 14 }
        PanelButton {
            id: disconnectButton
            visible: network.modelData.connected
            text: "󰖪"; icon: true; width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight
            iconOffsetX: -2
            foreground: network.foreground; available: !network.busy
            Accessible.name: Eitr.I18n.tr("Disconnect")
            onClicked: network.disconnectRequested()
            HoverHandler { id: disconnectHover }
            BarTooltip { target: disconnectButton; hovered: disconnectHover.hovered; text: Eitr.I18n.tr("Disconnect"); foreground: network.foreground; background: network.background }
        }
        PanelButton {
            id: removeButton
            readonly property bool confirming: network.pendingRemoval === network.modelData.knownPath
            visible: network.modelData.known && !network.modelData.connected
            text: confirming ? "" : "󰆴"
            icon: true; width: PanelStyle.selectionActionWidth; height: PanelStyle.selectionActionHeight; foreground: network.foreground
            Accessible.name: confirming ? Eitr.I18n.tr("Confirm removal") : Eitr.I18n.tr("Remove")
            available: !network.busy && !!network.modelData.knownPath
            onClicked: network.removeRequested(confirming)
            HoverHandler { id: removeHover }
            BarTooltip { target: removeButton; hovered: removeHover.hovered; text: removeButton.Accessible.name; foreground: network.foreground; background: network.background }
        }
    }
    BarTooltip { target: network; hovered: networkMouse.containsMouse && !removeHover.hovered; text: network.modelData.connected || network.modelData.available === false ? "" : Eitr.I18n.tr("Connect"); foreground: network.foreground; background: network.background }
}
