import ".."
import QtQuick
import QtQuick.Controls
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../AvatarCrop.js" as Crop

Column {
    id: sheet
    required property var centerRef
    // The chosen file: its path, a small upright preview and both sizes (eitr_avatar.preview).
    property var selected: null
    property real zoom: 1
    property real offsetX: 0
    property real offsetY: 0
    property bool pending: false
    // The folder shown by the in-panel picture browser (eitr_avatar.browse), or null.
    property var listing: null
    property bool browsing: false
    readonly property var entries: listing ? listing.folders.map(entry => Object.assign({folder: true}, entry))
        .concat(listing.images.map(entry => Object.assign({folder: false}, entry))) : []
    property bool busy: false
    property string error: ""
    readonly property var account: centerRef.accountPicture
    readonly property string picturePath: account.path || ""
    readonly property var placement: selected ? Crop.clamp(selected.previewWidth, selected.previewHeight, 200, zoom, offsetX, offsetY) : ({scale: 1, x: 0, y: 0})
    spacing: 12
    focus: visible
    onVisibleChanged: {
        if (visible) { reset(); forceActiveFocus(); }
        else DesktopData.releaseOwner(sheet);
    }
    Component.onDestruction: DesktopData.releaseOwner(sheet)
    function reset() { selected = null; zoom = 1; offsetX = 0; offsetY = 0; pending = false; busy = false; error = ""; browsing = false; }
    function close() { reset(); centerRef.page = "general"; }
    function act(name, args) {
        if (busy) return;
        busy = true; error = "";
        DesktopData.accountAction(name, args, sheet, function(message, result) {
            busy = false;
            error = message;
            if (message) return;
            if (name === "browse") { listing = result; browsing = true; grid.positionViewAtBeginning(); }
            else if (name === "preview") { browsing = false; selected = result; zoom = 1; offsetX = 0; offsetY = 0; pending = true; editor.show(); }
            else reset();
        });
    }
    function save() {
        if (!pending || busy || !selected || !editor.loaded) return;
        const crop = Crop.square(selected.previewWidth, selected.previewHeight, 200, zoom, offsetX, offsetY);
        const factor = selected.width / selected.previewWidth;
        act("save", {source: selected.path, x: crop.x * factor, y: crop.y * factor, size: crop.size * factor});
    }
    function browse(folder) { act("browse", folder ? {folder: folder} : {}); }
    function open(entry) {
        if (entry.folder) browse(entry.path);
        else act("preview", {source: entry.path});
    }
    function moveCrop(horizontal, vertical) {
        if (!selected) return;
        offsetX = placement.x + horizontal; offsetY = placement.y + vertical; pending = true;
    }
    Keys.onPressed: event => {
        if (browsing) {
            if (event.key === Qt.Key_Escape) browsing = false;
            else if (event.key === Qt.Key_Backspace && listing && listing.parent) browse(listing.parent);
            else return;
            event.accepted = true;
            return;
        }
        if (event.key === Qt.Key_Escape) close();
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
    // The picture browser: folders first, then images, each opened with a click.
    Row {
        visible: sheet.browsing
        width: parent.width; spacing: 8
        PanelButton {
            id: upButton
            foreground: sheet.centerRef.foreground; text: "‹"
            available: !sheet.busy && !!sheet.listing && !!sheet.listing.parent
            onClicked: sheet.browse(sheet.listing.parent)
        }
        Text {
            width: parent.width - upButton.width - 8; height: upButton.height
            verticalAlignment: Text.AlignVCenter; elide: Text.ElideMiddle
            text: sheet.listing ? sheet.listing.folder : ""
            color: sheet.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
    }
    GridView {
        id: grid
        visible: sheet.browsing
        width: parent.width; height: 320
        clip: true; boundsBehavior: Flickable.StopAtBounds
        cellWidth: Math.floor(width / 4); cellHeight: cellWidth + PanelStyle.captionSize + 8
        model: sheet.entries
        ScrollBar.vertical: ScrollBar {}
        delegate: Item {
            id: cell
            required property var modelData
            width: grid.cellWidth; height: grid.cellHeight
            Rectangle {
                anchors.fill: parent; anchors.margins: 3
                radius: PanelStyle.cornerRadius
                color: Qt.alpha(sheet.centerRef.foreground, PanelStyle.selectionAlpha(false, pointer.containsMouse))
            }
            Item {
                id: thumb
                x: 8; y: 8; width: parent.width - 16; height: width
                Text {
                    anchors.centerIn: parent; visible: cell.modelData.folder
                    text: "󰉋"; color: sheet.centerRef.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: parent.width * 0.6
                }
                Image {
                    anchors.fill: parent; visible: !cell.modelData.folder
                    source: cell.modelData.folder ? "" : "file://" + cell.modelData.path
                    sourceSize.width: width * 2; sourceSize.height: height * 2
                    fillMode: Image.PreserveAspectCrop; asynchronous: true; smooth: true
                }
            }
            Text {
                anchors.top: thumb.bottom; anchors.topMargin: 2
                x: 6; width: parent.width - 12; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideMiddle
                text: cell.modelData.name
                color: sheet.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
            }
            MouseArea {
                id: pointer
                anchors.fill: parent; hoverEnabled: true; enabled: !sheet.busy
                cursorShape: Qt.PointingHandCursor
                onClicked: sheet.open(cell.modelData)
            }
        }
        Text {
            anchors.centerIn: parent; visible: grid.count === 0
            text: Eitr.I18n.tr("No pictures in this folder")
            color: sheet.centerRef.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
    }
    PanelButton {
        visible: sheet.browsing
        foreground: sheet.centerRef.foreground; text: Eitr.I18n.tr("Cancel")
        onClicked: sheet.browsing = false
    }
    Item {
        visible: !sheet.browsing
        width: 200; height: 200
        anchors.horizontalCenter: parent.horizontalCenter
        Eitr.Avatar {
            anchors.centerIn: parent
            size: 200; initial: sheet.account.initial || ""
            source: sheet.picturePath ? "file://" + sheet.picturePath + "?v=" + (sheet.account.version || 0) : ""
            accent: sheet.centerRef.accent; background: sheet.centerRef.background
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
        // Zoom applies to a newly chosen picture; until then the slider keeps its place, unseen.
        visible: !sheet.browsing
        opacity: sheet.selected ? 1 : 0
        anchors.horizontalCenter: parent.horizontalCenter; width: 200
        accent: sheet.centerRef.accent; foreground: sheet.centerRef.foreground
        from: 1; to: 4
        Binding { target: zoomSlider; property: "value"; value: sheet.zoom; when: !zoomSlider.pressed }
        enabled: editor.loaded && !sheet.busy
        onMoved: sheet.zoom = value
    }
    PanelButton {
        visible: !sheet.browsing
        width: parent.width; foreground: sheet.centerRef.foreground
        text: Eitr.I18n.tr("Choose Picture…"); available: !sheet.busy
        onClicked: sheet.browse(sheet.listing ? sheet.listing.folder : "")
    }
    Row {
        visible: !sheet.browsing
        spacing: 8
        PanelButton { foreground: sheet.centerRef.foreground; text: Eitr.I18n.tr("Save"); available: sheet.pending && !sheet.busy && editor.loaded; onClicked: sheet.save() }
        PanelButton { foreground: sheet.centerRef.foreground; text: Eitr.I18n.tr("Remove"); visible: sheet.picturePath !== ""; available: !sheet.busy; onClicked: sheet.act("remove", {}) }
        PanelButton { foreground: sheet.centerRef.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: sheet.close() }
    }
    Text {
        width: parent.width; height: PanelStyle.captionSize + 4; elide: Text.ElideRight
        text: sheet.error
        color: sheet.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
}
