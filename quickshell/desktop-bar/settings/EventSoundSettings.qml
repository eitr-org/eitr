import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
Column {
    id: sounds
    required property color foreground
    required property color accent
    property bool live: true
    property real controlInset: 0
    property bool hasBattery: false
    spacing: PanelStyle.selectionRowGap
    // Optional event sounds; the charger row only on PCs with a battery.
    Repeater {
        model: [{setting: "notifications", label: Eitr.I18n.tr("Notification sounds")},
                {setting: "charger", label: Eitr.I18n.tr("Charger sounds"), battery: true}]
        ToggleRow {
            required property var modelData
            controlInset: sounds.controlInset
            visible: !modelData.battery || sounds.hasBattery
            text: modelData.label
            description: modelData.battery ? Eitr.I18n.tr("Play a sound when the charger is connected.") : Eitr.I18n.tr("Play a sound with notification popups.")
            foreground: sounds.foreground; accent: sounds.accent
            checked: EventSounds[modelData.setting]
            onToggled: checked => { if (sounds.live) EventSounds.setEnabled(modelData.setting, checked); }
        }
    }
}
