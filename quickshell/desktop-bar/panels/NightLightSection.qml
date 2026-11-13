import ".."
import QtQuick
import Eitr as Eitr
import QtQuick.Controls.Basic as Controls
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var menu
    required property var scheduleSettle
    required property var nightOperation
    readonly property alias startFieldItem: startField
    readonly property alias endFieldItem: endField
    width: parent.width
    spacing: 12
    visible: section.menu.settingsSection !== "displays"
    Row {
        width: parent.width
        height: 40
        Column {
            width: parent.width - 88
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text { text: Eitr.I18n.tr("Night Light"); color: section.menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            Text { width: parent.width; elide: Text.ElideRight; text: section.menu.nightlight.mode === "auto" ? Eitr.I18n.tr("Automatic · {start} - {end}", {start: section.menu.displayTime(section.menu.nightlight.start || "18:00"), end: section.menu.displayTime(section.menu.nightlight.end || "09:00")}) : Eitr.I18n.tr("Manual"); color: section.menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
        }
        PanelButton {
            id: editButton
            SettingsTarget { objectName: "setting-displays-edit-schedule" }
            icon: true
            width: 28
            height: 28
            anchors.verticalCenter: parent.verticalCenter
            text: "󰏫"
            foreground: section.menu.foreground
            available: section.menu.nightlight.available
            selected: section.menu.editingSchedule
            onClicked: {
                if (section.menu.editingSchedule && section.menu.scheduleDirty) section.scheduleSettle.restart();
                if (!section.menu.editingSchedule) section.menu.syncSchedule();
                section.menu.editingSchedule = !section.menu.editingSchedule;
            }
            HoverHandler { id: editHover }
            BarTooltip { target: editButton; hovered: editHover.hovered; text: Eitr.I18n.tr("Edit schedule"); background: section.menu.background; foreground: section.menu.foreground }
        }
        Item { width: 8; height: 1 }
        PanelSwitch {
            anchors.verticalCenter: parent.verticalCenter
            checked: section.menu.nightlight.enabled
            SettingsTarget { objectName: "setting-displays-night-light" }
            enabled: section.menu.nightlight.available && !section.nightOperation.running
            foreground: section.menu.foreground
            accent: section.menu.accent
            onClicked: section.menu.setNightlight(checked ? "on" : "off")
        }
    }
    Column {
        visible: section.menu.editingSchedule
        width: parent.width
        height: visible ? 58 : 0
        spacing: 2
        Row {
            width: parent.width
            height: 16
            spacing: 8
            Text { width: (parent.width - 68) / 2; height: parent.height; text: Eitr.I18n.tr("Start"); color: section.menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            Text { width: (parent.width - 68) / 2; height: parent.height; text: Eitr.I18n.tr("End"); color: section.menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            Text { width: 52; height: parent.height; text: Eitr.I18n.tr("Auto"); color: section.menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
        }
        Row {
            width: parent.width
            height: 40
            spacing: 8
            Controls.TextField {
                id: startField
                SettingsTarget { objectName: "setting-displays-schedule-start" }
                width: (parent.width - 68) / 2
                height: parent.height
                color: section.menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                selectByMouse: true
                onTextEdited: { section.menu.scheduleDirty = true; section.scheduleSettle.restart(); }
                HoverHandler { cursorShape: Qt.IBeamCursor }
                background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(section.menu.foreground.r, section.menu.foreground.g, section.menu.foreground.b, 0.08); border.width: 1; border.color: Qt.rgba(section.menu.foreground.r, section.menu.foreground.g, section.menu.foreground.b, 0.2) }
            }
            Controls.TextField {
                id: endField
                SettingsTarget { objectName: "setting-displays-schedule-end" }
                width: (parent.width - 68) / 2
                height: parent.height
                color: section.menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                selectByMouse: true
                onTextEdited: { section.menu.scheduleDirty = true; section.scheduleSettle.restart(); }
                HoverHandler { cursorShape: Qt.IBeamCursor }
                background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(section.menu.foreground.r, section.menu.foreground.g, section.menu.foreground.b, 0.08); border.width: 1; border.color: Qt.rgba(section.menu.foreground.r, section.menu.foreground.g, section.menu.foreground.b, 0.2) }
            }
            PanelSwitch {
                anchors.verticalCenter: parent.verticalCenter
                checked: section.menu.nightlight.mode === "auto"
                SettingsTarget { objectName: "setting-displays-schedule-auto" }
                enabled: section.menu.nightlight.available && !section.nightOperation.running
                foreground: section.menu.foreground
                accent: section.menu.accent
                onClicked: {
                    section.scheduleSettle.stop();
                    section.menu.configureNightlight(checked ? "auto" : (section.menu.nightlight.enabled ? "on" : "off"));
                }
            }
        }
    }
    Text {
        visible: section.menu.nightlightError !== ""
        text: section.menu.nightlightError
        color: section.menu.foreground
        opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
    }
}
