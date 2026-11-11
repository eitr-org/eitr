import ".."
pragma ComponentBehavior: Bound
import QtQuick

// What Drop's time pill shows around the time, which keeps the screen's centre. Before the
// time: a red dot while recording (the OBS page), a calendar mark when an event starts within
// ten minutes (today), a ring while a timer runs (the Timer page) and, next to the time, a
// note while music plays (the Media page). After it: a bell that slides out from behind the
// time when a notification arrives, rings twice, and slides back once its popup has gone
// (clicked meanwhile, it opens the Notifications page). Bell, mark and ring come from the
// bar's ClockActivityState; the flashes over the time are the clock's own. Dragging the note
// to the right turns the pill into one line of lyrics alone (no time, note or bell); dragging
// either way turns it back, and so does the player closing (pausing or a new song does not). The pill only makes room on a side that has
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
    readonly property var shared: barHost.clockActivity
    // Whether the bell is out; the pill eases to the room it needs (as for the dashboard)
    // and the glyphs ride its edge, so they move exactly with it.
    readonly property bool bellOut: shared.bellOut
    readonly property bool timing: shared.timing
    readonly property bool meetingSoon: shared.meetingSoon
    readonly property real leading: lyricsOpen ? 0 : ((playing ? 1 : 0) + (recording ? 1 : 0) + (timing ? 1 : 0) + (meetingSoon ? 1 : 0)) * slot
    // Lyrics across the pill, one line at a time, while opened by dragging the note right.
    property bool lyricsOpen: false
    // Pausing or changing song keeps them; only the player going away closes them (the media
    // strip's presence already bridges the gap between songs).
    readonly property bool present: !!(barHost.mediaStrip && barHost.mediaStrip.present)
    onPresentChanged: if (!present) lyricsOpen = false
    onVerticalChanged: if (vertical) lyricsOpen = false
    // The pill's length while it shows lyrics: the line's own width, within limits.
    readonly property real lyricsExtent: Math.max(120, Math.min(760, lyric.naturalWidth + 36))
    readonly property real trailing: bellOut && !lyricsOpen ? slot : 0
    readonly property real leadingSpace: leading > 0 ? leading + margin : 0
    readonly property real trailingSpace: trailing > 0 ? trailing + margin : 0
    // On a side edge "before" is above the time and "after" below it.
    readonly property bool vertical: host.verticalBar
    readonly property real along: vertical ? height : width
    readonly property real centre: along / 2 + timeOffset
    readonly property real timeHalf: (vertical ? barHost.verticalCalendarIcon.height : barHost.centerInfo.width) / 2
    // The room the pill has opened so far on each side of the time (4 px is its padding).
    readonly property real leadingRoom: Math.max(0, Math.min(leading, centre - timeHalf - 4 - margin))
    readonly property real trailingRoom: Math.max(0, Math.min(trailing, along - centre - timeHalf - 4 - margin))

    component Glyph: Text {
        id: glyph
        signal activated()
        width: activity.vertical ? activity.width : activity.slot; height: activity.vertical ? activity.slot : activity.height
        // Centred by its drawn shape: the note's ink sits off-centre in its font box, which
        // left it farther from the pill's end than the bell.
        TextMetrics { id: ink; font: glyph.font; text: glyph.text }
        horizontalAlignment: Text.AlignLeft; verticalAlignment: Text.AlignVCenter
        leftPadding: (width - ink.tightBoundingRect.width) / 2 - ink.tightBoundingRect.x
        color: activity.host.fg
        font.family: DesktopFonts.family; font.pixelSize: 14
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: parent.activated() }
    }

    // Each side is a window that opens from the time's edge; its glyphs ride its far edge,
    // so they slide out from behind the time and back in.
    Item {
        x: activity.vertical ? 0 : activity.centre - activity.timeHalf - width
        y: activity.vertical ? activity.centre - activity.timeHalf - height : 0
        width: activity.vertical ? parent.width : activity.leadingRoom
        height: activity.vertical ? activity.leadingRoom : parent.height
        clip: true
        Grid {
            columns: activity.vertical ? 1 : 4
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
                visible: activity.meetingSoon
                text: "󰃭"
                onActivated: activity.barHost.dropDashboard.showDay(new Date())
            }
            Item {
                visible: activity.timing
                width: activity.vertical ? activity.width : activity.slot; height: activity.vertical ? activity.slot : activity.height
                TimerRing { anchors.centerIn: parent; foreground: activity.host.fg }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: activity.barHost.dropDashboard.show("timer") }
            }
            // The note, next to the time. Dragging it right opens the lyrics; a plain click
            // opens the Media page.
            Glyph {
                visible: activity.playing
                text: "󰝚"
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    property real pressX: 0
                    property bool dragged: false
                    onPressed: mouse => { pressX = mouse.x; dragged = false; }
                    onPositionChanged: mouse => {
                        if (!pressed || dragged || activity.vertical || mouse.x - pressX < 16) return;
                        dragged = true;
                        activity.lyricsOpen = true;
                    }
                    onClicked: if (!dragged) activity.barHost.dropDashboard.show("media")
                }
            }
        }
    }
    // After the time: the bell, sliding out the same way.
    Item {
        x: activity.vertical ? 0 : activity.centre + activity.timeHalf
        y: activity.vertical ? activity.centre + activity.timeHalf : 0
        width: activity.vertical ? parent.width : activity.trailingRoom
        height: activity.vertical ? activity.trailingRoom : parent.height
        clip: true
        Glyph {
            id: bell
            // At the window's far end, which grows away from the time.
            x: activity.vertical ? 0 : parent.width - width
            y: activity.vertical ? parent.height - height : 0
            visible: activity.bellOut
            text: "󰂚"
            transformOrigin: Item.Top
            rotation: activity.shared.bellAngle
            onActivated: activity.barHost.dropDashboard.show("notifications")
        }
    }
    // The lyrics alone across the whole pill: each new line rises in as the last fades.
    // Dragging either way closes them; a click opens the Media page.
    Item {
        anchors.fill: parent
        visible: activity.lyricsOpen
        z: 2
        LyricLine {
            id: lyric
            anchors.centerIn: parent
            width: Math.max(0, parent.width - 24); height: parent.height
            host: activity.host; player: activity.player; active: activity.lyricsOpen
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
}
