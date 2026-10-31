import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr

Column {
    id: group
    required property var centerRef
    required property string settingKey
    required property string title
    width: parent.width
    spacing: 6
    ControlCenterOptionHeading { centerRef: group.centerRef; text: group.title }
    Flow {
        width: parent.width; spacing: 6
        Repeater {
            model: group.centerRef.terminalAppearanceChoices[group.settingKey] || []
            PanelButton {
                required property var modelData
                width: (parent.width - 6) / 2
                text: modelData.label; textSize: 12
                foreground: group.centerRef.foreground
                selected: group.centerRef.terminalAppearance[group.settingKey] === modelData.value
                leadingIcon: selected ? "\u{F00C}" : ""
                available: !group.centerRef.terminalWriteRef.running
                onClicked: if (!selected) group.centerRef.run(group.centerRef.terminalWriteRef,
                    ["python3", group.centerRef.terminalScript, "set", group.settingKey, modelData.value])
            }
        }
    }
}
