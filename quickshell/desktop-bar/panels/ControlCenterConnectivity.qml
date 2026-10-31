import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "general"
    width: parent.width; spacing: 12
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Connectivity"); width: parent.width }
    GridLayout {
        width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
        ControlCenterToggleTile { centerRef: section.centerRef;
            title: Eitr.I18n.tr("WiFi"); glyph: section.centerRef.wifiGlyph
            detail: section.centerRef.wifiControl.connected ? section.centerRef.wifiControl.connected.name : ""
            selected: !!section.centerRef.wifiControl.device && section.centerRef.wifiControl.device.powered
            available: !!section.centerRef.wifiControl.device && !section.centerRef.wifiControl.busy && !section.centerRef.airplane.enabled
            onClicked: section.centerRef.wifiControl.act(section.centerRef, "power", section.centerRef.wifiControl.device.path, section.centerRef.wifiControl.device.powered ? "false" : "true")
        }
        ControlCenterToggleTile { centerRef: section.centerRef;
            title: Eitr.I18n.tr("Bluetooth"); glyph: "󰂯"
            detail: section.centerRef.bluetoothDevices.length === 1 ? section.centerRef.bluetoothDevices[0].name
                : section.centerRef.bluetoothDevices.length > 1 ? Eitr.I18n.tr("{count} devices", {count: section.centerRef.bluetoothDevices.length}) : ""
            selected: !!section.centerRef.bluetoothControl.adapter && section.centerRef.bluetoothControl.adapter.enabled
            available: !!section.centerRef.bluetoothControl.adapter && !section.centerRef.airplane.enabled
            onClicked: section.centerRef.bluetoothControl.adapter.enabled = !section.centerRef.bluetoothControl.adapter.enabled
        }
        ControlCenterToggleTile { centerRef: section.centerRef;
            title: Eitr.I18n.tr("Airplane"); glyph: "󰀝"; selected: !!section.centerRef.airplane.enabled
            available: !!section.centerRef.airplane.available && !PowerService.busy
            onClicked: { section.centerRef.powerActionId = PowerService.act("airplane", section.centerRef.airplane.enabled ? "false" : "true", function(code, message) { section.centerRef.networkActionFinished(message || (code ? "Could not complete request" : ""), code); }); if (!section.centerRef.powerActionId) section.centerRef.networkActionFinished("Could not complete request", "broker-unavailable"); }
        }
    }
    Text { visible: (section.centerRef.networkMessage || section.centerRef.wifiControl.details.error || "") !== ""; width: parent.width; wrapMode: Text.WordWrap; text: section.centerRef.networkMessage ? section.centerRef.wifiControl.actionMessage(section.centerRef.networkMessage) : (section.centerRef.wifiControl.details.error || ""); color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Quick Actions"); width: parent.width }
    GridLayout {
        width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
        ControlCenterToggleTile { centerRef: section.centerRef; title: Eitr.I18n.tr("Idle Lock"); tooltip: Eitr.I18n.tr("Lock the screen automatically when you're away."); glyph: "󱫖"; selected: section.centerRef.idleEnabled; available: !section.centerRef.idleBusy; onClicked: section.centerRef.idleToggleRequested() }
        ControlCenterToggleTile { centerRef: section.centerRef; title: Eitr.I18n.tr("Crash Notifications"); tooltip: Eitr.I18n.tr("Show help notifications when a program crashes."); glyph: "󰅚"; selected: section.centerRef.crashNotifications; available: !section.centerRef.crashOperationRef.running; onClicked: { section.centerRef.actionError = ""; section.centerRef.crashOperationRef.running = true; } }
        ControlCenterToggleTile { centerRef: section.centerRef; title: Eitr.I18n.tr("Do Not Disturb"); tooltip: Eitr.I18n.tr("Silence popups while keeping notification history."); glyph: "󰂛"; selected: section.centerRef.service.doNotDisturb; onClicked: section.centerRef.service.toggleDnd() }
        ControlCenterToggleTile { centerRef: section.centerRef;
            visible: section.centerRef.organizationPolicy.gaming === true
            title: Eitr.I18n.tr("Game Mode"); tooltip: Eitr.I18n.tr("Disable effects and popups; use the performance profile."); glyph: "󰊴"; selected: section.centerRef.gameMode
            available: !section.centerRef.gameModeOperationRef.running
            onClicked: { section.centerRef.actionError = ""; section.centerRef.gameModeOperationRef.running = true; }
        }
        ControlCenterToggleTile { centerRef: section.centerRef;
            title: Eitr.I18n.tr("Night Light"); tooltip: Eitr.I18n.tr("Use warmer screen colors."); glyph: "󰖔"
            detail: section.centerRef.displayControl.nightlight.mode === "auto" ? Eitr.I18n.tr("Scheduled") : ""
            selected: section.centerRef.displayControl.nightlight.mode === "on" || !!section.centerRef.displayControl.nightlight.active
            available: !!section.centerRef.displayControl.nightlight.available
            onClicked: section.centerRef.displayControl.setNightlight(section.centerRef.displayControl.nightlight.mode === "on" ? "off" : "on")
        }
    }
    GridLayout {
        width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Hide Bar"); tooltip: Eitr.I18n.tr("Hide the bar; press SUPER + Shift + Space to restore it."); glyph: "󰍜"; onClicked: section.centerRef.menuAction("toggle", "Desktop Bar") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Start Screensaver"); tooltip: Eitr.I18n.tr("Start the screensaver now."); glyph: "󱄄"; onClicked: section.centerRef.menuAction("toggle", "Start Screensaver") }
    }
}
