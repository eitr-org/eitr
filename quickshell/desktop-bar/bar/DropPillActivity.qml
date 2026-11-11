import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Hyprland

// What Drop's time pill shows around the time, which stays exactly centred: a bell that
// rings on the left while a notification is up (it opens the Notifications page), a red
// dot while recording (the OBS panel), a note on the right while music plays (the Media
// page), and, on changing workspace, the workspace's number rolling in over the time.
Item {
    id: activity
    required property var host
    required property var barHost
    anchors.fill: parent
    readonly property var notifications: barHost.notificationsRef
    readonly property bool ringing: !!notifications && notifications.popups.length > 0 && !notifications.doNotDisturb
    readonly property var obsState: barHost.obsMenu ? barHost.obsMenu.obsState : ({})
    readonly property bool recording: !!obsState.recording || !!obsState.streaming
    readonly property var player: barHost.mediaStrip ? barHost.mediaStrip.player : null
    readonly property bool playing: !!player && player.isPlaying
    readonly property real slot: 22
    readonly property real leading: (ringing ? slot : 0) + (recording ? slot : 0)
    readonly property real trailing: playing ? slot : 0
    // The space each side of the time, the same on both so the time keeps the centre.
    readonly property real side: Math.max(leading, trailing)
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

    Row {
        anchors.right: parent.horizontalCenter; anchors.rightMargin: activity.barHost.centerInfo.width / 2 + 2
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
            visible: activity.ringing
            text: "󰂚"
            onActivated: activity.barHost.dropDashboard.show("notifications")
            transformOrigin: Item.Top
            SequentialAnimation on rotation {
                running: activity.ringing && !DesktopStyle.reduceMotion; loops: Animation.Infinite
                NumberAnimation { to: 18; duration: 90 }
                NumberAnimation { to: -16; duration: 140 }
                NumberAnimation { to: 12; duration: 120 }
                NumberAnimation { to: -8; duration: 110 }
                NumberAnimation { to: 0; duration: 100 }
                PauseAnimation { duration: 900 }
            }
        }
    }
    Glyph {
        x: parent.width / 2 + activity.barHost.centerInfo.width / 2 + 2
        visible: activity.playing
        text: "󰝚"; color: activity.host.activeBg
        onActivated: activity.barHost.dropDashboard.show("media")
    }

    // The workspace number over the time: it rises in from below as the time fades.
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: (1 - activity.flash) * 12
        visible: activity.flash > 0.01
        opacity: Math.min(1, activity.flash)
        scale: 0.7 + 0.3 * Math.min(1, activity.flash)
        text: activity.workspaceNumber
        color: activity.host.activeBg
        font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.Bold
    }
}
