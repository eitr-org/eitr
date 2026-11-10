import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: controls
    required property var model
    property bool live: true
    property color foreground: "white"
    property color background: "#202024"
    property color gold: foreground
    property string helperText: ""
    spacing: 10
    ChoiceDropdown {
        width: parent.width
        floatingLabel: Eitr.I18n.tr("Apply wallpaper to")
        helperText: controls.helperText
        foreground: controls.foreground
        background: controls.background
        gold: controls.gold
        choices: [{id: "global", label: Eitr.I18n.tr("All displays")}].concat(controls.model.monitorName ? [
            {id: "monitor", label: Eitr.I18n.tr("This display") + " · " + controls.model.monitorName}
        ].concat(controls.model.workspaceNumber ? [
            {id: "workspace", label: Eitr.I18n.tr("This workspace") + " · " + Eitr.I18n.tr("%1, workspace %2", [controls.model.monitorName, controls.model.workspaceNumber])}
        ] : []) : [])
        current: controls.model.scope
        onChosen: value => { if (controls.live) controls.model.scope = value; }
    }
    Repeater {
        model: controls.model.assignments
        Row {
            required property var modelData
            width: controls.width
            spacing: 8
            Text {
                width: parent.width - clearButton.width - parent.spacing
                anchors.verticalCenter: parent.verticalCenter
                text: (modelData.number ? Eitr.I18n.tr("%1, workspace %2", [modelData.monitor, modelData.number]) : modelData.monitor) + " · " + modelData.path.split("/").pop()
                color: controls.foreground
                font.family: DesktopFonts.family
                font.pixelSize: 12
                elide: Text.ElideMiddle
            }
            PanelButton {
                id: clearButton
                text: Eitr.I18n.tr("Clear")
                foreground: controls.foreground
                onClicked: if (controls.live) controls.model.wallpaperAction("clear", ["--key", modelData.key])
            }
        }
    }
}
