import QtQuick
import Eitr as Eitr

Item {
    id: panel
    required property var api
    implicitHeight: body.implicitHeight + 24
    Column {
        id: body
        anchors.centerIn: parent
        width: parent.width
        spacing: 6
        Text {
            width: parent.width; text: panel.api.title; textFormat: Text.PlainText
            color: panel.api.foreground; font.family: panel.api.fontFamily
            font.pixelSize: panel.api.headingSize; horizontalAlignment: Text.AlignHCenter
        }
        Text {
            width: parent.width; text: Eitr.I18n.tr("Hello from an Eitr plugin"); textFormat: Text.PlainText
            color: panel.api.foreground; font.family: panel.api.fontFamily
            font.pixelSize: panel.api.bodySize; horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
    }
}
