import ".."
import QtQuick
import QtQuick.Controls.Basic
import "../PanelStyle.js" as PanelStyle
import Eitr as Eitr

// A small centred confirmation over Settings: a title, one explaining line, Cancel and the
// confirming action, which has the keyboard focus. Escape cancels.
Popup {
    id: sheet
    required property color foreground
    required property color surfaceColor
    property string title: ""
    property string message: ""
    property string confirmText: Eitr.I18n.tr("Remove")
    property string confirmName: ""
    signal confirmed()
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 320
    padding: 24
    modal: true
    dim: true
    focus: true
    closePolicy: Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: Qt.alpha("black", 0.45) }
    background: Rectangle {
        radius: DesktopStyle.radius(12)
        color: Qt.rgba(sheet.surfaceColor.r, sheet.surfaceColor.g, sheet.surfaceColor.b, 1)
        border.width: 1
        border.color: Qt.alpha(SettingsInk.gold, 0.4)
    }
    onOpened: confirm.forceActiveFocus()
    contentItem: Column {
        spacing: 14
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: sheet.title
            color: sheet.foreground
            font.family: SiteStyle.carved
            font.pixelSize: PanelStyle.headingSize
        }
        SettingsText {
            width: parent.width
            visible: text !== ""
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            text: sheet.message
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8
            PanelButton { width: 110; foreground: sheet.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: sheet.close() }
            PanelButton {
                id: confirm
                objectName: sheet.confirmName
                width: 110
                foreground: sheet.foreground
                text: sheet.confirmText
                // Act before closing: a page may clear what the sheet was about when it closes.
                onClicked: { sheet.confirmed(); sheet.close(); }
            }
        }
    }
}
