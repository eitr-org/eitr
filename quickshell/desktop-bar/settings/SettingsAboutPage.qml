import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: pageBody
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 12
    SettingsSummaryCards { context: pageBody.context }
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("About")
        foreground: view.foreground
        visible: view.page === "about"
        width: parent.width
        spacing: 12
        Repeater {
            model: view.hardware.sections || []
            SettingsText {
                required property var modelData
                text: Eitr.I18n.tr(modelData.title) + " · " + modelData.name
            }
        }
        PanelButton {
            width: 180
            foreground: view.foreground
            text: Eitr.I18n.tr("Website")
            onClicked: if (view.live)
                Qt.openUrlExternally("https://eitr.info")
        }
        PanelButton {
            width: 180
            foreground: view.foreground
            text: Eitr.I18n.tr("Repository")
            onClicked: if (view.live)
                Qt.openUrlExternally("https://github.com/eitr-org/eitr")
        }
    }
}
