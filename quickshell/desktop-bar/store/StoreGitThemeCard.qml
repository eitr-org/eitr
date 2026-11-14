import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    required property var catalog

    id: gitCard
    required property var row
    property bool selectable: true
    readonly property bool chosen: selectable && catalog.gitSelected.includes(row.id)
    height: gitDetails.y + gitDetails.height + 12
    radius: DesktopStyle.radius(10); color: catalog.surface
    border.width: 1; border.color: chosen ? catalog.accent : selectable && gitMouse.containsMouse ? catalog.lineStrong : catalog.line
    Component.onCompleted: catalog.gitArtworkFor(row)
    RectangularShadow { anchors.fill: parent; z: -1; visible: gitCard.chosen; radius: gitCard.radius; blur: 18; spread: 2; color: catalog.glow }
    StorePreview { catalog: gitCard.catalog; id: gitArt; x: 2; y: 2; width: parent.width - 4; height: width * 9 / 16; source: catalog.gitArtwork[gitCard.row.id] || ""
        plugin: catalog.kind === "plugins"; iconOnly: plugin && !gitCard.row.preview }
    Column {
        id: gitDetails
        x: 12; y: gitArt.y + gitArt.height + 10; width: parent.width - 24; spacing: 5
        StoreLabel { catalog: gitCard.catalog; width: parent.width; text: gitCard.row.name || ""; font.family: SiteStyle.carved; font.weight: Font.Medium; font.letterSpacing: 0.7; maximumLineCount: 1; elide: Text.ElideRight }
        StoreLabel { catalog: gitCard.catalog; width: parent.width; text: gitCard.row.description || ""; font.pixelSize: 13; color: catalog.muted; maximumLineCount: 1; elide: Text.ElideRight }
        Row { spacing: 4; visible: catalog.kind === "themes"
            Repeater {
                model: gitCard.row.palette ? ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"] : []
                Rectangle { required property string modelData; width: 14; height: 14; radius: 7; color: gitCard.row.palette[modelData]; border.width: 1; border.color: catalog.lineStrong }
            }
        }
        Row { spacing: 6
            StorePill { catalog: gitCard.catalog; visible: catalog.kind === "themes"; text: gitCard.row.light ? Eitr.I18n.tr("Light") : Eitr.I18n.tr("Dark") }
            StorePill { catalog: gitCard.catalog; visible: catalog.kind === "themes"; text: catalog.sizeText(gitCard.row.size || 0) }
            StorePill { catalog: gitCard.catalog; visible: catalog.kind === "plugins" && !!gitCard.row.version; text: gitCard.row.version || "" }
            StorePill { catalog: gitCard.catalog; visible: catalog.kind === "plugins" && catalog.isInstalled(gitCard.row); text: Eitr.I18n.tr("Installed") }
        }
    }
    MouseArea { id: gitMouse; anchors.fill: parent; hoverEnabled: true; enabled: gitCard.selectable && !catalog.busy && !(catalog.kind === "plugins" && catalog.isInstalled(gitCard.row))
        cursorShape: Qt.PointingHandCursor; onClicked: catalog.toggleGitTheme(gitCard.row.id) }
    Rectangle {
        visible: gitCard.chosen; x: 10; y: 10; width: 30; height: 30; radius: 15; color: catalog.accent
        StoreLabel { catalog: gitCard.catalog; anchors.centerIn: parent; text: "\uF00C"; color: PanelStyle.readableInk(catalog.accent, catalog.foreground, catalog.background); font.pixelSize: 18 }
    }
}
