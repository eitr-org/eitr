import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: backupPage
    required property var context
    readonly property var view: context
    readonly property var status: view.backupStatus || ({hasBackup: false, lastBackup: null, lastBackupExists: false, lastRestore: null, undoPoints: []})
    readonly property var lastBackup: status.lastBackup || null
    readonly property var undoPoints: status.undoPoints || []
    // Backup, restore and undo run in the task terminal, which shows what happened.
    function runInTerminal(arguments) {
        if (!view.live)
            return;
        Quickshell.execDetached([
            Eitr.Paths.code("walker/bin/menu-path/kitty"),
            "--class", "system-backup",
            "-e", "python3", Eitr.Paths.code("walker/scripts/actions/task-terminal.py"),
            "python3", Eitr.Paths.library("eitr_backup/cli.py"), ...arguments
        ]);
    }
    function launchMode(mode) { runInTerminal(["wizard", "--mode", mode]); }
    width: parent ? parent.width : 0
    spacing: 12

    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("Latest backup")
        foreground: backupPage.view.foreground
        width: parent.width
        spacing: 8
        SettingsText {
            visible: !backupPage.status.hasBackup
            text: Eitr.I18n.tr("No backup created yet.")
        }
        SettingsText {
            visible: !backupPage.status.hasBackup
            text: Eitr.I18n.tr("Encrypted archives store your Eitr preferences, app settings, chosen folders and installed app lists in one file.")
            font.pixelSize: PanelStyle.captionSize
            color: Qt.alpha(backupPage.view.foreground, PanelStyle.secondaryTextOpacity)
        }
        SettingsText {
            visible: backupPage.status.hasBackup && backupPage.lastBackup !== null
            text: backupPage.lastBackup ? Eitr.I18n.tr("Last backup: %1 · %2", [String(backupPage.lastBackup.timestamp || "").slice(0, 16).replace("T", " "), backupPage.lastBackup.sizeFormatted || ""]) : ""
        }
        SettingsText {
            visible: backupPage.status.hasBackup && backupPage.lastBackup !== null
            text: backupPage.lastBackup ? Eitr.I18n.tr("Destination: %1", [backupPage.lastBackup.destination || ""]) : ""
            font.pixelSize: PanelStyle.captionSize
            color: Qt.alpha(backupPage.view.foreground, PanelStyle.secondaryTextOpacity)
        }
        SettingsText {
            visible: backupPage.status.hasBackup && !backupPage.status.lastBackupExists
            text: Eitr.I18n.tr("Archive not found at that location (external drive may be disconnected or moved).")
            font.pixelSize: PanelStyle.captionSize
            color: Qt.alpha(backupPage.view.foreground, PanelStyle.secondaryTextOpacity)
        }
        SettingsText {
            visible: backupPage.view.backupError !== ""
            text: backupPage.view.backupError
            font.pixelSize: PanelStyle.captionSize
            color: Qt.alpha(backupPage.view.foreground, PanelStyle.secondaryTextOpacity)
        }
    }

    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("Backup actions")
        foreground: backupPage.view.foreground
        width: parent.width
        spacing: 10
        ControlRow {
            SettingsTarget { objectName: "setting-backup-create" }
            controlWidth: 190
            text: Eitr.I18n.tr("Create backup")
            description: Eitr.I18n.tr("Choose settings, personal folders and apps to save into an encrypted archive.")
            foreground: backupPage.view.foreground
            PanelButton {
                width: parent.width
                foreground: backupPage.view.foreground
                text: Eitr.I18n.tr("Create backup…")
                onClicked: backupPage.launchMode("create")
            }
        }
        ControlRow {
            SettingsTarget { objectName: "setting-backup-restore" }
            controlWidth: 190
            text: Eitr.I18n.tr("Restore from backup")
            description: Eitr.I18n.tr("Inspect an encrypted archive, restore files with undo and reinstall apps.")
            foreground: backupPage.view.foreground
            PanelButton {
                width: parent.width
                foreground: backupPage.view.foreground
                text: Eitr.I18n.tr("Restore…")
                onClicked: backupPage.launchMode("restore")
            }
        }
    }

    ControlCard {
        visible: backupPage.undoPoints.length > 0
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("Restore undo points")
        foreground: backupPage.view.foreground
        width: parent.width
        spacing: 6
        Repeater {
            model: backupPage.undoPoints.slice(0, 3)
            ControlRow {
                required property var modelData
                text: String(modelData.timestamp || "").slice(0, 16).replace("T", " ")
                description: Eitr.I18n.tr("Puts back %1 replaced files and removes %2 added ones", [String(modelData.replacedCount || 0), String(modelData.addedCount || 0)])
                foreground: backupPage.view.foreground
                PanelButton {
                    width: parent.width
                    text: Eitr.I18n.tr("Undo")
                    foreground: backupPage.view.foreground
                    onClicked: backupPage.runInTerminal(["undo", modelData.id])
                }
            }
        }
    }

    PanelButton {
        width: 160
        text: Eitr.I18n.tr("Refresh")
        foreground: backupPage.view.foreground
        onClicked: if (backupPage.view.live) backupPage.view.backupQuery.running = true
    }
}
