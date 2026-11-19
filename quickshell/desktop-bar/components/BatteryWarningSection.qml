import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property color foreground
    required property color accent
    property var battery: PowerService.battery
    visible: !!battery && !!battery.available
    width: parent ? parent.width : 0
    spacing: 12

    readonly property int lowValue: (battery && battery.low !== undefined) ? battery.low : 10
    readonly property int criticalValue: (battery && battery.critical !== undefined) ? battery.critical : 5

    property int pendingLow: lowValue
    property int pendingCritical: criticalValue

    onLowValueChanged: {
        if (!lowSlider.pressed) pendingLow = lowValue;
    }
    onCriticalValueChanged: {
        if (!criticalSlider.pressed) pendingCritical = criticalValue;
    }

    function saveLevels(newLow, newCritical) {
        if (newCritical >= newLow) {
            newCritical = Math.max(2, newLow - 1);
        }
        PowerService.setWarningLevels(newLow, newCritical);
    }

    PanelDivider {
        width: parent.width
        height: 8
        foreground: section.foreground
    }

    Text {
        text: Eitr.I18n.tr("Battery Warnings")
        color: section.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
    }

    ControlRow {
        SettingsTarget { objectName: "setting-displays-battery-low" }
        width: parent.width
        text: Eitr.I18n.tr("Low battery warning")
        description: Eitr.I18n.tr("Notify when the battery drops to this level.")
        foreground: section.foreground
        PanelSlider {
            id: lowSlider
            width: parent.width
            accent: section.accent
            foreground: section.foreground
            from: 2
            to: 50
            stepSize: 1
            valueText: Math.round(value) + "%"
            Accessible.name: Eitr.I18n.tr("Low battery warning")
            Binding { target: lowSlider; property: "value"; value: section.pendingLow; when: !lowSlider.pressed }
            onMoved: {
                const rounded = Math.round(value);
                section.pendingLow = rounded;
                if (section.pendingCritical >= rounded) {
                    section.pendingCritical = Math.max(2, rounded - 1);
                }
            }
            onPressedChanged: {
                if (!pressed) {
                    section.saveLevels(section.pendingLow, section.pendingCritical);
                }
            }
        }
    }

    ControlRow {
        SettingsTarget { objectName: "setting-displays-battery-critical" }
        width: parent.width
        text: Eitr.I18n.tr("Critical battery warning")
        description: Eitr.I18n.tr("Send an urgent alert when the battery drops to this level.")
        foreground: section.foreground
        PanelSlider {
            id: criticalSlider
            width: parent.width
            accent: section.accent
            foreground: section.foreground
            from: 2
            to: 50
            stepSize: 1
            valueText: Math.round(value) + "%"
            Accessible.name: Eitr.I18n.tr("Critical battery warning")
            Binding { target: criticalSlider; property: "value"; value: section.pendingCritical; when: !criticalSlider.pressed }
            onMoved: {
                const rounded = Math.round(value);
                section.pendingCritical = rounded;
                if (rounded >= section.pendingLow) {
                    section.pendingLow = Math.min(50, rounded + 1);
                }
            }
            onPressedChanged: {
                if (!pressed) {
                    section.saveLevels(section.pendingLow, section.pendingCritical);
                }
            }
        }
    }
}
