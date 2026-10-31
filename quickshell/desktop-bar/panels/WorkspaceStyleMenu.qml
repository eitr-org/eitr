import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

ThemedPopup {
    id: menu
    required property string currentStyle
    required property color selectedForeground
    signal selected(string style)

    readonly property real rowWidth: PanelStyle.selectionTextInset + labelMetrics.advanceWidth + 12 + 5 * 23 + 4 * 4 + 10
    implicitWidth: Math.max(296, rowWidth + horizontalContentInset)
    implicitHeight: styles.length * PanelStyle.selectionRowHeight + (styles.length - 1) * PanelStyle.selectionRowGap + verticalContentInset
    // Without the join insets, which depend on edge contact.
    edgeContactWidth: Math.max(296, rowWidth + (contentGaps[1] + contentGaps[3]) * PanelStyle.contentGapMultiplier)
    leftAligned: true
    readonly property var styles: ["Dots", "Glyph", "Numbers", "Runes"]

    TextMetrics {
        id: labelMetrics
        text: Eitr.I18n.tr("Numbers")
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
    }

    Column {
        anchors.fill: parent
        anchors.margins: 0
        spacing: PanelStyle.selectionRowGap
        Repeater {
            model: menu.styles
            Rectangle {
                id: choiceRow
                required property string modelData
                required property int index
                width: parent.width
                height: PanelStyle.selectionRowHeight
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(modelData === menu.currentStyle, mouse.containsMouse))
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: PanelStyle.selectionTextInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData
                    color: menu.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                Row {
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4
                    Repeater {
                        model: 5
                        WorkspaceMarker {
                            required property int index
                            width: 23
                            height: 20
                            style: choiceRow.modelData
                            label: String(index + 1)
                            active: index === 1
                            accent: menu.accent
                            foreground: menu.foreground
                            selectedForeground: menu.selectedForeground
                        }
                    }
                }
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData === menu.currentStyle ? "" : ""
                    color: menu.accent
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.controlSize
                }
                MouseArea {
                    id: mouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        menu.selected(parent.modelData);
                        menu.opened = false;
                    }
                }
            }
        }
    }
}
