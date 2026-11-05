import ".."
import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// A screenshot set on a background with padding, rounded corners and a shadow, ready to
// share. The composition is built at full size and shown scaled to fit; Copy and Save
// export the full-size picture, never the preview.
FloatingWindow {
    id: window
    required property color foreground
    required property color background
    required property color accent
    property string path: ""
    property int backdrop: 0
    property real padding: 64
    property real corners: 12
    property bool shadow: true
    property string status: ""
    visible: path !== ""
    title: Eitr.I18n.tr("Beautify screenshot")
    color: window.background
    implicitWidth: 960
    implicitHeight: 720

    readonly property var backdrops: [
        {name: Eitr.I18n.tr("Theme"), stops: [window.accent, Qt.darker(window.accent, 2.6)]},
        {name: "Ember", stops: ["#f6d365", "#fda085"]},
        {name: "Ocean", stops: ["#4facfe", "#00c6fb"]},
        {name: "Violet", stops: ["#a18cd1", "#fbc2eb"]},
        {name: "Night", stops: ["#232526", "#414345"]},
        {name: Eitr.I18n.tr("Accent"), stops: [window.accent, window.accent]},
        {name: Eitr.I18n.tr("None"), stops: []}
    ]
    function open(file) { status = ""; path = file; }
    function exportTo(file, then) {
        composition.grabToImage(function(result) {
            if (!result.saveToFile(file)) { window.status = Eitr.I18n.tr("Could not save the picture"); return; }
            then(file);
        });
    }
    function save() {
        var target = path.replace(/(\.[^./]+)?$/, "-beautified.png");
        exportTo(target, function(file) { window.status = Eitr.I18n.tr("Saved as {name}", {name: file.split("/").pop()}); });
    }
    function copy() {
        var temporary = (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/eitr-beautified.png";
        exportTo(temporary, function(file) {
            Quickshell.execDetached(["sh", "-c", 'wl-copy --type image/png < "$1"', "sh", file]);
            window.status = Eitr.I18n.tr("Copied, ready to paste");
        });
    }

    IpcHandler {
        target: "beautify"
        function open(path: string): void { window.open(path); }
    }

    Item {
        id: stage
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: controls.top; margins: 20 }
        clip: true
        // The full-size picture, scaled to fit; only its scale changes with the window.
        Item {
            id: composition
            width: Math.max(1, (shot.sourceSize.width || 1) + window.padding * 2)
            height: Math.max(1, (shot.sourceSize.height || 1) + window.padding * 2)
            anchors.centerIn: parent
            scale: Math.min(1, stage.width / width, stage.height / height)
            Rectangle {
                anchors.fill: parent
                visible: window.backdrops[window.backdrop].stops.length > 0
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: window.backdrops[window.backdrop].stops[0] || "transparent" }
                    GradientStop { position: 1; color: window.backdrops[window.backdrop].stops[1] || "transparent" }
                }
            }
            // The shadow wraps the rounded picture: one effect each, since a single
            // MultiEffect with both drops the mask.
            Item {
                id: framed
                x: window.padding; y: window.padding
                width: shot.sourceSize.width; height: shot.sourceSize.height
                layer.enabled: window.shadow
                layer.effect: MultiEffect { shadowEnabled: true; shadowBlur: 0.8; shadowVerticalOffset: 10; shadowOpacity: 0.45 }
                Item {
                    anchors.fill: parent
                    layer.enabled: true
                    layer.effect: MultiEffect { maskEnabled: true; maskSource: roundedMask; maskThresholdMin: 0.5; maskSpreadAtMin: 1 }
                    Image {
                        id: shot
                        anchors.fill: parent
                        source: window.path ? "file://" + window.path : ""
                        cache: false
                    }
                }
            }
            Item {
                id: roundedMask
                width: framed.width; height: framed.height
                visible: false
                layer.enabled: true
                Rectangle { anchors.fill: parent; radius: window.corners; color: "white" }
            }
        }
    }

    Column {
        id: controls
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 20 }
        spacing: 12
        Row {
            spacing: 8
            Repeater {
                model: window.backdrops
                Rectangle {
                    id: swatch
                    required property var modelData
                    required property int index
                    width: 30; height: 30; radius: 15
                    border.width: window.backdrop === index ? 2 : 1
                    border.color: window.backdrop === index ? window.foreground : Qt.alpha(window.foreground, 0.25)
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: swatch.modelData.stops[0] || Qt.alpha(window.foreground, 0.08) }
                        GradientStop { position: 1; color: swatch.modelData.stops[1] || Qt.alpha(window.foreground, 0.08) }
                    }
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.name
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: window.backdrop = swatch.index }
                }
            }
        }
        Row {
            width: parent.width; spacing: 12
            Text { width: 70; height: 30; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Padding"); color: window.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            PanelSlider { id: paddingSlider; width: (parent.width - 70 * 2 - 3 * 12) / 2; from: 0; to: 160; value: window.padding; foreground: window.foreground; accent: window.accent; onMoved: window.padding = Math.round(value) }
            Text { width: 70; height: 30; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Corners"); color: window.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            PanelSlider { width: paddingSlider.width; from: 0; to: 40; value: window.corners; foreground: window.foreground; accent: window.accent; onMoved: window.corners = Math.round(value) }
        }
        Item {
            width: parent.width; height: 32
            Row {
                spacing: 10
                Text { height: 32; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Shadow"); color: window.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                PanelSwitch { anchors.verticalCenter: parent.verticalCenter; checked: window.shadow; foreground: window.foreground; accent: window.accent; Accessible.name: Eitr.I18n.tr("Shadow"); onClicked: window.shadow = checked }
            }
            Row {
                id: actions
                anchors.right: parent.right
                spacing: 8
                Text {
                    height: 32; verticalAlignment: Text.AlignVCenter
                    text: window.status
                    color: Qt.alpha(window.foreground, 0.7); font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                PanelButton { text: Eitr.I18n.tr("Copy picture"); foreground: window.foreground; onClicked: window.copy() }
                PanelButton { text: Eitr.I18n.tr("Save picture"); foreground: window.foreground; onClicked: window.save() }
                PanelButton { text: Eitr.I18n.tr("Close"); foreground: window.foreground; onClicked: window.path = "" }
            }
        }
    }
    Shortcut { sequence: "Escape"; onActivated: window.path = "" }
}
