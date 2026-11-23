import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland
import Eitr as Eitr
import "../clock/AlarmModel.js" as AlarmModel

Variants {
    id: overlay
    required property color foreground
    required property color background
    required property color accent
    readonly property var alarm: ClockAlarms.ringing
    model: alarm && ClockAlarms.unlocked ? Quickshell.screens : []
    delegate: Component {
        PanelWindow {
            required property var modelData
            screen: modelData
            visible: Boolean(overlay.alarm) && ClockAlarms.unlocked
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "desktop-alarm"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
            AlarmRingingContent {
                anchors.fill: parent
                color: Qt.rgba(overlay.background.r, overlay.background.g, overlay.background.b, 1)
                foreground: overlay.foreground
                accent: overlay.accent
                alarmName: overlay.alarm ? overlay.alarm.text : ""
                alarmTime: overlay.alarm ? AlarmModel.displayTime(overlay.alarm.alarm.ringTime, PluginRegistry.clockFormat === "12h", Qt.locale(Eitr.I18n.locale)) : ""
                onStopped: ClockAlarms.run("alarm-stop", ClockAlarms.ringingId)
                onSnoozed: ClockAlarms.run("alarm-snooze", ClockAlarms.ringingId)
                Component.onCompleted: forceActiveFocus()
            }
        }
    }
}
