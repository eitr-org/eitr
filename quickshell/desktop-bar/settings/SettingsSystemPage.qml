import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ChoiceLists.js" as ChoiceLists
import "../JsonState.js" as JsonState

Flickable {
    id: view
    objectName: "settings-system-page"
    required property string page
    required property string title
    required property color foreground
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var checks: []
    property string checkError: ""
    property string channel: ""
    property var accountPicture: (DesktopData.topics["account.picture"] || {}).data || ({})
    property var hardware: (DesktopData.topics["hardware.details"] || {}).data || ({})
    property var updates: DesktopData.topics["updates.status"] || ({})
    property bool editingPicture: false
    onEditingPictureChanged: if (editingPicture)
        profileContext.page = "picture"
    function dismiss() {
        if (!editingPicture)
            return false;
        editingPicture = false;
        return true;
    }
    Timer {
        interval: 120000
        running: check.running
        onTriggered: {
            check.running = false;
            view.checkError = Eitr.I18n.tr("Check timed out");
        }
    }
    readonly property var items: helper.summary.items || []
    readonly property var matches: items.filter(entry => [entry.group || "", entry.title, entry.detail].join(" ").toLocaleLowerCase().includes(query.text.trim().toLocaleLowerCase()))
    contentHeight: content.implicitHeight + 18
    boundsBehavior: Flickable.StopAtBounds
    clip: true
    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
    }
    function demand() {
        DesktopData.releaseOwner(view);
        if (!active || !live)
            return;
        if (page === "user")
            DesktopData.observe("account.picture", view);
        if (page === "about")
            DesktopData.observe("hardware.details", view);
        if (page === "updates") {
            DesktopData.observe("updates.status", view);
            channelQuery.running = true;
        }
    }
    onActiveChanged: demand()
    onPageChanged: {
        helper.summary = {
            items: []
        };
        contentY = 0;
        query.text = "";
        editingPicture = false;
        Qt.callLater(demand);
    }
    Component.onDestruction: DesktopData.releaseOwner(view)
    function menu(name) {
        if (live)
            Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:" + name]);
    }
    function action(menu, title) {
        if (live)
            Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), menu, title]);
    }
    SettingsHelper {
        id: helper
        objectName: "settings-system-helper"
        active: view.active && ["keybinds", "git-cloud", "security", "about"].includes(view.page)
        live: view.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/settings-system.py")
        summaryArguments: [view.page]
        summary: ({
                items: []
            })
        schema: ({
                items: "array"
            })
    }
    SettingsHelper {
        id: defaults
        objectName: "settings-default-apps-helper"
        active: view.active && view.page === "default-apps"
        live: view.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/default-apps.py")
        schema: ({
                items: "array"
            })
        summary: ({
                items: []
            })
    }
    PreferenceWatch {
        path: view.active && view.live && view.page === "updates" ? "/etc/pacman.conf" : ""
        onChanged: if (view.active && view.live && view.page === "updates" && !channelQuery.running)
            channelQuery.running = true
    }
    Process {
        id: channelQuery
        command: ["/usr/lib/eitr/eitr-system", "channel-status"]
        stdout: StdioCollector {
            id: channelOutput
        }
        onExited: function (code) {
            view.channel = code === 0 ? channelOutput.text.trim() : "";
        }
    }
    Process {
        id: check
        command: ["eitr", "check", "--json"]
        stdout: StdioCollector {
            id: checkOutput
        }
        onExited: function (code) {
            const result = JsonState.parse(checkOutput.text, code, {
                checks: "array"
            });
            view.checkError = result.ok ? "" : result.error;
            if (result.ok)
                view.checks = result.data.checks;
        }
    }
    component Label: Text {
        width: parent.width
        color: view.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.WordWrap
    }
    Column {
        id: content
        width: view.width
        spacing: 12
        SettingsPageHeader {
            page: view.page
            foreground: view.foreground
        }
        TextField {
            id: query
            visible: view.page === "keybinds"
            width: parent.width
            placeholderText: Eitr.I18n.tr("Search shortcuts")
            placeholderTextColor: Qt.alpha(view.foreground, PanelStyle.secondaryTextOpacity)
            color: view.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
            background: Rectangle {
                radius: DesktopStyle.radius(6)
                color: Qt.alpha(view.foreground, 0.05)
            }
        }
        Repeater {
            model: ["keybinds", "git-cloud", "security", "about"].includes(view.page) ? view.matches : []
            ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
                id: summaryCard
                title: Eitr.I18n.tr(modelData.title)
                foreground: view.foreground
                required property var modelData
                required property int index
                width: content.width
                spacing: 5
                Label {
                    visible: view.page === "keybinds" && (summaryCard.index === 0 || view.matches[summaryCard.index - 1].group !== summaryCard.modelData.group)
                    text: summaryCard.modelData.group || ""
                    font.pixelSize: PanelStyle.captionSize
                    color: Qt.alpha(view.foreground, PanelStyle.secondaryTextOpacity)
                }
                Label {
                    text: Eitr.I18n.tr(summaryCard.modelData.title)
                }
                Label {
                    text: Eitr.I18n.tr(summaryCard.modelData.detail || "Unavailable")
                    color: Qt.alpha(view.foreground, PanelStyle.secondaryTextOpacity)
                    font.pixelSize: PanelStyle.captionSize
                }
                PanelButton {
                    visible: !!summaryCard.modelData.menu || !!summaryCard.modelData.actionMenu
                    width: 180
                    text: Eitr.I18n.tr("Open settings")
                    foreground: view.foreground
                    onClicked: summaryCard.modelData.menu ? view.menu(summaryCard.modelData.menu) : view.action(summaryCard.modelData.actionMenu, summaryCard.modelData.actionTitle || summaryCard.modelData.title)
                }
                Rectangle {
                    width: parent.width
                    height: 1
                    color: Qt.alpha(view.foreground, PanelStyle.dividerAlpha)
                }
            }
        }
        Label {
            visible: view.page === "keybinds" && view.matches.length === 0
            text: Eitr.I18n.tr("No matching shortcuts")
        }
        Repeater {
            model: view.page === "default-apps" ? defaults.summary.items || [] : []
            ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
                id: appCard
                objectName: "settings-default-app-card"
                required property var modelData
                width: content.width
                title: Eitr.I18n.tr(modelData.label)
                foreground: view.foreground
                ControlRow {
                    text: Eitr.I18n.tr(appCard.modelData.label)
                    description: Eitr.I18n.tr("Choose the app used for this file or link type.")
                    foreground: view.foreground
                    ChoiceDropdown { gold: SettingsInk.gold; background: SettingsInk.background;
                        foreground: view.foreground
                        choices: appCard.modelData.choices
                        current: appCard.modelData.current
                        available: !defaults.busy
                        onChosen: value => defaults.change(["set", appCard.modelData.kind, value])
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("User")
            foreground: view.foreground
            visible: view.page === "user"
            width: parent.width
            spacing: 12
            Eitr.Avatar {
                width: 80
                height: 80
                source: view.accountPicture.path ? "file://" + view.accountPicture.path : ""
                initial: view.accountPicture.initial || ""
                accent: view.accent
                background: view.background
            }
            Label {
                text: view.accountPicture.name || Eitr.I18n.tr("Unavailable")
            }
            PanelButton {
                width: 200
                foreground: view.foreground
                text: Eitr.I18n.tr("Profile picture")
                onClicked: view.editingPicture = !view.editingPicture
            }
            ProfilePicture {
                objectName: "settings-profile-picture"
                width: parent.width
                visible: view.editingPicture
                centerRef: QtObject {
                    id: profileContext
                    property var accountPicture: view.accountPicture
                    property color foreground: view.foreground
                    property color background: view.background
                    property color accent: view.accent
                    property string page: "user"
                    onPageChanged: if (page === "general")
                        view.editingPicture = false
                }
            }
        }
        Row {
            visible: view.page === "git-cloud"
            spacing: 6
            PanelButton {
                width: 180
                foreground: view.foreground
                text: Eitr.I18n.tr("Git Accounts")
                onClicked: view.menu("git-accounts")
            }
            PanelButton {
                width: 180
                foreground: view.foreground
                text: Eitr.I18n.tr("Cloud")
                onClicked: view.menu("cloud")
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Updates")
            foreground: view.foreground
            visible: view.page === "updates"
            width: parent.width
            spacing: 12
            Label {
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
            Label {
                text: view.updates.status === "ready" && !view.updates.inFlight ? Eitr.I18n.tr("Pending updates: %1", [(view.updates.data || {}).count]) : view.updates.status === "loading" || view.updates.inFlight ? Eitr.I18n.tr("Checking for updates…") : Eitr.I18n.tr("Pending updates unavailable")
            }
            PanelButton {
                width: 200
                foreground: view.foreground
                text: Eitr.I18n.tr("System Update")
                onClicked: view.action("system", "System Update")
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Check This PC")
            foreground: view.foreground
            visible: view.page === "check-pc"
            width: parent.width
            spacing: 12
            PanelButton {
                width: 200
                text: Eitr.I18n.tr("Check This PC")
                foreground: view.foreground
                loading: check.running
                onClicked: if (view.live && !check.running)
                    check.running = true
            }
            Label {
                visible: view.checkError !== ""
                text: view.checkError
            }
            Repeater {
                model: view.checks
                Column {
                    required property var modelData
                    width: parent.width
                    spacing: 4
                    Label {
                        text: Eitr.I18n.tr(parent.modelData.status) + " · " + Eitr.I18n.tr(parent.modelData.group)
                    }
                    Label {
                        text: Eitr.I18n.tr(parent.modelData.meaning || parent.modelData.message)
                    }
                    Label {
                        visible: !!parent.modelData.meaning
                        text: Eitr.I18n.tr(parent.modelData.message)
                        font.pixelSize: PanelStyle.captionSize
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("About")
            foreground: view.foreground
            visible: view.page === "about"
            width: parent.width
            spacing: 12
            Repeater {
                model: view.hardware.sections || []
                Label {
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
        PanelButton {
            visible: ["git-cloud", "security", "updates"].includes(view.page)
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
        Label {
            visible: helper.active && helper.error !== ""
            text: helper.error
        }
        Label {
            visible: defaults.active && defaults.error !== ""
            text: defaults.error
        }
        PanelButton {
            objectName: "settings-page-handbook"
            width: 160
            text: Eitr.I18n.tr("Learn more")
            foreground: view.foreground
            onClicked: if (view.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", view.page === "git-cloud" ? "git-accounts" : view.page === "keybinds" ? "shortcuts" : view.page === "security" || view.page === "user" ? "security" : view.page === "updates" || view.page === "check-pc" ? "maintenance" : view.page === "about" ? "information" : "control-center"])
        }
    }
}
