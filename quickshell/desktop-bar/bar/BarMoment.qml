import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Pipewire
import "../PanelStyle.js" as PanelStyle

// Immutable payloads let the old and new contents cross-fade during replacement.
Item {
    id: moment
    required property var host
    property var payload: null
    property var previous: null
    property var shown: null
    property real mix: 1
    readonly property bool vertical: host.verticalBar
    readonly property bool level: !!payload && (payload.kind === "volume" || payload.kind === "brightness")
    readonly property real naturalExtent: vertical ? (level ? 92 : 40)
        : level ? 208 : Math.min(320, metrics.width + 68)
    // Retain a notification click aimed at a fading preview.
    property bool retainAction: false
    property bool actionArmed: false
    onRetainActionChanged: if (!retainAction) actionArmed = false
    signal activated(var entry)
    TextMetrics { id: metrics; text: moment.payload ? moment.payload.text || "" : ""; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
    function armAction() { actionArmed = !payload && retainAction && shown && shown.kind === "notification"; }
    onPayloadChanged: {
        if (!payload) {
            Qt.callLater(armAction);
            return;
        }
        actionArmed = false;
        // A new level of the same kind updates in place: a cross-fade between two nearly equal
        // moments dims them halfway, so each volume step would blink.
        if (shown && shown.kind === payload.kind && (payload.kind === "volume" || payload.kind === "brightness")) {
            if (previous && previous.kind === payload.kind) previous = null;
            shown = payload;
            return;
        }
        previous = shown; shown = payload;
        fade.stop(); mix = DesktopStyle.reduceMotion ? 1 : 0; fade.start();
    }
    NumberAnimation { id: fade; target: moment; property: "mix"; to: 1; duration: DesktopStyle.motionDuration(120); onFinished: moment.previous = null }
    clip: true
    opacity: payload ? 1 : 0
    enabled: !!payload || (retainAction && actionArmed)
    Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
    component Content: Item {
        id: content
        property var entry: null
        readonly property bool level: !!entry && (entry.kind === "volume" || entry.kind === "brightness")
        anchors.fill: parent
        Item {
            id: iconBox
            width: 28; height: 24
            x: moment.vertical ? (parent.width - width) / 2 : 12
            y: moment.vertical ? 6 : (parent.height - height) / 2
            Image {
                id: image
                anchors.fill: parent
                source: content.entry ? content.entry.image || "" : ""
                sourceSize: Qt.size(160, 120)
                fillMode: Image.PreserveAspectFit
                cache: true
            }
            Text {
                anchors.centerIn: parent
                visible: image.status !== Image.Ready
                text: content.entry ? content.entry.icon || "" : ""
                color: moment.host.barFg
                font.family: DesktopFonts.family; font.pixelSize: 16
            }
        }
        Text {
            x: moment.vertical ? 0 : 46
            y: moment.vertical ? 34 : 0
            width: moment.vertical ? parent.width : Math.max(0, parent.width - x - 14)
            height: moment.vertical ? 22 : parent.height
            visible: !moment.vertical || content.level
            text: content.entry ? (content.level ? content.entry.level + "%" : content.entry.text || "") : ""
            horizontalAlignment: content.level ? Text.AlignRight : Text.AlignLeft
            rightPadding: 0
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight; textFormat: Text.PlainText
            color: moment.host.barFg
            font.family: DesktopFonts.family; font.pixelSize: moment.vertical ? PanelStyle.captionSize : PanelStyle.bodySize
        }
        Rectangle {
            visible: content.level
            x: moment.vertical ? (parent.width - 4) / 2 : 48
            y: moment.vertical ? 62 : (parent.height - height) / 2
            width: moment.vertical ? 4 : Math.max(0, parent.width - 110)
            height: moment.vertical ? Math.max(0, parent.height - 72) : 3
            radius: 2; color: Qt.alpha(moment.host.barFg, 0.2)
            Rectangle {
                readonly property real fraction: content.entry ? Math.min(1, content.entry.level / 100) : 0
                width: moment.vertical ? parent.width : parent.width * fraction
                height: moment.vertical ? parent.height * fraction : parent.height
                radius: 2; color: moment.host.barFg
                // Steps slide to the new level instead of jumping.
                Behavior on width { enabled: !moment.vertical; NumberAnimation { duration: DesktopStyle.motionDuration(90); easing.type: Easing.OutCubic } }
                Behavior on height { enabled: moment.vertical; NumberAnimation { duration: DesktopStyle.motionDuration(90); easing.type: Easing.OutCubic } }
            }
        }
    }
    Content { entry: moment.previous; opacity: moment.previous ? 1 - moment.mix : 0 }
    Content { entry: moment.shown; opacity: moment.mix }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: moment.activated(moment.shown) }
    // A volume or brightness moment is a control while it shows: scroll over it, or click
    // and drag along its bar. Hovering holds the moment, and each change renews it.
    readonly property bool adjustable: !!shown && !!payload && (shown.kind === "volume" || shown.kind === "brightness")
    readonly property var sink: Pipewire.defaultAudioSink
    function setLevel(value) {
        const target = Math.round(Math.max(0, Math.min(100, value)));
        if (!shown || target === shown.level) return;
        if (shown.kind === "volume") {
            if (sink && sink.audio) { sink.audio.muted = false; sink.audio.volume = target / 100; }
        } else {
            pendingBrightness = target;
            if (!brightnessWrite.running) writeBrightness();
        }
    }
    property int pendingBrightness: -1
    function writeBrightness() {
        if (pendingBrightness < 0) return;
        brightnessWrite.command = ["bash", Quickshell.shellDir + "/scripts/level-key.sh", "brightness", "set", String(Math.max(1, pendingBrightness))];
        pendingBrightness = -1;
        brightnessWrite.running = true;
    }
    // One write at a time; a drag keeps only the latest level while one runs.
    Process { id: brightnessWrite; onExited: moment.writeBrightness() }
    WheelHandler {
        enabled: moment.adjustable
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: event => moment.setLevel(moment.shown.level + (event.angleDelta.y + event.angleDelta.x > 0 ? 5 : -5))
    }
    MouseArea {
        id: track
        enabled: moment.adjustable
        visible: enabled
        // The level bar, a little taller than it looks so it is easy to grab.
        x: moment.vertical ? 0 : 40
        y: moment.vertical ? 56 : 0
        width: moment.vertical ? parent.width : Math.max(0, parent.width - 96)
        height: moment.vertical ? Math.max(0, parent.height - 60) : parent.height
        cursorShape: Qt.PointingHandCursor
        preventStealing: true
        function levelAt(mouse) {
            return moment.vertical ? (mouse.y - 6) / Math.max(1, height - 12) * 100
                : (mouse.x - 8) / Math.max(1, width - 16) * 100;
        }
        onPressed: mouse => moment.setLevel(levelAt(mouse))
        onPositionChanged: mouse => { if (pressed) moment.setLevel(levelAt(mouse)); }
    }
}
