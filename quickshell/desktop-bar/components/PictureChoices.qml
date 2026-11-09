import ".."
import QtQuick
import Eitr as Eitr

Flow {
    property color themeBackground: background
    property color themeForeground: foreground
    property color themeAccent: accent
    property color background: "#20242c"
    property color accent: foreground
    property color muted: Qt.alpha(foreground, 0.72)
    property color line: Qt.alpha(foreground, 0.15)
    property color surface: Qt.alpha(foreground, 0.04)
    property color raised: Qt.alpha(foreground, 0.08)
    property color gold: foreground
    property color foreground: "#eeeeee"
    id: control
    property bool carved: false
    property string kind: "layout"
    property var choices: []
    property string current: ""
    property string edge: "top"
    property string appearance: "solid"
    property bool available: true
    property bool compact: false
    // Pictures alone (the bar's workspace popup): no name under them, so the cards are short;
    // the outline marks the current choice and screen readers still hear the name.
    property bool showLabels: true
    readonly property bool barPictures: ["layout", "position", "appearance"].indexOf(kind) !== -1
    readonly property bool smallCards: compact && !barPictures
    signal chosen(string value)
    width: parent ? parent.width : 600
    spacing: 8
    Repeater {
        model: control.choices
        Rectangle {
            id: card
            required property var modelData
            readonly property string value: String(modelData.id ?? modelData.value ?? modelData.key ?? modelData)
            readonly property bool selected: value === control.current
            width: Math.floor((control.width - 8 * (columns - 1)) / columns)
            readonly property int columns: control.barPictures ? Math.max(1, Math.min(3, Math.floor((control.width + 8) / 210))) : control.smallCards ? Math.max(1, Math.min(control.choices.length, Math.floor((control.width + 8) / 110))) : Math.max(1, Math.floor((control.width + 8) / 190))
            height: !control.showLabels ? 52 : control.barPictures ? (detail.visible ? 220 : 200) : control.smallCards ? 108 : detail.visible ? 138 : 118
            radius: DesktopStyle.radius(6)
            color: pointer.containsMouse ? control.raised : control.surface
            border.width: selected || activeFocus ? 2 : 1
            border.color: selected || activeFocus ? control.gold : control.line
            activeFocusOnTab: true
            enabled: control.available
            Accessible.role: Accessible.RadioButton
            Accessible.name: label.text + (detail.visible ? ". " + detail.text : "")
            Accessible.checked: selected
            Keys.onReturnPressed: control.chosen(value)
            Keys.onSpacePressed: control.chosen(value)
            Loader {
                x: 8; y: 8; width: parent.width - 16; height: !control.showLabels ? 36 : control.barPictures ? 156 : control.smallCards ? 58 : 74
                sourceComponent: control.kind === "workspace" ? workspacePicture : control.kind === "layout" ? layoutPicture : control.kind === "position" ? positionPicture : control.kind === "appearance" ? appearancePicture : control.kind === "media" ? mediaPicture : control.kind === "gaps" ? gapsPicture : control.kind === "corners" ? cornersPicture : control.kind === "lockscreen" ? lockPicture : palettePicture
                Component { id: workspacePicture; Item {
                    Row { anchors.centerIn: parent; spacing: 4
                        Repeater { model: 5
                            WorkspaceMarker { required property int index; style: card.value; label: String(index + 1); active: index === 1; width: Math.min(23, (card.width - 32) / 5); foreground: control.foreground; accent: control.accent; selectedForeground: control.background }
                        }
                    }
                } }
                Component { id: layoutPicture; BarPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; layout: card.value; edge: control.edge; appearance: control.appearance } }
                Component { id: positionPicture; PositionPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value } }
                Component { id: appearancePicture; AppearancePreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value; edge: control.edge } }
                Component { id: mediaPicture; MediaPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value } }
                Component { id: gapsPicture; GapsPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; choice: card.modelData } }
                Component { id: cornersPicture; CornersPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value } }
                Component { id: lockPicture; LockscreenPreview { foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value } }
                Component { id: palettePicture; PalettePreview { themeBackground: control.themeBackground; themeForeground: control.themeForeground; themeAccent: control.themeAccent; foreground: control.foreground; background: control.background; accent: control.accent; gold: control.gold; value: card.value } }
            }
            Text {
                id: label
                visible: control.showLabels
                x: 10; y: control.barPictures ? 173 : control.smallCards ? 73 : 91; width: parent.width - 30
                text: Eitr.I18n.tr(String(card.modelData.label ?? card.modelData.name ?? card.modelData))
                color: card.selected ? control.gold : control.foreground
                font.family: control.carved ? SiteStyle.carved : DesktopFonts.family; font.pixelSize: control.carved ? 11 : 13
                elide: Text.ElideRight
            }
            Text { anchors.right: parent.right; anchors.rightMargin: 9; y: control.barPictures ? 172 : control.smallCards ? 72 : 90; visible: card.selected && control.showLabels; text: "✓"; color: control.gold }
            Text {
                id: detail
                x: 10; y: control.barPictures ? 196 : 112; width: parent.width - 20
                visible: control.showLabels && !control.smallCards && !!card.modelData.description
                text: Eitr.I18n.tr(card.modelData.description || "")
                color: control.muted
                font.family: DesktopFonts.family; font.pixelSize: 10
                elide: Text.ElideRight
            }
            MouseArea { id: pointer; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { card.forceActiveFocus(); control.chosen(card.value); } }
        }
    }
}
