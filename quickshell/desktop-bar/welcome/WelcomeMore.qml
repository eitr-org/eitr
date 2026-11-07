import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Opens the rest of the welcome chapter, listing its section titles, so the
// welcome itself stays short.
Rectangle {
    id: more
    required property var titles
    required property color foreground
    property bool expanded: false
    signal toggled()
    readonly property bool lit: pointer.containsMouse || activeFocus
    width: parent ? parent.width : 0
    height: 64
    radius: DesktopStyle.radius(12)
    color: lit ? SettingsPalette.raised : "transparent"
    border.width: 1
    border.color: lit ? Qt.alpha(SettingsInk.gold, 0.8) : SettingsPalette.line
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: heading.text
    Accessible.description: summary.text
    Keys.onReturnPressed: toggled()
    Keys.onEnterPressed: toggled()
    Keys.onSpacePressed: toggled()
    Column {
        x: 18; anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 70
        spacing: 3
        Text {
            id: heading
            text: more.expanded ? Eitr.I18n.tr("Show less") : Eitr.I18n.tr("More to read")
            color: more.foreground
            font.family: SiteStyle.carved; font.pixelSize: 15
        }
        Text {
            id: summary
            width: parent.width
            text: more.titles.join("  ·  ")
            color: SettingsPalette.muted
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            elide: Text.ElideRight
        }
    }
    Text {
        anchors.right: parent.right; anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        text: "›"
        rotation: more.expanded ? -90 : 90
        color: more.lit ? SettingsInk.gold : SettingsPalette.muted
        font.family: DesktopFonts.family; font.pixelSize: 22
        Behavior on rotation { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
    }
    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { more.forceActiveFocus(); more.toggled(); }
    }
}
