import ".."
import QtQuick
import "../JsonState.js" as JsonState
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Item {
    id: picker
    property bool opened: false
    property string mode: "wallpaper"
    property var targetScreen: null
    // IPC opens on the bar's primary screen; desktop double-clicks use their own screen.
    property var defaultScreen: null
    property var items: []
    property var allItems: []
    property var catalogs: ({})
    property string searchText: ""
    readonly property bool searchable: mode === "theme-dark" || mode === "theme-light"
    property int selectedIndex: 0
    property color accent: "#cdd6f4"
    property color foreground: "#ffffff"
    property color background: "#202024"
    property string error: ""

    function open(kind, screen) {
        if (loader.running)
            return;
        mode = kind;
        targetScreen = screen;
        const cached = catalogs[mode] || [];
        if (JsonState.changed(items, cached)) items = cached;
        if (JsonState.changed(allItems, cached)) allItems = cached;
        searchText = "";
        error = "";
        opened = true;
        loader.command = ["python3", Quickshell.shellDir + "/scripts/appearance-items.py", mode];
        loader.running = true;
    }

    function navigate(delta) {
        if (items.length)
            selectedIndex = (selectedIndex + delta + items.length) % items.length;
    }

    function search(value) {
        searchText = value;
        var query = value.trim().toLocaleLowerCase();
        items = allItems.filter(function(item) {
            return item.name.toLocaleLowerCase().indexOf(query) !== -1;
        });
        selectedIndex = 0;
    }

    function apply() {
        if (!items.length || applyProcess.running)
            return;
        var script = mode.startsWith("theme-") ? "style/apply.sh" : "wallpaper/apply.sh";
        applyProcess.command = [Eitr.Paths.code("walker/scripts/actions/") + script, items[selectedIndex].value];
        opened = false;
        applyProcess.running = true;
    }

    function switchThemeMode() {
        if (!loader.running && searchable)
            open(mode === "theme-light" ? "theme-dark" : "theme-light", targetScreen);
    }

    Process {
        id: loader
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const result = JsonState.parse(output.text, code, {mode: "string", items: [{name: "string", value: "string", image: "string", current: "boolean"}], accent: "string", foreground: "string", background: "string"});
            const data = result.data;
            if (result.ok) {
                picker.mode = data.mode;
                if (JsonState.changed(picker.items, data.items)) picker.items = data.items;
                if (JsonState.changed(picker.allItems, data.items)) picker.allItems = data.items;
                picker.catalogs[picker.mode] = data.items;
                picker.accent = data.accent;
                picker.foreground = data.foreground;
                picker.background = data.background;
                picker.selectedIndex = 0;
                for (var index = 0; index < data.items.length; index++) {
                    if (data.items[index].current)
                        picker.selectedIndex = index;
                }
                if (picker.searchText) picker.search(picker.searchText);
                picker.error = data.items.length ? "" : Eitr.I18n.tr("No images found");
            } else {
                picker.items = [];
                picker.allItems = [];
                picker.catalogs[picker.mode] = [];
                picker.error = Eitr.I18n.tr("Images unavailable");
            }
            Qt.callLater(function() { content.forceActiveFocus(); });
        }
    }

    Process { id: applyProcess }

    IpcHandler {
        target: "appearance"
        function show(kind: string): void {
            picker.open(kind.startsWith("theme") ? kind : "wallpaper", picker.defaultScreen || Quickshell.screens[0]);
        }
        function close(): void { picker.opened = false; }
        function next(): void { picker.navigate(1); }
    }

    Variants {
        model: Quickshell.screens
        PanelWindow {
            required property var modelData
            screen: modelData
            anchors { top: true; bottom: true; left: true; right: true }
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "desktop-appearance-clicks"
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onDoubleClicked: function(mouse) {
                    picker.open(mouse.button === Qt.RightButton ? "theme" : "wallpaper", modelData);
                }
            }
        }
    }

    PanelWindow {
        id: overlay
        visible: picker.opened
        screen: picker.targetScreen
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        color: "transparent"
        WlrLayershell.namespace: "desktop-appearance-picker"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

        Rectangle {
            anchors.fill: parent
            color: picker.searchable ? Qt.rgba(picker.background.r, picker.background.g, picker.background.b, 0.9) : "#b3000000"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: picker.opened = false
            onWheel: function(event) { picker.navigate(event.angleDelta.y > 0 ? -1 : 1); }
        }

        Item {
            id: content
            anchors.fill: parent
            focus: true
            // Theme previews keep their 16:9 aspect on every screen shape.
            readonly property real previewAspect: 16 / 9
            readonly property real previewWidth: picker.mode !== "wallpaper" ? previewHeight * previewAspect : Math.min(768, width * 0.55)
            readonly property real previewHeight: picker.mode !== "wallpaper" ? Math.min(560, height * 0.58, width * 0.68 / previewAspect) : Math.min(475, height * 0.58)
            readonly property real sliceWidth: Math.min(108, width * 0.08)
            readonly property real step: sliceWidth * 0.74
            Keys.onPressed: function(event) {
                if (event.key === Qt.Key_Escape) {
                    if (picker.searchText) picker.search("");
                    else picker.opened = false;
                }
                else if (event.key === Qt.Key_Backspace) {
                    if (picker.searchText) picker.search(picker.searchText.slice(0, -1));
                    else picker.opened = false;
                }
                else if (picker.searchable && event.key === Qt.Key_Tab && (event.modifiers & Qt.ControlModifier)) picker.switchThemeMode();
                else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) picker.apply();
                else if (event.key === Qt.Key_Left || (!picker.searchable && event.key === Qt.Key_H)) picker.navigate(-1);
                else if (event.key === Qt.Key_Right || (!picker.searchable && event.key === Qt.Key_L) || event.key === Qt.Key_Tab) picker.navigate(1);
                else if (picker.searchable && event.text && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)) && !/[\x00-\x1f\x7f]/.test(event.text)) picker.search(picker.searchText + event.text);
                else return;
                event.accepted = true;
            }
            PanelHeading {
                x: PanelStyle.padding; y: PanelStyle.padding
                width: parent.width - 2 * PanelStyle.padding
                text: picker.mode === "wallpaper" ? Eitr.I18n.tr("Wallpaper") : picker.mode === "font" ? Eitr.I18n.tr("Fonts") : Eitr.I18n.tr("Theme")
                foreground: picker.foreground; accent: picker.accent; rune: "style"
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: PanelStyle.padding
                width: filters.implicitWidth + 12
                height: PanelStyle.selectionRowHeight + 12
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: picker.background
                visible: picker.searchable
                Row {
                    id: filters
                    anchors.centerIn: parent
                    spacing: PanelStyle.selectionRowGap
                    Repeater {
                        model: [{mode: "theme-light", glyph: "󰖙", label: Eitr.I18n.tr("Light")},
                                {mode: "theme-dark", glyph: "󰖔", label: Eitr.I18n.tr("Dark")}]
                        delegate: PanelButton {
                            required property var modelData
                            icon: true
                            width: PanelStyle.selectionRowHeight
                            height: PanelStyle.selectionRowHeight
                            text: modelData.glyph
                            foreground: picker.foreground
                            selected: picker.mode === modelData.mode
                            activeFocusOnTab: false
                            available: !loader.running
                            color: Qt.rgba(foreground.r, foreground.g, foreground.b,
                                               PanelStyle.selectionAlpha(selected, filterHover.containsMouse))
                            border.width: PanelStyle.selectionBorderWidth(selected)
                            border.color: Qt.rgba(foreground.r, foreground.g, foreground.b, PanelStyle.selectionBorderAlpha)
                            Accessible.name: modelData.label
                            onClicked: {
                                if (!selected) picker.switchThemeMode();
                                content.forceActiveFocus();
                            }
                            MouseArea {
                                id: filterHover
                                anchors.fill: parent
                                acceptedButtons: Qt.NoButton
                                hoverEnabled: true
                            }
                        }
                    }
                }
            }
            Text {
                visible: picker.searchable && picker.searchText.length > 0
                anchors.horizontalCenter: parent.horizontalCenter
                y: Math.max(PanelStyle.padding, (content.height - content.previewHeight) / 2 - 70)
                width: content.previewWidth
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideLeft
                text: picker.searchText
                color: picker.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.headingSize
            }

            Repeater {
                model: picker.items
                delegate: Item {
                    id: tile
                    required property int index
                    required property var modelData
                    readonly property int offset: index - picker.selectedIndex
                    readonly property bool selected: offset === 0
                    visible: Math.abs(offset) <= Math.ceil((content.width - content.previewWidth) / (2 * content.step)) + 1
                    width: selected ? content.previewWidth : content.sliceWidth
                    height: selected ? content.previewHeight : content.previewHeight * 0.91
                    x: selected ? (content.width - content.previewWidth) / 2 : (offset < 0 ? (content.width - content.previewWidth) / 2 + offset * content.step : (content.width + content.previewWidth) / 2 - content.sliceWidth * 0.26 + (offset - 1) * content.step)
                    y: (content.height - height) / 2 - 24
                    z: selected ? 100 : 50 - Math.abs(offset)
                    Behavior on x { NumberAnimation { duration: DesktopStyle.motionDuration(160); easing.type: Easing.OutCubic } }
                    Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(160); easing.type: Easing.OutCubic } }
                    Behavior on height { NumberAnimation { duration: DesktopStyle.motionDuration(160); easing.type: Easing.OutCubic } }
                    Behavior on y { NumberAnimation { duration: DesktopStyle.motionDuration(160); easing.type: Easing.OutCubic } }

                    Rectangle {
                        id: roundedMask
                        anchors.fill: parent
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: "white"
                        visible: false
                        layer.enabled: true
                    }

                    Item {
                        anchors.fill: parent
                        clip: true
                        layer.enabled: true
                        layer.effect: MultiEffect { maskEnabled: true; maskSource: roundedMask }
                        Rectangle { anchors.fill: parent; color: "#202024" }
                        Image {
                            anchors.fill: parent
                            source: tile.visible ? tile.modelData.image : ""
                            sourceSize.width: Math.ceil(content.previewWidth)
                            sourceSize.height: Math.ceil(content.previewHeight)
                            asynchronous: true
                            cache: false
                            fillMode: picker.mode !== "wallpaper" && tile.selected ? Image.PreserveAspectFit : Image.PreserveAspectCrop
                        }
                        Rectangle { anchors.fill: parent; color: tile.selected ? "transparent" : "#70000000" }
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        border.color: tile.selected ? picker.accent : "#66ffffff"
                        border.width: tile.selected ? 3 : 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: tile.selected ? picker.apply() : picker.selectedIndex = tile.index
                        onWheel: function(event) { picker.navigate(event.angleDelta.y > 0 ? -1 : 1); }
                    }
                }
            }

            Text {
                visible: picker.mode !== "wallpaper" || !picker.items[picker.selectedIndex]
                anchors.horizontalCenter: parent.horizontalCenter
                y: (content.height + content.previewHeight) / 2 - 4
                width: content.previewWidth
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideMiddle
                text: picker.items[picker.selectedIndex] ? picker.items[picker.selectedIndex].name : (picker.searchText ? Eitr.I18n.tr("No matching themes") : (picker.error || Eitr.I18n.tr("Loading...")))
                color: picker.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.headingSize
                font.bold: true
            }
        }
    }
}
