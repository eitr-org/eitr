import ".."
import QtQuick
ControlRow {
    id: row
    required property color accent
    property bool checked: false
    property bool available: true
    signal toggled(bool checked)
    property real controlInset: 0
    // PanelSwitch draws its track and knob in 42 px; a narrower slot cut its right edge.
    controlWidth: 42 + controlInset
    PanelSwitch {
        width: 42
        foreground: row.foreground; accent: row.accent
        checked: row.checked; enabled: row.available
        Accessible.name: row.text
        onToggled: row.toggled(checked)
    }
}
