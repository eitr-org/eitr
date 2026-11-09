import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle
import "../ChoiceLists.js" as ChoiceLists

ThemedPopup {
    id: menu
    required property string currentStyle
    required property color selectedForeground
    signal selected(string style)

    // Two picture cards per row; five markers fit each card at the 296 px minimum.
    readonly property real rowWidth: 2 * (5 * 22 + 4 * 4 + 16) + 8
    implicitWidth: Math.max(296, rowWidth + horizontalContentInset)
    implicitHeight: pictures.implicitHeight + verticalContentInset
    // Without the join insets, which depend on edge contact.
    edgeContactWidth: Math.max(296, rowWidth + (contentGaps[1] + contentGaps[3]) * PanelStyle.contentGapMultiplier)
    leftAligned: true
    readonly property var styles: ChoiceLists.workspaceStyles

    // The panel's content column, like every side panel's: picture cards with the real markers.
    Column {
        width: parent.width
        PictureChoices {
            id: pictures
            width: parent.width
            compact: true
            showLabels: false
            kind: "workspace"
            choices: menu.styles
            current: menu.currentStyle
            foreground: menu.foreground; background: menu.background; accent: menu.accent
            onChosen: value => { menu.selected(value); menu.opened = false; }
        }
    }
}
