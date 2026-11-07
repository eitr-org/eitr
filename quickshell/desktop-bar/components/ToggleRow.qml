import ".."
import QtQuick
ControlRow {
    id: row
    required property color accent
    property bool checked: false
    property bool available: true
    signal toggled(bool checked)
    property real controlInset: 0
    controlWidth: 36 + controlInset
    PanelSwitch {
        width: 36
        foreground: row.foreground; accent: row.accent
        checked: row.checked; enabled: row.available
        Accessible.name: row.text
        onToggled: row.toggled(checked)
    }
}
