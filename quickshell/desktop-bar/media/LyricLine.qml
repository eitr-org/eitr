import ".."
import QtQuick
import "Lyrics.js" as Lyrics

// One line of lyrics on the bar (Drop's pill, the media wave): the line being sung, each new
// one rising in as the last fades. It follows the player's position while active; without
// timed lyrics it shows the song itself.
Item {
    id: lyric
    required property var host
    required property var player
    required property bool active
    property color foreground: host.fg
    LyricsSource { id: source; host: lyric.host; player: lyric.player; active: lyric.active }
    property real position: 0
    Timer {
        interval: 250; repeat: true; triggeredOnStart: true
        running: lyric.active && !!lyric.player
        onTriggered: lyric.position = lyric.player.position
    }
    readonly property var lines: Lyrics.parse(source.text)
    readonly property int index: Lyrics.current(lines, position)
    readonly property string line: index >= 0 ? (lines[index].text || "♪")
        : source.state === "loading" ? "…"
        : player ? [player.trackTitle, player.trackArtist].filter(Boolean).join(" · ") : ""
    // The line's own width, for a surface that sizes itself to it.
    readonly property real naturalWidth: metrics.advanceWidth
    TextMetrics { id: metrics; text: lyric.line; font: label.font }
    Text {
        id: label
        anchors.centerIn: parent
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        text: lyric.line
        color: lyric.foreground; elide: Text.ElideRight; textFormat: Text.PlainText
        font.family: DesktopFonts.family; font.pixelSize: 13
        onTextChanged: if (lyric.visible && !DesktopStyle.reduceMotion) nextLine.restart()
        NumberAnimation { id: nextLine; target: label; property: "opacity"; from: 0; to: 1; duration: 240 }
        transform: Translate { y: (1 - label.opacity) * 6 }
    }
}
