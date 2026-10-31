import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

ControlCenterLabel {
    id: control
    width: parent.width
    topPadding: PanelStyle.selectionRowGap
    wrapMode: Text.WordWrap
    opacity: PanelStyle.secondaryTextOpacity
}
