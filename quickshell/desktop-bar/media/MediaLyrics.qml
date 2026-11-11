import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle
import "Lyrics.js" as Lyrics

// Lyrics text (from the player or LRCLIB, see LyricsSource). Timed LRC lines
// ("[01:23.45] text") follow the song, the current one large and centred; untimed
// lyrics scroll as plain text.
Item {
    id: lyrics
    required property string text
    required property real position
    required property color foreground
    required property color accent
    readonly property var lines: Lyrics.parse(text)
    readonly property bool timed: lines.length > 0 && lines[0].time >= 0
    readonly property int current: Lyrics.current(lines, position)
    readonly property bool available: lines.length > 0
    clip: true

    ListView {
        id: view
        anchors.fill: parent
        model: lyrics.lines
        spacing: 6
        interactive: !lyrics.timed
        boundsBehavior: Flickable.StopAtBounds
        currentIndex: lyrics.current
        highlightFollowsCurrentItem: true
        preferredHighlightBegin: height / 2 - 14
        preferredHighlightEnd: height / 2 + 14
        highlightRangeMode: lyrics.timed ? ListView.StrictlyEnforceRange : ListView.NoHighlightRange
        highlightMoveDuration: DesktopStyle.motionDuration(400)
        delegate: Text {
            required property var modelData
            required property int index
            readonly property bool now: index === lyrics.current
            width: view.width
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap; textFormat: Text.PlainText
            text: modelData.text || "♪"
            color: now ? lyrics.accent : lyrics.foreground
            opacity: !lyrics.timed || now ? 1 : Math.max(0.25, 0.7 - Math.abs(index - lyrics.current) * 0.15)
            font.family: DesktopFonts.family; font.pixelSize: now ? 16 : PanelStyle.bodySize
            font.weight: now ? Font.Bold : Font.Normal
            Behavior on font.pixelSize { NumberAnimation { duration: DesktopStyle.motionDuration(200) } }
        }
    }
}
