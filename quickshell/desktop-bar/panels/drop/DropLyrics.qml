import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import "../../PanelStyle.js" as PanelStyle

// Lyrics the player sends in its track metadata (xesam:asText). Timed LRC lines
// ("[01:23.45] text") follow the song, the current one large and centred; untimed
// lyrics scroll as plain text.
Item {
    id: lyrics
    required property string text
    required property real position
    required property color foreground
    required property color accent
    readonly property var lines: parse(text)
    readonly property bool timed: lines.length > 0 && lines[0].time >= 0
    readonly property int current: {
        if (!timed) return -1;
        let found = 0;
        for (let index = 0; index < lines.length; index++) if (lines[index].time <= position) found = index;
        return found;
    }
    readonly property bool available: lines.length > 0
    clip: true

    function parse(source) {
        const timedLines = [];
        const plain = [];
        String(source || "").split(/\r?\n/).forEach(line => {
            const stamp = /\[(\d+):(\d+(?:\.\d+)?)\]/g;
            const words = line.replace(/\[[^\]]*\]/g, "").trim();
            let match, timedHere = false;
            while ((match = stamp.exec(line)) !== null) {
                timedLines.push({time: Number(match[1]) * 60 + Number(match[2]), text: words});
                timedHere = true;
            }
            if (timedHere) return;
            if (words !== "") plain.push({time: -1, text: words});
        });
        return timedLines.length ? timedLines.sort((first, second) => first.time - second.time) : plain;
    }

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
