import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

Column {
    id: management
    objectName: "settings-manage-users"
    required property var context
    required property var accounts
    property alias sheet: confirmation
    width: parent ? parent.width : 0
    spacing: 12
    PanelButton {
        objectName: "settings-manage-create-user"
        width: 180
        text: Eitr.I18n.tr("Create User…")
        foreground: management.context.foreground
        onClicked: management.context.action("users", "Create User…")
    }
    Repeater {
        model: management.visible ? management.accounts : []
        ControlCard {
            id: accountCard
            required property var modelData
            width: management.width
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            foreground: management.context.foreground
            title: modelData.title || modelData.login
            Row {
                width: parent.width
                spacing: 12
                Eitr.Avatar {
                    size: 48
                    width: 48
                    height: 48
                    source: accountCard.modelData.picture ? "file://" + accountCard.modelData.picture : ""
                    initial: accountCard.modelData.initial || ""
                    accent: management.context.accent
                    background: management.context.background
                }
                SettingsText {
                    width: Math.max(100, parent.width - 60)
                    text: accountCard.modelData.login + " · " + (accountCard.modelData.administrator ? Eitr.I18n.tr("Administrator") : Eitr.I18n.tr("Standard"))
                    wrapMode: Text.WordWrap
                }
            }
            Flow {
                width: parent.width
                spacing: 8
                PanelButton {
                    width: 150
                    text: Eitr.I18n.tr("Change type")
                    foreground: management.context.foreground
                    available: !terminal.running
                    onClicked: confirmation.review("set-type", accountCard.modelData)
                }
                PanelButton {
                    width: 150
                    visible: !accountCard.modelData.current
                    text: Eitr.I18n.tr("Set password")
                    foreground: management.context.foreground
                    available: !terminal.running
                    onClicked: confirmation.review("set-password", accountCard.modelData)
                }
                PanelButton {
                    width: 110
                    visible: !accountCard.modelData.current
                    text: Eitr.I18n.tr("Remove")
                    foreground: management.context.foreground
                    available: !terminal.running
                    onClicked: confirmation.review("remove", accountCard.modelData)
                }
            }
        }
    }
    SettingsAccountSheet {
        id: confirmation
        view: management.context
        onConfirmed: function(arguments) {
            if (!management.context.live || management.context.helper.summary.administrator !== true) return;
            terminal.command = [Eitr.Paths.code("walker/bin/menu-path/kitty"), "-e", "python3",
                Eitr.Paths.code("walker/scripts/actions/task-terminal.py"), "python3",
                Eitr.Paths.code("walker/scripts/actions/system/users.py")].concat(arguments);
            terminal.running = true;
        }
    }
    Process {
        id: terminal
        onExited: management.context.helper.refresh()
    }
}
