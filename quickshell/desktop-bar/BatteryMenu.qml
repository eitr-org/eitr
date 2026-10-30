import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

ThemedPopup {
    id: menu
    required property var battery
    required property var displayControl
    implicitWidth: 400
    implicitHeight: content.implicitHeight + verticalContentInset
    property var powerTokens: []
    onOpenedChanged: {
        PowerService.release(powerTokens);
        powerTokens = opened ? PowerService.observe(menu, 5, false) : [];
    }
    Component.onDestruction: DesktopData.releaseOwner(menu)
    Column {
        id: content
        x: 0; y: 0
        width: parent.width; spacing: 18
        PanelHeading { text: Eitr.I18n.tr("Battery & Power"); foreground: menu.foreground; accent: menu.accent; rune: "power" }
        PowerControls { width: parent.width; battery: menu.battery; displayControl: menu.displayControl; foreground: menu.foreground }
        Text { visible: menu.battery.health > 0; text: Eitr.I18n.tr("Battery health: {percent}%", {percent: Math.round(menu.battery.health)}); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
}
