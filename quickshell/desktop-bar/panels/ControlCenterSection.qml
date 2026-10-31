import ".."
pragma ComponentBehavior: Bound
import QtQuick

PanelDivider {
    id: control
    required property var centerRef
    foreground: control.centerRef.foreground
}
