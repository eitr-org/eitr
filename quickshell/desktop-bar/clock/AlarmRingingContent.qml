import ".."
import QtQuick
import Eitr as Eitr

Rectangle {
    id: surface
    required property color foreground
    required property color accent
    required property string alarmName
    required property string alarmTime
    signal stopped()
    signal snoozed()

    focus: true
    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (event.isAutoRepeat) { event.accepted = true; return; }
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Escape)
            surface.stopped();
        else if (event.key === Qt.Key_Space || event.key === Qt.Key_S)
            surface.snoozed();
        else return;
        event.accepted = true;
    }

    AlarmEffect { anchors.fill: parent; accent: surface.accent }
    Column {
        anchors.centerIn: parent
        // Stay inside AlarmEffect's circle (70% of the shorter side) with a margin.
        width: Math.max(280, Math.min(surface.width, surface.height) * 0.56)
        spacing: 20
        Text {
            width: parent.width
            text: surface.alarmTime
            color: surface.accent
            horizontalAlignment: Text.AlignHCenter
            font.family: DesktopFonts.family
            font.pixelSize: 92
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 28
        }
        Text {
            width: parent.width
            text: surface.alarmName
            textFormat: Text.PlainText
            color: surface.foreground
            horizontalAlignment: Text.AlignHCenter
            font.family: DesktopFonts.family
            font.pixelSize: 26
            elide: Text.ElideRight
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 12
            PanelButton {
                width: Math.min(164, (parent.parent.width - 12) / 2); height: 52; textSize: 16
                foreground: surface.foreground
                text: Eitr.I18n.tr("Stop")
                selected: true
                activeFocusOnTab: false
                onClicked: { surface.forceActiveFocus(); surface.stopped(); }
            }
            PanelButton {
                width: Math.min(164, (parent.parent.width - 12) / 2); height: 52; textSize: 16
                foreground: surface.foreground
                text: Eitr.I18n.tr("Snooze")
                activeFocusOnTab: false
                onClicked: { surface.forceActiveFocus(); surface.snoozed(); }
            }
        }
    }
}
