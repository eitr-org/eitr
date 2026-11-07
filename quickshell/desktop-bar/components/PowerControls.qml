import ".."
pragma ComponentBehavior: Bound
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

Column {
    id: controls
    required property var displayControl
    required property var battery
    required property color foreground
    spacing: 12
    Text {
        width: parent.width
        text: controls.battery.available ? (controls.battery.hours > 0 ? Eitr.I18n.tr("{percent}% · {status} · ~{hours}h {minutes}m", {percent: Math.round(controls.battery.percent), status: controls.battery.status, hours: Math.floor(controls.battery.hours), minutes: Math.floor((controls.battery.hours % 1) * 60)}) : Eitr.I18n.tr("{percent}% · {status}", {percent: Math.round(controls.battery.percent), status: controls.battery.status})) : ""
        color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    ChoiceSegmented { width: parent.width; foreground: controls.foreground; choices: [{id: "power-saver", label: "Saver"}, {id: "balanced", label: "Balanced"}, {id: "performance", label: "Performance"}].map(profile => Object.assign({}, profile, {available: controls.displayControl.power.profiles.includes(profile.id)})); current: controls.displayControl.power.active || ""; available: !controls.displayControl.powerBusy; onChosen: value => controls.displayControl.setPowerProfile(value) }
    Text { visible: !controls.displayControl.power.available; width: parent.width; wrapMode: Text.WordWrap; text: Eitr.I18n.tr("Power profiles unavailable on this hardware"); color: controls.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    Text { visible: text !== ""; width: parent.width; wrapMode: Text.WordWrap; text: controls.displayControl.powerError; color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
}
