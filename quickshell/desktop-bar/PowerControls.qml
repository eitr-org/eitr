pragma ComponentBehavior: Bound
import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

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
    Row {
        width: parent.width; spacing: 6
        Repeater {
            model: [{name: "power-saver", label: "Saver"}, {name: "balanced", label: "Balanced"}, {name: "performance", label: "Performance"}]
            PanelButton {
                required property var modelData
                width: (controls.width - 12) / 3; height: 36
                text: Eitr.I18n.tr(modelData.label); foreground: controls.foreground
                selected: controls.displayControl.power.active === modelData.name
                available: controls.displayControl.power.profiles.indexOf(modelData.name) !== -1
                loading: controls.displayControl.powerBusy
                onClicked: controls.displayControl.setPowerProfile(modelData.name)
            }
        }
    }
    Text { visible: !controls.displayControl.power.available; width: parent.width; wrapMode: Text.WordWrap; text: Eitr.I18n.tr("Power profiles unavailable on this hardware"); color: controls.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    Text { visible: text !== ""; width: parent.width; wrapMode: Text.WordWrap; text: controls.displayControl.powerError; color: controls.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
}
