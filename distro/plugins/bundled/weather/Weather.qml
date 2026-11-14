import QtQuick

// The host view retains the weather broker and native styling.
Item {
    required property var api
    implicitWidth: api.compactBarItem ? 26 : 64
    implicitHeight: 24
    Loader {
        anchors.centerIn: parent
        sourceComponent: parent.api.weatherWidgetComponent
    }
}
