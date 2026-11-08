import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import "../HandbookModel.js" as Model

// A chapter figure: the named static drawing on a card in the Settings palette, with
// its caption from the chapter text below. Drawings narrower than their minimumWidth
// are laid out at that width and scaled down to fit. Clicks stop at the card, so the
// shared controls inside only illustrate; hovering still shows their hover state.
Column {
    id: holder
    required property string name
    required property string caption
    signal linkActivated(string link)
    spacing: 8
    Rectangle {
        id: stage
        width: holder.width
        height: drawing.height * drawing.scale + 32
        radius: DesktopStyle.radius(10)
        color: SettingsPalette.surface
        border.width: 1; border.color: SettingsPalette.line
        clip: true
        Loader {
            id: drawing
            x: 16; y: 16
            readonly property real available: stage.width - 32
            width: Math.max(available, item ? item.minimumWidth : 0)
            height: item ? item.implicitHeight : 0
            scale: width > 0 ? available / width : 1
            transformOrigin: Item.TopLeft
            active: holder.name !== ""
            source: holder.name ? Qt.resolvedUrl(Model.figureFile(holder.name)) : ""
        }
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }
    }
    Text {
        width: holder.width
        visible: text !== ""
        text: holder.caption
        textFormat: Text.StyledText
        wrapMode: Text.Wrap
        color: SettingsPalette.muted
        linkColor: SettingsPalette.accent
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
        onLinkActivated: link => holder.linkActivated(link)
    }
}
