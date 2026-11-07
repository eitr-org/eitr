import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "SettingsIndex.js" as SettingsIndex

Rectangle {
    id: settings
    objectName: "settings-content"
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property bool live: true
    property var networkService: null
    property var notifications: null
    property bool idleEnabled: false
    signal idleToggleRequested()
    property string page: "system"
    property string tab: ""
    signal themesRequested()
    readonly property color gold: SettingsInk.gold
    readonly property var current: SettingsIndex.pages.find(entry => entry.id === page) || SettingsIndex.pages[0]
    property string query: ""
    readonly property var results: SettingsIndex.filter(query, Eitr.I18n.tr)
    signal closeRequested()
    Binding { target: SettingsInk; property: "background"; value: settings.background }
    color: Qt.rgba(background.r, background.g, background.b, 1)
    focus: opened
    Keys.onEscapePressed: {
        if (devicesPage.visible && devicesPage.dismiss()) return;
        if (systemPage.visible && systemPage.dismiss()) return;
        closeRequested();
    }
    function navigate(identifier) {
        const route = SettingsIndex.resolve(identifier);
        page = route.page;
        tab = route.tab;
        query = "";
    }
    FamilySidebar {
        id: sidebar
        width: Math.min(260, settings.width * 0.31)
        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.margins: PanelStyle.padding
        foreground: settings.foreground; background: settings.background; accent: settings.accent
        subtitle: Eitr.I18n.tr("Settings")
        placeholder: Eitr.I18n.tr("Search settings")
        query: settings.query
        emptyText: Eitr.I18n.tr("No matching settings")
        currentId: settings.page
        entries: settings.results.map(page => {
            const group = SettingsIndex.groupFor(page);
            return {id: page.id, title: Eitr.I18n.tr(page.title), rune: page.rune, group: Eitr.I18n.tr(group.name), groupRune: group.rune, destination: page.destinationId};
        })
        onChosen: entry => settings.navigate(entry.destination)
        onCloseRequested: settings.closeRequested()
        onSearchEdited: text => settings.query = text
        onSearchAccepted: if (settings.results.length) settings.navigate(settings.results[0].destinationId)
    }
    Rectangle { x: sidebar.x + sidebar.width + PanelStyle.padding; width: 1; height: parent.height; color: Qt.alpha(settings.foreground, PanelStyle.dividerAlpha) }
    Item {
        id: body
        anchors.left: sidebar.right; anchors.leftMargin: PanelStyle.padding * 2
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.margins: PanelStyle.padding
        SettingsOverview {
            objectName: "settings-overview"
            anchors.fill: parent
            visible: settings.page === "system"
            observing: settings.opened && visible && settings.live
            live: settings.live
            foreground: settings.foreground; background: settings.background; accent: settings.accent
            onPageRequested: page => settings.navigate(page)
        }
        SettingsDesktopHost {
            anchors.fill: parent
            visible: ["appearance", "bar", "windows", "lockscreen", "notifications", "focus"].includes(settings.page)
            page: settings.page; title: settings.current.title; tab: settings.tab
            onTabRequested: value => settings.tab = value
            active: settings.opened && visible
            live: settings.live
            notifications: settings.notifications; idleEnabled: settings.idleEnabled
            foreground: settings.foreground; background: settings.background; accent: settings.accent
            onThemesRequested: settings.themesRequested()
            onIdleToggleRequested: settings.idleToggleRequested()
        }
        SettingsDevicesPage {
            id: devicesPage
            anchors.fill: parent
            visible: ["displays", "sound", "connections", "input"].includes(settings.page)
            page: settings.page; title: settings.current.title; tab: settings.tab
            onTabRequested: value => settings.tab = value
            active: settings.opened && visible
            live: settings.live; networkService: settings.networkService
            foreground: settings.foreground; background: settings.background; accent: settings.accent
        }
        SettingsStreamingPage {
            anchors.fill: parent
            visible: settings.page === "streaming"
            active: settings.opened && visible
            live: settings.live
            foreground: settings.foreground; background: settings.background; accent: settings.accent
        }
        SettingsSystemHost {
            id: systemPage
            onPageRequested: page => settings.navigate(page)
            anchors.fill: parent
            visible: ["keybinds", "default-apps", "user", "git-cloud", "security", "assistant", "updates", "check-pc", "about"].includes(settings.page)
            page: settings.page; title: settings.current.title
            active: settings.opened && visible
            live: settings.live
            foreground: settings.foreground; background: settings.background; accent: settings.accent
        }
    }
}
