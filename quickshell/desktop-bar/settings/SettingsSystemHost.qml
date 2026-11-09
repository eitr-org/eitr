import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

Flickable {
    id: hostView
    objectName: "settings-system-page"
    required property string page
    required property string title
    required property color foreground
    required property color background
    required property color accent
    property string tab: ""
    signal tabRequested(string value)
    property bool active: false
    property bool live: true
    property var checks: []
    property string checkError: ""
    property string channel: ""
    property var accountPicture: (DesktopData.topics["account.picture"] || {}).data || ({})
    property var updates: DesktopData.topics["updates.status"] || ({})
    function dismiss() {
        if (!(pictureSheet && pictureSheet.opened))
            return false;
        profileEditor.cancel();
        return true;
    }
    // Change picture: the desktop portal's file chooser (xdg-desktop-portal-gtk), then the
    // crop editor in a sheet over the window. The chooser waits for the person, so it runs
    // here rather than under the data broker's action deadline.
    function choosePicture() {
        if (!live || chooser.running || profileEditor.busy)
            return;
        profileEditor.error = "";
        chooser.running = true;
    }
    function pictureChosen(path) {
        pictureSheet.open();
        profileEditor.edit(path);
    }
    Process {
        id: chooser
        objectName: "settings-picture-chooser"
        command: ["python3", Eitr.Paths.library("eitr_avatar.py"), "choose", Eitr.I18n.tr("Choose a picture") + " · Eitr"]
        stdout: StdioCollector { id: chooserOutput }
        onExited: function(code) {
            let reply = null;
            try { reply = JSON.parse(chooserOutput.text); } catch (error) { reply = null; }
            if (!reply || !reply.ok) profileEditor.error = reply && reply.error ? reply.error : Eitr.I18n.tr("The file chooser is not available");
            else if (reply.result && reply.result.path) hostView.pictureChosen(reply.result.path);
        }
    }
    Timer {
        interval: 120000
        running: check.running
        onTriggered: {
            check.running = false;
            hostView.checkError = Eitr.I18n.tr("Check timed out");
        }
    }
    readonly property var items: helper.summary.items || []
    readonly property var matches: items.filter(entry => (!entry.tab || entry.tab === tab)
        && [entry.group || "", entry.title, entry.detail].join(" ").toLocaleLowerCase().includes(shortcutQuery.trim().toLocaleLowerCase()))
    contentHeight: content.implicitHeight + 18
    boundsBehavior: Flickable.StopAtBounds
    clip: true
    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
    }
    function demand() {
        DesktopData.releaseOwner(hostView);
        if (!active || !live)
            return;
        if (page === "user")
            DesktopData.observe("account.picture", hostView);
        if (page === "updates") {
            DesktopData.observe("updates.status", hostView);
            channelQuery.running = true;
        }
    }
    onActiveChanged: demand()
    onPageChanged: {
        helper.summary = {
            items: []
        };
        contentY = 0;
        shortcutQuery = "";
        if ((pictureSheet && pictureSheet.opened))
            profileEditor.cancel();
        Qt.callLater(demand);
    }
    Component.onDestruction: DesktopData.releaseOwner(hostView)
    property string shortcutQuery: ""
    readonly property var pictureSheet: page === "user" && pageLoader.item ? pageLoader.item.pictureSheet : null
    readonly property var profileEditor: page === "user" && pageLoader.item ? pageLoader.item.profileEditor : null
    signal pageRequested(string page)
    function runControl(entry, selection) {
        if (!live) return;
        if (entry.command) Quickshell.execDetached(entry.command);
        else if (entry.page) pageRequested(entry.page);
        else action(entry.actionMenu, entry.actionTitle || entry.title);
    }
    function action(menu, title) {
        if (live)
            Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), menu, title]);
    }
    SettingsHelper {
        id: helper
        objectName: "settings-system-helper"
        active: hostView.active && ["keybinds", "security", "assistant", "about"].includes(hostView.page)
        live: hostView.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/settings-system.py")
        summaryArguments: [hostView.page === "assistant" ? "assistants" : hostView.page]
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
        active: hostView.active && hostView.page === "default-apps"
        live: hostView.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/default-apps.py")
        schema: ({
                items: "array"
            })
        summary: ({
                items: []
            })
    }
    PreferenceWatch {
        path: hostView.active && hostView.live && hostView.page === "updates" ? "/etc/pacman.conf" : ""
        onChanged: if (hostView.active && hostView.live && hostView.page === "updates" && !channelQuery.running)
            channelQuery.running = true
    }
    Process {
        id: channelQuery
        command: ["/usr/lib/eitr/eitr-system", "channel-status"]
        stdout: StdioCollector {
            id: channelOutput
        }
        onExited: function (code) {
            hostView.channel = code === 0 ? channelOutput.text.trim() : "";
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
            hostView.checkError = result.ok ? "" : result.error;
            if (result.ok)
                hostView.checks = result.data.checks;
        }
    }
    component Label: Text {
        width: parent.width
        color: hostView.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.WordWrap
    }
    property alias helper: helper
    property alias defaults: defaults
    property alias check: check
    property alias chooser: chooser
    Component { id: keybindsComponent; SettingsKeybindsPage { context: hostView } }
    Component { id: defaultappsComponent; SettingsDefaultAppsPage { context: hostView } }
    Component { id: userComponent; SettingsUserPage { context: hostView } }
    Component { id: securityComponent; SettingsSecurityPage { context: hostView } }
    Component { id: assistantsComponent; SettingsAssistantPage { context: hostView } }
    Component { id: updatesComponent; SettingsUpdatesPage { context: hostView } }
    Component { id: checkpcComponent; SettingsCheckPage { context: hostView } }
    Component { id: aboutComponent; SettingsAboutPage { context: hostView } }
    Column {
        id: content
        width: hostView.width
        spacing: 12
        SettingsPageHeader { page: hostView.page; foreground: hostView.foreground }
        Loader {
            id: pageLoader
            width: parent.width
            height: item ? item.implicitHeight : 0
            sourceComponent: ({"keybinds": keybindsComponent, "default-apps": defaultappsComponent, "user": userComponent, "security": securityComponent, "assistant": assistantsComponent, "updates": updatesComponent, "check-pc": checkpcComponent, "about": aboutComponent})[hostView.page] || null
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
            foreground: hostView.foreground
            onClicked: if (hostView.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", hostView.page === "keybinds" ? "shortcuts" : hostView.page === "security" || hostView.page === "user" ? "security" : hostView.page === "updates" || hostView.page === "check-pc" ? "maintenance" : hostView.page === "about" ? "information" : hostView.page === "assistant" ? "development" : "control-center"])
        }
    }
}
