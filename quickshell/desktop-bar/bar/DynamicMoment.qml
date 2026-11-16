import ".."
import QtQuick
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
    // Hover suppresses the moment, but a click aimed at its preview still opens it.
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
                color: moment.host.fg
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
            color: moment.host.fg
            font.family: DesktopFonts.family; font.pixelSize: moment.vertical ? PanelStyle.captionSize : PanelStyle.bodySize
        }
        Rectangle {
            visible: content.level
            x: moment.vertical ? (parent.width - 4) / 2 : 48
            y: moment.vertical ? 62 : (parent.height - height) / 2
            width: moment.vertical ? 4 : Math.max(0, parent.width - 110)
            height: moment.vertical ? Math.max(0, parent.height - 72) : 3
            radius: 2; color: Qt.alpha(moment.host.fg, 0.2)
            Rectangle {
                readonly property real fraction: content.entry ? Math.min(1, content.entry.level / 100) : 0
                width: moment.vertical ? parent.width : parent.width * fraction
                height: moment.vertical ? parent.height * fraction : parent.height
                radius: 2; color: moment.host.fg
            }
        }
    }
    Content { entry: moment.previous; opacity: moment.previous ? 1 - moment.mix : 0 }
    Content { entry: moment.shown; opacity: moment.mix }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: moment.activated(moment.shown) }
}
