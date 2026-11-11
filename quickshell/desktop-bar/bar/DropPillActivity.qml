import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Hyprland
import "../panels/drop/Lyrics.js" as Lyrics

// What Drop's time pill shows around the time, which keeps the screen's centre: a bell
// that slides out from behind the time when a notification arrives, rings twice, and
// slides back once its popup has gone (clicked meanwhile, it opens the Notifications page); a red dot while recording
// (the OBS page); a note after the time while music plays (the Media page); and, on
// changing workspace, the workspace's number rolling in over the time. Dragging the note to
// the left turns the pill into one line of lyrics alone (no time, note or bell); dragging
// either way, pausing or stopping turns it back. The pill only makes room on a side that has
// something.
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
    readonly property real leading: lyricsOpen ? 0 : ((bellOut ? 1 : 0) + (recording ? 1 : 0)) * slot
    // Lyrics after the time, one line at a time, while opened by dragging the note right.
    property bool lyricsOpen: false
    onPlayingChanged: if (!playing) lyricsOpen = false
    // The pill's length while it shows lyrics: the line's own width, within limits.
    readonly property real lyricsExtent: Math.max(120, Math.min(380, lineMetrics.advanceWidth + 36))
    TextMetrics { id: lineMetrics; text: activity.line; font.family: DesktopFonts.family; font.pixelSize: 13 }
    DropLyricsSource { id: lyricsSource; player: activity.player; active: activity.lyricsOpen }
    property real position: 0
    Timer {
        interval: 250; repeat: true; triggeredOnStart: true
        running: activity.lyricsOpen && !!activity.player
        onTriggered: activity.position = activity.player.position
    }
    readonly property var lines: Lyrics.parse(lyricsSource.text)
    readonly property int lineIndex: Lyrics.current(lines, position)
    // The sung line; without timed lyrics, the song itself.
    readonly property string line: lineIndex >= 0 ? (lines[lineIndex].text || "♪")
        : lyricsSource.state === "loading" ? "…"
        : player ? [player.trackTitle, player.trackArtist].filter(Boolean).join(" · ") : ""
    readonly property real trailing: playing && !lyricsOpen ? slot : 0
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
        // Long enough for a hidden bar to drop in and the pill to open before it rings.
        PauseAnimation { duration: DesktopStyle.motionDuration(activity.host.barAutoHide ? 640 : 320) }
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
                onActivated: activity.barHost.dropDashboard.show("obs")
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
    // After the time: the note, sliding out the same way. Dragging it left opens the
    // lyrics; a plain click opens the Media page.
    Item {
        x: activity.centre + activity.timeHalf; width: activity.trailingRoom
        height: parent.height
        clip: true
        Glyph {
            anchors.right: parent.right
            visible: activity.playing
            text: "󰝚"
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            property real pressX: 0
            property bool dragged: false
            onPressed: mouse => { pressX = mouse.x; dragged = false; }
            onPositionChanged: mouse => {
                if (!pressed || dragged || pressX - mouse.x < 16) return;
                dragged = true;
                activity.lyricsOpen = true;
            }
            onClicked: if (!dragged) activity.barHost.dropDashboard.show("media")
        }
    }

    // The lyrics alone across the whole pill: each new line rises in as the last fades.
    // Dragging either way closes them; a click opens the Media page.
    Item {
        anchors.fill: parent
        visible: activity.lyricsOpen
        z: 2
        Text {
            id: lyricLine
            anchors.centerIn: parent
            width: Math.max(0, parent.width - 24)
            horizontalAlignment: Text.AlignHCenter
            text: activity.line
            color: activity.host.fg; elide: Text.ElideRight; textFormat: Text.PlainText
            font.family: DesktopFonts.family; font.pixelSize: 13
            onTextChanged: if (visible && !DesktopStyle.reduceMotion) nextLine.restart()
            NumberAnimation { id: nextLine; target: lyricLine; property: "opacity"; from: 0; to: 1; duration: 240 }
            transform: Translate { y: (1 - lyricLine.opacity) * 6 }
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            property real pressX: 0
            property bool dragged: false
            onPressed: mouse => { pressX = mouse.x; dragged = false; }
            onPositionChanged: mouse => {
                if (!pressed || dragged || Math.abs(mouse.x - pressX) < 16) return;
                dragged = true;
                activity.lyricsOpen = false;
            }
            onClicked: if (!dragged) activity.barHost.dropDashboard.show("media")
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
        color: activity.host.fg
        font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.Bold
    }
}
