import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// A network or device row in Settings. Clicking anywhere on the row runs its main
// action (connect); the buttons in its action slot handle everything else. While
// that action runs, a spinner replaces the glyph and an error replaces the detail.
Rectangle {
    id: row
    required property string text
    required property color foreground
    property string glyph: ""
    property string detail: ""
    property string error: ""
    property bool selected: false
    property bool activatable: true
    property bool loading: false
    readonly property bool interactive: activatable && !loading
    readonly property bool hovered: mouse.containsMouse
    default property alias actions: actionRow.data
    signal activated()
    width: parent ? parent.width : 0
    height: Math.max(PanelStyle.selectionRowHeight + 8, labels.implicitHeight + 14)
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: Qt.alpha(foreground, PanelStyle.selectionAlpha(selected, (mouse.containsMouse && interactive) || activeFocus))
    border.width: PanelStyle.selectionBorderWidth(selected)
    border.color: Qt.alpha(foreground, PanelStyle.selectionBorderAlpha)
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.description: error || detail
    Keys.onReturnPressed: if (interactive) activated()
    Keys.onEnterPressed: if (interactive) activated()
    Keys.onSpacePressed: if (interactive) activated()
    MouseArea {
        id: mouse
        objectName: "connection-row-area"
        anchors.fill: parent
        hoverEnabled: true
        enabled: row.interactive
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            row.forceActiveFocus();
            row.activated();
        }
    }
    SpinningGlyph {
        id: glyphText
        x: PanelStyle.selectionInset + (PanelStyle.selectionTextInset - PanelStyle.selectionInset - 4 - width) / 2
        anchors.verticalCenter: parent.verticalCenter
        glyph: row.loading ? "󰑐" : row.glyph
        color: row.foreground
        size: PanelStyle.selectionIconSize
        spinning: row.loading
    }
    Column {
        id: labels
        x: PanelStyle.selectionTextInset
        width: Math.max(0, actionRow.x - x - 12)
        anchors.verticalCenter: parent.verticalCenter
        spacing: PanelStyle.selectionDetailGap
        Text {
            width: parent.width
            text: row.text
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: row.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }
        Text {
            width: parent.width
            visible: text !== ""
            text: row.error !== "" ? "\uF071  " + row.error : row.detail
            textFormat: Text.PlainText
            wrapMode: row.error !== "" ? Text.WordWrap : Text.NoWrap
            elide: Text.ElideRight
            color: row.foreground
            opacity: row.error !== "" ? 1 : PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
    }
    Row {
        id: actionRow
        anchors.right: parent.right
        anchors.rightMargin: PanelStyle.selectionActionInset + 4
        anchors.verticalCenter: parent.verticalCenter
        spacing: PanelStyle.selectionActionGap
    }
}
