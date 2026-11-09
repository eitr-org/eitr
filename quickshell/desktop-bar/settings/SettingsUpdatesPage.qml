import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../ChoiceLists.js" as ChoiceLists

Column {
    required property var context
    readonly property var view: context
    readonly property var helper: context.helper
    width: parent ? parent.width : 0
    spacing: 12
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Updates")
        foreground: view.foreground
        visible: view.page === "updates"
        width: parent.width
        spacing: 12
        SettingsText {
            text: Eitr.I18n.tr("Update Channel")
        }
        ControlRow {
            text: Eitr.I18n.tr("Update Channel")
            description: Eitr.I18n.tr("Choose stable builds or try new builds first.")
            foreground: view.foreground
            ChoiceSegmented { gold: SettingsInk.gold; background: SettingsInk.background;
                foreground: view.foreground
                choices: ChoiceLists.updateChannels
                current: view.channel
                onChosen: value => {
                    if (view.live && value !== view.channel)
                        Quickshell.execDetached([Eitr.Paths.code("walker/bin/menu-path/kitty"), "-e", "python3", Eitr.Paths.code("walker/scripts/actions/task-terminal.py"), "python3", Eitr.Paths.code("walker/scripts/actions/system/update-channel.py"), "set", value]);
                }
            }
        }
        SettingsText {
            text: view.updates.status === "ready" && !view.updates.inFlight ? Eitr.I18n.tr("Pending updates: %1", [(view.updates.data || {}).count]) : view.updates.status === "loading" || view.updates.inFlight ? Eitr.I18n.tr("Checking for updates…") : Eitr.I18n.tr("Pending updates unavailable")
        }
        PanelButton {
            width: 200
            foreground: view.foreground
            text: Eitr.I18n.tr("System Update")
            onClicked: view.action("system", "System Update")
        }
    }
    PanelButton {
        visible: ["security", "updates"].includes(view.page)
        width: 160
        text: Eitr.I18n.tr("Refresh")
        foreground: view.foreground
        onClicked: if (view.live) {
            if (view.page === "updates") {
                channelQuery.running = true;
                DesktopData.refresh("updates.status");
            } else
                helper.refresh();
        }
    }
}
