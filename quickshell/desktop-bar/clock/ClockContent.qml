import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Shared Settings-family layout for Clock: sidebar on the left and active page on the right.
Rectangle {
    id: content
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property string page: "timers"
    property string clockFormat: "24h"
    property bool live: true
    signal closeRequested()
    signal storeRequested(string kind, string tab)

    readonly property var pages: [
        {id: "timers", title: Eitr.I18n.tr("Timers"), rune: "ᛉ", group: Eitr.I18n.tr("Clock"), groupRune: "ᛞ"},
        {id: "stopwatch", title: Eitr.I18n.tr("Stopwatch"), rune: "ᛏ", group: Eitr.I18n.tr("Clock"), groupRune: "ᛞ"},
        {id: "focus", title: Eitr.I18n.tr("Focus"), rune: "ᚠ", group: Eitr.I18n.tr("Clock"), groupRune: "ᛞ"},
        {id: "world", title: Eitr.I18n.tr("World"), rune: "ᛟ", group: Eitr.I18n.tr("Clock"), groupRune: "ᛞ"}
    ]

    Binding { target: SettingsInk; property: "background"; value: content.background }
    color: Qt.rgba(background.r, background.g, background.b, 1)
    focus: opened

    Keys.onEscapePressed: closeRequested()

    FamilySidebar {
        id: sidebar
        objectName: "clock-sidebar"
        width: Math.min(260, content.width * 0.31)
        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.margins: PanelStyle.padding
        foreground: content.foreground; background: content.background; accent: content.accent
        subtitle: Eitr.I18n.tr("Clock")
        searchVisible: false
        currentId: content.page
        entries: content.pages
        onChosen: function(entry) { content.page = entry.id; }
        onCloseRequested: content.closeRequested()
    }

    Rectangle {
        x: sidebar.x + sidebar.width + PanelStyle.padding
        width: 1
        height: parent.height
        color: Qt.alpha(content.foreground, PanelStyle.dividerAlpha)
    }

    Item {
        id: body
        anchors.left: sidebar.right; anchors.leftMargin: PanelStyle.padding * 2
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.margins: PanelStyle.padding

        TimersPage {
            anchors.fill: parent
            foreground: content.foreground
            background: content.background
            accent: content.accent
            visible: content.page === "timers"
            opacity: visible ? 1 : 0
            Behavior on opacity {
                enabled: !DesktopStyle.reduceMotion
                NumberAnimation { duration: DesktopStyle.motionDuration(120) }
            }
        }

        StopwatchPage {
            anchors.fill: parent
            foreground: content.foreground
            background: content.background
            accent: content.accent
            visible: content.page === "stopwatch"
            opacity: visible ? 1 : 0
            Behavior on opacity {
                enabled: !DesktopStyle.reduceMotion
                NumberAnimation { duration: DesktopStyle.motionDuration(120) }
            }
        }

        FocusPage {
            anchors.fill: parent
            foreground: content.foreground
            background: content.background
            accent: content.accent
            visible: content.page === "focus"
            opacity: visible ? 1 : 0
            Behavior on opacity {
                enabled: !DesktopStyle.reduceMotion
                NumberAnimation { duration: DesktopStyle.motionDuration(120) }
            }
        }

        WorldPage {
            anchors.fill: parent
            foreground: content.foreground
            background: content.background
            accent: content.accent
            clockFormat: content.clockFormat
            active: content.opened && content.page === "world"
            live: content.live
            visible: content.page === "world"
            opacity: visible ? 1 : 0
            onStoreRequested: function(kind, tab) { content.storeRequested(kind, tab); }
            Behavior on opacity {
                enabled: !DesktopStyle.reduceMotion
                NumberAnimation { duration: DesktopStyle.motionDuration(120) }
            }
        }
    }
}
