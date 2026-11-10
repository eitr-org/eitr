import ".."
import QtQuick
import QtQuick.Controls
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../AvatarCrop.js" as Crop

// The profile picture's crop editor and the owner of its account actions (preview, save,
// remove). Settings > User shows it in a sheet once the file chooser returns a picture.
Column {
    id: sheet
    required property color foreground
    required property color background
    required property color accent
    property var account: ({})
    // The chosen file: its path, a small upright preview and both sizes (eitr_avatar.preview).
    property var selected: null
    property real zoom: 1
    property real offsetX: 0
    property real offsetY: 0
    property bool pending: false
    property bool busy: false
    property string error: ""
    readonly property string picturePath: account.path || ""
    readonly property var placement: selected ? Crop.clamp(selected.previewWidth, selected.previewHeight, 200, zoom, offsetX, offsetY) : ({scale: 1, x: 0, y: 0})
    // Saved, removed or cancelled: the host closes its sheet.
    signal finished()
    spacing: 12
    Component.onDestruction: DesktopData.releaseOwner(sheet)
    function reset() { selected = null; zoom = 1; offsetX = 0; offsetY = 0; pending = false; busy = false; error = ""; }
    function cancel() { DesktopData.releaseOwner(sheet); reset(); finished(); }
    function act(name, args) {
        if (busy) return;
        busy = true; error = "";
        DesktopData.accountAction(name, args, sheet, function(message, result) {
            busy = false;
            error = message;
            if (message) return;
            if (name === "preview") { selected = result; zoom = 1; offsetX = 0; offsetY = 0; pending = true; editor.show(); }
            else { reset(); finished(); }
        });
    }
    // Opens PATH (a file the chooser returned) for cropping.
    function edit(path) {
        reset();
        forceActiveFocus();
        act("preview", {source: path});
    }
    function remove() { act("remove", {}); }
    function save() {
        if (!pending || busy || !selected || !editor.loaded) return;
        const crop = Crop.square(selected.previewWidth, selected.previewHeight, 200, zoom, offsetX, offsetY);
        const factor = selected.width / selected.previewWidth;
        act("save", {source: selected.path, x: crop.x * factor, y: crop.y * factor, size: crop.size * factor});
    }
    function moveCrop(horizontal, vertical) {
        if (!selected) return;
        offsetX = placement.x + horizontal; offsetY = placement.y + vertical; pending = true;
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) cancel();
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) save();
        else if (event.key === Qt.Key_Left) moveCrop(-5, 0);
        else if (event.key === Qt.Key_Right) moveCrop(5, 0);
        else if (event.key === Qt.Key_Up) moveCrop(0, -5);
        else if (event.key === Qt.Key_Down) moveCrop(0, 5);
        else if ((event.key === Qt.Key_Plus || event.key === Qt.Key_Equal) && selected) zoom = Math.min(4, zoom + 0.1);
        else if (event.key === Qt.Key_Minus && selected) zoom = Math.max(1, zoom - 0.1);
        else return;
        event.accepted = true;
    }
    Item {
        width: 200; height: 200
        anchors.horizontalCenter: parent.horizontalCenter
        Eitr.Avatar {
            anchors.centerIn: parent
            size: 200; initial: sheet.account.initial || ""
            source: sheet.picturePath ? "file://" + sheet.picturePath + "?v=" + (sheet.account.version || 0) : ""
            accent: sheet.accent; background: sheet.background
            visible: !sheet.selected
        }
        // The chosen picture, moved and zoomed inside the circle that will be saved.
        Canvas {
            id: editor
            anchors.fill: parent
            visible: sheet.selected !== null
            property url current: ""
            property bool loaded: false
            function show() {
                if (current.toString() !== "") unloadImage(current);
                loaded = false;
                current = "file://" + sheet.selected.preview + "?v=" + sheet.selected.version;
                loadImage(current);
            }
            onImageLoaded: { loaded = isImageLoaded(current) && !isImageError(current); requestPaint(); }
            onPaint: {
                const context = getContext("2d");
                context.reset();
                if (!loaded || !sheet.selected) return;
                const view = sheet.placement;
                const width = sheet.selected.previewWidth * view.scale, height = sheet.selected.previewHeight * view.scale;
                context.beginPath();
                context.arc(100, 100, 100, 0, 2 * Math.PI);
                context.clip();
                context.drawImage(current, (200 - width) / 2 + view.x, (200 - height) / 2 + view.y, width, height);
            }
            Connections { target: sheet; function onPlacementChanged() { editor.requestPaint(); } }
        }
        MouseArea {
            anchors.fill: parent
            enabled: editor.loaded && !sheet.busy
            cursorShape: Qt.PointingHandCursor
            property real previousX: 0
            property real previousY: 0
            onPressed: mouse => { previousX = mouse.x; previousY = mouse.y; sheet.forceActiveFocus(); }
            onPositionChanged: mouse => {
                if (!pressed) return;
                sheet.moveCrop(mouse.x - previousX, mouse.y - previousY);
                previousX = mouse.x; previousY = mouse.y;
            }
            onWheel: wheel => { sheet.zoom = Math.max(1, Math.min(4, sheet.zoom + wheel.angleDelta.y / 1200)); }
        }
    }
    PanelSlider {
        id: zoomSlider
        anchors.horizontalCenter: parent.horizontalCenter; width: 200
        accent: sheet.accent; foreground: sheet.foreground
        from: 1; to: 4
        valueText: Math.round(value * 100) + "%"
        Binding { target: zoomSlider; property: "value"; value: sheet.zoom; when: !zoomSlider.pressed }
        enabled: editor.loaded && !sheet.busy
        onMoved: sheet.zoom = value
    }
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 8
        PanelButton { objectName: "profilePictureSave"; width: 96; foreground: sheet.foreground; text: Eitr.I18n.tr("Save"); available: sheet.pending && !sheet.busy && editor.loaded; onClicked: sheet.save() }
        PanelButton { objectName: "profilePictureCancel"; width: 96; foreground: sheet.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: sheet.cancel() }
    }
    Text {
        width: parent.width; height: PanelStyle.captionSize + 4; elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        text: sheet.error
        color: sheet.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
}
