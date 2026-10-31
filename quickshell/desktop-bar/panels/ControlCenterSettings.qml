import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import QtQuick.Controls.Basic
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "settings"; width: parent.width; spacing: 12
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Language"); width: parent.width }
    PanelButton {
        width: parent.width; textAlignment: Text.AlignLeft
        text: Eitr.I18n.tr("Language · %1", [Eitr.I18n.languageName])
        foreground: section.centerRef.foreground
        onClicked: section.centerRef.runAfterClose(["eitr-run", "walker/bin/walker", "--provider", "menus:language"])
    }
    ControlCenterLabel { centerRef: section.centerRef;
        width: parent.width; wrapMode: Text.WordWrap
        text: Eitr.I18n.tr("Follows the system locale (LC_MESSAGES / LANG). Sign out and back in after changing it.")
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Devices")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Audio"); glyph: "󰕾"; onClicked: section.centerRef.panelRequested("volume") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Microphone"); glyph: "󰍬"; onClicked: section.centerRef.panelRequested("mic") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Display"); glyph: "󰍹"; onClicked: section.centerRef.panelRequested("display") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"; onClicked: section.centerRef.panelRequested("bluetooth") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("WiFi"); glyph: "󰤨"; onClicked: section.centerRef.panelRequested("wifi") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Lighting"); glyph: "󰛨"; onClicked: section.centerRef.walkerMenu("lighting") }
        ControlCenterGridAction { centerRef: section.centerRef; visible: section.centerRef.battery.available; title: Eitr.I18n.tr("Battery Limit"); glyph: "󰂄"; onClicked: section.centerRef.walkerMenu("battery-limit") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Keyboard")
    Column {
    width: parent.width; spacing: PanelStyle.selectionRowGap
    Repeater {
        model: section.centerRef.keyboardControl.layouts
        KeyboardLayoutRow {
            required property var modelData
            width: parent.width; label: modelData.label
            foreground: section.centerRef.foreground; tooltipBackground: section.centerRef.background
            selected: modelData.index === section.centerRef.keyboardControl.activeLayout
            showRemove: false
            onActivated: section.centerRef.keyboardControl.perform(["select", String(modelData.index)])
        }
    }
    }
    // Adding and removing layouts happens in Walker's Keyboard menu.
    PanelFooterLink { text: Eitr.I18n.tr("Add or Remove Layouts…"); foreground: section.centerRef.foreground; onClicked: section.centerRef.walkerMenu("keyboard") }
    ControlCenterLabel { centerRef: section.centerRef; visible: section.centerRef.keyboardControl.error !== ""; width: parent.width; wrapMode: Text.WordWrap; text: section.centerRef.keyboardControl.error }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Night Light & Main Display")
    Row { width: parent.width; spacing: 8
        Repeater { model: ["off", "on", "auto"]
            PanelButton { textSize: 12; iconSize: 16; required property string modelData; width: (parent.width - 16) / 3; text: modelData.charAt(0).toUpperCase() + modelData.slice(1); foreground: section.centerRef.foreground; selected: section.centerRef.displayControl.nightlight.mode === modelData; available: !!section.centerRef.displayControl.nightlight.available; onClicked: section.centerRef.displayControl.setNightlight(modelData) }
        }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Night Light schedule") }
    Row { width: parent.width; spacing: 8
        TextField {
            id: scheduleStart; width: (parent.width - 8) / 2; height: 36
            text: section.centerRef.displayControl.displayTime(section.centerRef.displayControl.nightlight.start || "18:00")
            color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: 12
            background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(section.centerRef.foreground, 0.08) }
            onEditingFinished: section.centerRef.displayControl.configureNightlightTimes(text, scheduleEnd.text, section.centerRef.displayControl.nightlight.mode)
        }
        TextField {
            id: scheduleEnd; width: (parent.width - 8) / 2; height: 36
            text: section.centerRef.displayControl.displayTime(section.centerRef.displayControl.nightlight.end || "09:00")
            color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: 12
            background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(section.centerRef.foreground, 0.08) }
            onEditingFinished: section.centerRef.displayControl.configureNightlightTimes(scheduleStart.text, text, section.centerRef.displayControl.nightlight.mode)
        }
    }
    ControlCenterLabel { centerRef: section.centerRef; visible: section.centerRef.displayControl.nightlightError !== ""; width: parent.width; wrapMode: Text.WordWrap; text: section.centerRef.displayControl.nightlightError }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Main display") }
    Column {
    width: parent.width; spacing: PanelStyle.selectionRowGap
    Repeater {
        model: section.centerRef.displayControl.monitors
        KeyboardLayoutRow { required property var modelData; width: parent.width; label: modelData.name; foreground: section.centerRef.foreground; showRemove: false; selected: modelData.name === section.centerRef.displayControl.primaryDisplay; onActivated: section.centerRef.displayControl.selectPrimary(modelData.name) }
    }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Information")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("About"); glyph: "󰋽"; onClicked: section.centerRef.menuAction("system", "About") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Hardware"); glyph: "󰍛"; onClicked: section.centerRef.panelRequested("hardware") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("AI Usage"); glyph: ""; onClicked: section.centerRef.panelRequested("ai") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Weather"); glyph: "󰖐"; onClicked: section.centerRef.panelRequested("weather") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Report a Problem"); glyph: "󰃤"; onClicked: section.centerRef.menuAction("system-information", "Report a Problem") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Updates")
    Item { width: parent.width; height: 32
        ControlCenterLabel { centerRef: section.centerRef; anchors.verticalCenter: parent.verticalCenter; text: section.centerRef.updateChannel === "testing" ? Eitr.I18n.tr("Channel: Testing") : section.centerRef.updateChannel === "stable" ? Eitr.I18n.tr("Channel: Stable") : Eitr.I18n.tr("Channel: unknown") }
        PanelButton { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; width: 110; height: 30; textSize: 12; text: Eitr.I18n.tr("Change"); visible: section.centerRef.organizationPolicy.update_channel === true; foreground: section.centerRef.foreground; onClicked: section.centerRef.walkerMenu("update-channel") }
    }
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("System Update"); glyph: "󰚰"; onClicked: section.centerRef.menuAction("system", "System Update") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("What Changed"); glyph: "󰋚"; onClicked: section.centerRef.menuAction("snapshots", "What Each Update Changed") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Snapshots & Cleanup")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Restore a File"); glyph: "󰁯"; onClicked: section.centerRef.menuAction("snapshots", "Restore a File or Folder") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Home Snapshots"); glyph: "󰉏"; onClicked: section.centerRef.menuAction("snapshots", "Home Folder Snapshots") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Recovery Snapshots"); glyph: "󰆓"; onClicked: section.centerRef.menuAction("snapshots", "List Recovery Snapshots") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Recovery Guide"); glyph: "󰋗"; onClicked: section.centerRef.menuAction("snapshots", "Recovery Instructions") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Cleanup"); glyph: "󰃢"; onClicked: section.centerRef.menuAction("system-maintenance", "Cleanup") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Dotfiles"); glyph: "󰘓"; onClicked: section.centerRef.menuAction("settings", "Dotfiles") }
    }
    }
}
