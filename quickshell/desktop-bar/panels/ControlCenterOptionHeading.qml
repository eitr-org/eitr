import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

ControlCenterLabel {
    id: control
    width: parent.width
    topPadding: PanelStyle.selectionRowGap
    wrapMode: Text.WordWrap
    // Small labels are gold on the website; otherwise a dimmed foreground.
    color: DesktopStyle.website ? SiteStyle.bronze : centerRef.foreground
    opacity: DesktopStyle.website ? 1 : PanelStyle.secondaryTextOpacity
}
