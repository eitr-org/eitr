import QtQuick

Item {
    required property var api
    implicitWidth: 240; implicitHeight: 144
    property date now: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: parent.now = new Date() }
    Column {
        anchors.centerIn: parent; width: Math.max(0, parent.width - 24); spacing: 6
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(parent.parent.now, Qt.locale(), Locale.ShortFormat)
            color: api.foreground; font.family: api.fontFamily; font.pixelSize: api.headingSize
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width; horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: Qt.formatDate(parent.parent.now, Qt.locale(), Locale.LongFormat)
            color: api.foreground; font.family: api.fontFamily; font.pixelSize: api.captionSize
        }
    }
}
