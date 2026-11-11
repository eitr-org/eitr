import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Drop's dashboard, opened by clicking its time pill: a row of pages dragged sideways
// (dragging right goes forward, left goes back, both wrapping). It opens on Calendar and
// weather, then Media (skipped while nothing plays), quick controls, Performance, AI Usage and
// Notifications. Arrow keys and horizontal scrolling switch pages too.
ThemedPopup {
    id: dashboard
    required property var barHost
    required property var player
    property bool hold: false
    centered: true
    implicitWidth: 580
    implicitHeight: content.implicitHeight + verticalContentInset
    property date now: new Date()
    Timer { interval: 1000; running: dashboard.opened; repeat: true; triggeredOnStart: true; onTriggered: dashboard.now = new Date() }

    readonly property var pages: ["home", dashboard.player ? "media" : "", "controls", "performance", "ai", "notifications"].filter(Boolean)
    property string page: "home"
    readonly property int index: Math.max(0, pages.indexOf(page))
    // The slide: the current page sits at `shift`; the page it is leaving, or the one peeking
    // in during a drag, sits one page further on `otherSide` (-1 left, 1 right).
    property real shift: 0
    property string otherPage: ""
    property int otherSide: 1
    readonly property real span: content.width + 24
    // The page the next opening starts on (the pill's bell and note pick theirs).
    property string startPage: "home"
    function show(target) {
        startPage = pages.indexOf(target) >= 0 ? target : "home";
        if (opened) { go(startPage, 1); startPage = "home"; }
        else barHost.showPanel(dashboard);
    }
    onOpenedChanged: if (opened) { page = startPage; startPage = "home"; otherPage = ""; slide.stop(); shift = 0; home.monthOffset = 0; home.selectedDay = null; home.weatherOpen = false; }
    onPagesChanged: if (pages.indexOf(page) < 0) page = "home"

    function neighbour(direction) {
        return pages[(index + direction + pages.length) % pages.length];
    }
    // Forward (1) brings the next page in from the left, as a drag to the right does.
    function go(target, direction) {
        if (target === page || pages.length < 2) return;
        const side = direction > 0 ? -1 : 1;
        otherPage = page;
        page = target;
        shift = shift + side * span;
        otherSide = -side;
        slide.restart();
    }
    function step(direction) { go(neighbour(direction), direction); }
    NumberAnimation { id: slide; target: dashboard; property: "shift"; to: 0; duration: DesktopStyle.motionDuration(280); easing.type: Easing.OutCubic }

    Column {
        id: content
        width: parent.width
        spacing: 12
        focus: true
        Keys.onLeftPressed: dashboard.step(-1)
        Keys.onRightPressed: dashboard.step(1)

        Item {
            id: viewport
            width: parent.width
            clip: true
            readonly property Item current: ({home: home, media: media, controls: controls, performance: performance, ai: ai, notifications: notifications})[dashboard.page] || home
            height: current.implicitHeight
            Behavior on height { NumberAnimation { duration: DesktopStyle.motionDuration(240); easing.type: Easing.OutCubic } }
            function place(id) {
                return id === dashboard.page ? dashboard.shift : dashboard.shift + dashboard.otherSide * dashboard.span;
            }
            function shown(id) {
                return id === dashboard.page || (id === dashboard.otherPage && (slide.running || drag.active));
            }

            DropHomePage {
                id: home
                x: viewport.place("home"); visible: viewport.shown("home")
                width: viewport.width
                barHost: dashboard.barHost; now: dashboard.now
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            DropMediaPage {
                id: media
                x: viewport.place("media"); visible: viewport.shown("media")
                width: viewport.width
                player: dashboard.player
                active: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            DropControlsPage {
                id: controls
                x: viewport.place("controls"); visible: viewport.shown("controls")
                width: viewport.width
                barHost: dashboard.barHost
                watching: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent; background: dashboard.background
            }
            DropPerformancePage {
                id: performance
                x: viewport.place("performance"); visible: viewport.shown("performance")
                width: viewport.width
                watching: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent
            }

            DropAiPage {
                id: ai
                x: viewport.place("ai"); visible: viewport.shown("ai")
                width: viewport.width
                barHost: dashboard.barHost
                watching: dashboard.opened && visible
                foreground: dashboard.foreground; accent: dashboard.accent
            }
            // The notification center's own list, with its Do Not Disturb and Clear buttons.
            NotificationList {
                id: notifications
                x: viewport.place("notifications"); visible: viewport.shown("notifications")
                width: viewport.width; height: service.count === 0 ? 150 : 380; implicitHeight: height
                service: dashboard.barHost.notificationsRef
                foreground: dashboard.foreground; background: dashboard.background; accent: dashboard.accent
                onActivated: dashboard.opened = false
                // Reading here counts as the notification center being open.
                readonly property bool reading: dashboard.opened && dashboard.page === "notifications"
                onReadingChanged: service.centerOpen = reading
            }
            // Dragging sideways anywhere on a page moves it; a short drag springs back.
            DragHandler {
                id: drag
                target: null
                xAxis.enabled: true; yAxis.enabled: false
                cursorShape: Qt.ClosedHandCursor
                onTranslationChanged: {
                    if (!active) return;
                    slide.stop();
                    dashboard.shift = translation.x;
                    dashboard.otherSide = translation.x > 0 ? -1 : 1;
                    dashboard.otherPage = dashboard.neighbour(translation.x > 0 ? 1 : -1);
                }
                onActiveChanged: {
                    if (active) return;
                    if (Math.abs(dashboard.shift) > Math.min(90, viewport.width / 5)) dashboard.step(dashboard.shift > 0 ? 1 : -1);
                    else slide.restart();
                }
            }
            WheelHandler {
                orientation: Qt.Horizontal
                property real gathered: 0
                onWheel: function(event) {
                    gathered += event.angleDelta.x;
                    if (Math.abs(gathered) < 120 || slide.running) return;
                    dashboard.step(gathered < 0 ? 1 : -1);
                    gathered = 0;
                }
            }
        }
    }
}
