import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Flickable {
    id: hostView
    ScrollBar.vertical: PanelScrollBar { foreground: hostView.foreground }
    objectName: "settings-desktop-page"
    required property string page
    required property string title
    required property color foreground
    required property color background
    required property color accent
    signal tabRequested(string value)
    property string tab: "theme"
    property bool active: false
    property bool live: true
    property var notifications: null
    property bool idleEnabled: false
    signal themesRequested
    signal idleToggleRequested
    contentHeight: content.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    onPageChanged: {
        contentY = 0;
        Qt.callLater(refreshPage);
    }
    function refreshPage() {
        if (!active || !live)
            return;
        state.loadStyle();
        if (page === "appearance") {
            themeModel.open("theme", null);
            wallpaperModel.open("wallpaper", null);
        }
    }
    SettingsNotificationState {
        id: notificationState
        active: hostView.active && hostView.page === "notifications"
        live: hostView.live
    }
    SettingsStyleState {
        id: state
        objectName: "settings-style-state"
        active: hostView.active
        live: hostView.live
        property color foreground: hostView.foreground
        property color background: hostView.background
        property color accent: hostView.accent
        property var bar: barHelper.summary.current || ({})
        property string layout: bar.layout || "unified"
        property string barPosition: bar.edge || "top"
        property string appearance: bar.appearance || "solid"
        property string barScreens: bar.screens || "main"
        property string clockFormat: bar.clock || "12h"
        property string mediaStyle: bar.mediaStyle || "bars"
        property bool barAutoHide: bar.autohide === "yes"
        property bool barDock: bar.dock !== "no"
        property string workspaceStyle: workspaceHelper.summary.current
        function settingRequested(key, value) {
            barHelper.change(["set", key, value]);
        }
        function workspaceStyleRequested(value) {
            workspaceHelper.change([value]);
        }
    }
    SettingsHelper {
        id: barHelper
        objectName: "settings-bar-helper"
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/bar-settings.py")
        active: hostView.active && hostView.page === "bar"
        live: hostView.live
        schema: ({
                current: "object",
                choices: "object",
                available: "boolean"
            })
    }
    SettingsHelper {
        id: workspaceHelper
        objectName: "settings-workspace-helper"
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/workspace-style.py")
        active: hostView.active && hostView.page === "bar"
        live: hostView.live
    }
    SettingsHelper {
        id: fontHelper
        objectName: "settings-font-helper"
        script: Eitr.Paths.code("walker/scripts/actions/style/fonts.py")
        active: hostView.active && hostView.page === "appearance"
        live: hostView.live
    }
    SettingsAppearanceModel {
        id: themeModel
        objectName: "settings-theme-model"
        onApplied: hostView.refreshPage()
    }
    SettingsAppearanceModel {
        id: wallpaperModel
        objectName: "settings-wallpaper-model"
        onApplied: if (hostView.active && hostView.live)
            open("wallpaper", null)
    }
    onActiveChanged: if (active && live && page === "appearance") {
        themeModel.open("theme", null);
        wallpaperModel.open("wallpaper", null);
    }
    component Label: Text {
        color: hostView.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.WordWrap
        width: parent.width
    }
    property alias styleState: state
    property alias notificationState: notificationState
    property alias themeModel: themeModel
    property alias wallpaperModel: wallpaperModel
    property alias fontHelper: fontHelper
    property alias barHelper: barHelper
    property alias workspaceHelper: workspaceHelper
    Component { id: appearanceComponent; SettingsAppearancePage { context: hostView } }
    Component { id: barComponent; SettingsBarPage { context: hostView } }
    Component { id: windowsComponent; SettingsWindowsPage { context: hostView } }
    Component { id: lockscreenComponent; SettingsLockscreenPage { context: hostView } }
    Component { id: notificationsComponent; SettingsNotificationsPage { context: hostView } }
    Component { id: focusComponent; SettingsFocusPage { context: hostView } }
    Column {
        id: content
        width: hostView.width
        spacing: 18
        SettingsPageHeader { page: hostView.page; foreground: hostView.foreground }
        Loader {
            width: parent.width
            height: item ? item.implicitHeight : 0
            sourceComponent: ({"appearance": appearanceComponent, "bar": barComponent, "windows": windowsComponent, "lockscreen": lockscreenComponent, "notifications": notificationsComponent, "focus": focusComponent})[hostView.page] || null
        }
        Label {
            visible: state.actionError !== ""
            text: state.actionError
        }
        Label {
            visible: themeModel.error !== ""
            text: themeModel.error
        }
        Label {
            visible: wallpaperModel.error !== ""
            text: wallpaperModel.error
        }
        Label {
            visible: fontHelper.error !== ""
            text: fontHelper.error
        }
        Label {
            visible: barHelper.error !== ""
            text: barHelper.error
        }
        Label {
            visible: workspaceHelper.error !== ""
            text: workspaceHelper.error
        }
        Label {
            visible: Object.keys(state.styleErrors).length > 0
            text: Object.values(state.styleErrors).join("\n")
        }
        PanelButton {
            objectName: "settings-page-handbook"
            width: 160
            text: Eitr.I18n.tr("Learn more")
            foreground: hostView.foreground
            onClicked: if (hostView.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", hostView.page === "focus" ? "focus" : hostView.page === "bar" ? "desktop-bar" : hostView.page === "notifications" ? "control-center" : "appearance"])
        }
    }
}
