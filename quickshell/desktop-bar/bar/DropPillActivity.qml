import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Hyprland

// What Drop's time pill shows around the time, which keeps the screen's centre: a bell
// that slides out from behind the time when a notification arrives, rings twice, and
// slides back once its popup has gone (clicked meanwhile, it opens the Notifications page); a red dot while recording
// (the OBS panel); a note after the time while music plays (the Media page); and, on
// changing workspace, the workspace's number rolling in over the time. The pill only makes
// room on a side that has something.
Item {
    id: activity
    required property var host
    required property var barHost
    // Where the time sits within the pill, relative to its middle.
    required property real timeOffset
    anchors.fill: parent
    readonly property var notifications: barHost.notificationsRef
    readonly property var obsState: barHost.obsMenu ? barHost.obsMenu.obsState : ({})
    readonly property bool recording: !!obsState.recording || !!obsState.streaming
    readonly property var player: barHost.mediaStrip ? barHost.mediaStrip.player : null
    readonly property bool playing: !!player && player.isPlaying
    readonly property real slot: 22
    // Room beyond the glyphs, so they keep clear of the pill's rounded ends.
    readonly property real margin: 6
    // Whether the bell is out; the pill eases to the room it needs (as for the dashboard)
    // and the glyphs ride its edge, so they move exactly with it.
    property bool bellOut: false
    readonly property real leading: ((bellOut ? 1 : 0) + (recording ? 1 : 0)) * slot
    readonly property real trailing: playing ? slot : 0
    readonly property real leadingSpace: leading > 0 ? leading + margin : 0
    readonly property real trailingSpace: trailing > 0 ? trailing + margin : 0
    readonly property real centre: width / 2 + timeOffset
    readonly property real timeHalf: barHost.centerInfo.width / 2
    // The room the pill has opened so far on each side of the time (4 px is its padding).
    readonly property real leadingRoom: Math.max(0, Math.min(leading, centre - timeHalf - 4 - margin))
    readonly property real trailingRoom: Math.max(0, Math.min(trailing, width - centre - timeHalf - 4 - margin))

    // A new popup brings the bell out to ring twice; it stays out while popups are on
    // screen and goes back behind the time when they have gone. Do Not Disturb keeps it in.
    property int popupCount: notifications ? notifications.popups.length : 0
    onPopupCountChanged: {
        if (popupCount > seenPopups && !notifications.doNotDisturb) ring.restart();
        else if (popupCount === 0 && !ring.running) bellOut = false;
        seenPopups = popupCount;
    }
    property int seenPopups: 0
    SequentialAnimation {
        id: ring
        PropertyAction { target: activity; property: "bellOut"; value: true }
        PauseAnimation { duration: DesktopStyle.motionDuration(320) }
        SequentialAnimation {
            loops: 2
            NumberAnimation { target: bell; property: "rotation"; to: 18; duration: 90 }
            NumberAnimation { target: bell; property: "rotation"; to: -16; duration: 140 }
            NumberAnimation { target: bell; property: "rotation"; to: 10; duration: 120 }
            NumberAnimation { target: bell; property: "rotation"; to: 0; duration: 110 }
            PauseAnimation { duration: 260 }
        }
        ScriptAction { script: if (activity.popupCount === 0) activity.bellOut = false }
    }

    // 0 shows the time, 1 the workspace number; it rises and falls back on a change.
    property real flash: 0
    property string workspaceNumber: ""
    readonly property var monitor: barHost.screen ? Hyprland.monitorFor(barHost.screen) : null
    readonly property int workspaceId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : 0
    property int seenWorkspace: 0
    onWorkspaceIdChanged: {
        if (seenWorkspace !== 0 && workspaceId > 0 && workspaceId !== seenWorkspace) {
            const entry = host.workspaceRows(barHost.screen).find(row => row.id === workspaceId);
            workspaceNumber = String(entry ? entry.number : workspaceId);
            showWorkspace.restart();
        }
        if (workspaceId > 0) seenWorkspace = workspaceId;
    }
    SequentialAnimation {
        id: showWorkspace
        NumberAnimation { target: activity; property: "flash"; to: 1; duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutBack }
        PauseAnimation { duration: 900 }
        NumberAnimation { target: activity; property: "flash"; to: 0; duration: DesktopStyle.motionDuration(260); easing.type: Easing.InCubic }
    }

    component Glyph: Text {
        signal activated()
        width: activity.slot; height: parent ? parent.height : 0
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        color: activity.host.fg
        font.family: DesktopFonts.family; font.pixelSize: 14
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: parent.activated() }
    }

    // Each side is a window that opens from the time's edge; its glyphs ride its far edge,
    // so they slide out from behind the time and back in.
    Item {
        x: activity.centre - activity.timeHalf - width; width: activity.leadingRoom
        height: parent.height
        clip: true
        Row {
            x: 0
            height: parent.height
            Glyph {
                visible: activity.recording
                text: "●"; color: activity.obsState.paused && !activity.obsState.streaming ? activity.host.fg : "#e05c68"
                font.pixelSize: 10
                onActivated: activity.barHost.togglePanel(activity.barHost.obsMenu)
                SequentialAnimation on opacity {
                    running: activity.recording && !DesktopStyle.reduceMotion; loops: Animation.Infinite
                    NumberAnimation { to: 0.35; duration: 700; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1; duration: 700; easing.type: Easing.InOutSine }
                }
            }
            Glyph {
                id: bell
                visible: activity.bellOut
                text: "󰂚"
                transformOrigin: Item.Top
                onActivated: activity.barHost.dropDashboard.show("notifications")
            }
        }
    }
    // After the time: the note, sliding out the same way.
    Item {
        x: activity.centre + activity.timeHalf; width: activity.trailingRoom
        height: parent.height
        clip: true
        Glyph {
            anchors.right: parent.right
            visible: activity.playing
            text: "󰝚"
            onActivated: activity.barHost.dropDashboard.show("media")
        }
    }

    // The workspace number over the time: it rises in from below as the time fades.
    Text {
        x: activity.centre - width / 2
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: (1 - activity.flash) * 12
        visible: activity.flash > 0.01
        opacity: Math.min(1, activity.flash)
        scale: 0.7 + 0.3 * Math.min(1, activity.flash)
        text: activity.workspaceNumber
        color: activity.host.activeBg
        font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.Bold
    }
}
