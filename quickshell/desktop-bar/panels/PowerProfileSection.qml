import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var menu
    visible: section.menu.settingsSection !== "nightlight" && section.menu.power.available
    width: parent.width
    spacing: 12
    PanelDivider { width: parent.width; height: 8; foreground: section.menu.foreground }
    Text { text: Eitr.I18n.tr("Power Profile"); color: section.menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
    ChoiceSegmented { width: parent.width; foreground: section.menu.foreground; choices: section.menu.powerProfiles.map(profile => ({id: profile.name, label: profile.label, available: section.menu.power.profiles.includes(profile.name)})); current: section.menu.power.active || ""; available: !section.menu.powerBusy; onChosen: value => section.menu.setPowerProfile(value) }
    Text {
        visible: section.menu.powerError !== ""
        text: section.menu.powerError
        color: section.menu.foreground
        opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
    }
}
