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
    // 0 hidden behind the time, 1 fully out; the bell's appearance drives the pill's growth.
    property real bellOut: 0
    property real noteOut: playing ? 1 : 0
    Behavior on noteOut { NumberAnimation { duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutCubic } }
    property real dotOut: recording ? 1 : 0
    Behavior on dotOut { NumberAnimation { duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutCubic } }
    readonly property real leading: (bellOut + dotOut) * slot
    readonly property real trailing: noteOut * slot
    readonly property real leadingSpace: leading + Math.min(1, bellOut + dotOut) * margin
    readonly property real trailingSpace: trailing + noteOut * margin
    readonly property real centre: width / 2 + timeOffset
    readonly property real timeHalf: barHost.centerInfo.width / 2

    // A new popup brings the bell out to ring twice; it stays out while popups are on
    // screen and goes back behind the time when they have gone. Do Not Disturb keeps it in.
    property int popupCount: notifications ? notifications.popups.length : 0
    onPopupCountChanged: {
        if (popupCount > seenPopups && !notifications.doNotDisturb) { hideBell.stop(); ring.restart(); }
        else if (popupCount === 0 && !ring.running) hideBell.restart();
        seenPopups = popupCount;
    }
    property int seenPopups: 0
    SequentialAnimation {
        id: ring
        NumberAnimation { target: activity; property: "bellOut"; to: 1; duration: DesktopStyle.motionDuration(280); easing.type: Easing.OutBack }
        SequentialAnimation {
            loops: 2
            NumberAnimation { target: bell; property: "rotation"; to: 18; duration: 90 }
            NumberAnimation { target: bell; property: "rotation"; to: -16; duration: 140 }
            NumberAnimation { target: bell; property: "rotation"; to: 10; duration: 120 }
            NumberAnimation { target: bell; property: "rotation"; to: 0; duration: 110 }
            PauseAnimation { duration: 260 }
        }
        ScriptAction { script: if (activity.popupCount === 0) hideBell.restart() }
    }
    NumberAnimation { id: hideBell; target: activity; property: "bellOut"; to: 0; duration: DesktopStyle.motionDuration(280); easing.type: Easing.InCubic }

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
        x: activity.centre - activity.timeHalf - width; width: activity.leading
        height: parent.height
        clip: true
        Row {
            x: 0
            height: parent.height
            Glyph {
                visible: activity.dotOut > 0
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
                visible: activity.bellOut > 0
                text: "󰂚"
                transformOrigin: Item.Top
                onActivated: activity.barHost.dropDashboard.show("notifications")
            }
        }
    }
    // After the time: the note, sliding out the same way.
    Item {
        x: activity.centre + activity.timeHalf; width: activity.trailing
        height: parent.height
        clip: true
        Glyph {
            anchors.right: parent.right
            visible: activity.noteOut > 0
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
