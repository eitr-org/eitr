import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr

Item {
    id: logo
    required property color foreground
    required property color background
    property int slotWidth: 24
    property int iconSize: 22
    signal clicked()
    width: slotWidth
    height: 24

    ToolButton {
        id: button
        anchors.fill: parent
        padding: 0
        background: null
        display: AbstractButton.IconOnly
        icon.source: "../assets/eitr-logo-white.svg"
        icon.width: logo.iconSize; icon.height: logo.iconSize
        icon.color: logo.foreground
        hoverEnabled: true
        onClicked: logo.clicked()
        HoverHandler { cursorShape: Qt.PointingHandCursor }
    }
    BarTooltip {
        target: logo
        background: logo.background
        foreground: logo.foreground
        hovered: button.hovered
        text: Eitr.I18n.tr("Control Center")
    }
}
