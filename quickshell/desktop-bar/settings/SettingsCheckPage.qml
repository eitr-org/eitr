import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    required property var context
    readonly property var view: context
    readonly property var check: context.check
    width: parent ? parent.width : 0
    spacing: 12
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Check This PC")
        foreground: view.foreground
        visible: view.page === "check-pc"
        width: parent.width
        spacing: 12
        PanelButton {
            SettingsTarget { objectName: "setting-check-pc-check-this-pc" }
            width: 200
            text: Eitr.I18n.tr("Check This PC")
            foreground: view.foreground
            loading: check.running
            onClicked: if (view.live && !check.running)
                check.running = true
        }
        SettingsText {
            visible: view.checkError !== ""
            text: view.checkError
        }
        Repeater {
            model: view.checks
            Column {
                required property var modelData
                width: parent.width
                spacing: 4
                SettingsText {
                    text: Eitr.I18n.tr(parent.modelData.status) + " · " + Eitr.I18n.tr(parent.modelData.group)
                }
                SettingsText {
                    text: Eitr.I18n.tr(parent.modelData.meaning || parent.modelData.message)
                }
                SettingsText {
                    visible: !!parent.modelData.meaning
                    text: Eitr.I18n.tr(parent.modelData.message)
                    font.pixelSize: PanelStyle.captionSize
                }
            }
        }
    }
}
