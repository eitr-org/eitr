import ".."
import QtQuick
import "../JsonState.js" as JsonState
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import QtQuick.Effects
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland

SettingsAppearanceModel {
    id: picker
    onLoaded: Qt.callLater(function() { content.forceActiveFocus(); })
    // Shortcuts and Walker open the carousel on the display in use, like a desktop double-click.
    function focusedScreen() {
        const monitor = Hyprland.focusedMonitor;
        return Quickshell.screens.find(screen => monitor && screen.name === monitor.name) || picker.defaultScreen || Quickshell.screens[0];
    }
    IpcHandler {
        target: "appearance"
        function show(kind: string): void {
            picker.open(kind.startsWith("theme") ? kind : "wallpaper", picker.focusedScreen());
        }
        function wallpaper(path: string): void {
            picker.preferredPath = path;
            picker.open("wallpaper", picker.focusedScreen());
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
                else if (picker.searchable && event.key === Qt.Key_Tab && (event.modifiers & Qt.ControlModifier)) picker.filterThemes(picker.mode === "theme" ? "theme-dark" : picker.mode === "theme-dark" ? "theme-light" : "theme");
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
                // Just above the selected card.
                y: Math.max(PanelStyle.padding, (content.height - content.previewHeight) / 2 - 36 - height)
                width: filters.implicitWidth + 12
                height: PanelStyle.selectionRowHeight + 12
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: picker.background
                visible: picker.searchable
                Row {
                    id: filters
                    anchors.centerIn: parent
                    spacing: PanelStyle.selectionRowGap
                    ChoiceSegmented {
                        width: 180
                        foreground: picker.foreground
                        choices: [{id: "theme-light", label: Eitr.I18n.tr("Light")}, {id: "theme-dark", label: Eitr.I18n.tr("Dark")}]
                        current: picker.mode
                        available: !picker.loading
                        onChosen: value => { picker.filterThemes(value); content.forceActiveFocus(); }
                    }

                    PanelButton {
                        id: addThemes
                        icon: true
                        width: PanelStyle.selectionRowHeight
                        height: PanelStyle.selectionRowHeight
                        text: "󰐕"
                        foreground: picker.foreground
                        activeFocusOnTab: false
                        color: Qt.rgba(foreground.r, foreground.g, foreground.b, PanelStyle.selectionAlpha(false, addHover.containsMouse))
                        border.width: PanelStyle.selectionBorderWidth(false)
                        border.color: Qt.rgba(foreground.r, foreground.g, foreground.b, PanelStyle.selectionBorderAlpha)
                        Accessible.name: Eitr.I18n.tr("Add themes")
                        onClicked: {
                            const tone = picker.mode === "theme-light" ? "light" : picker.mode === "theme-dark" ? "dark" : "all";
                            picker.opened = false;
                            picker.catalogRequested(tone);
                        }
                        MouseArea {
                            id: addHover
                            anchors.fill: parent
                            acceptedButtons: Qt.NoButton
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }
                BarTooltip {
                    target: addThemes
                    hovered: addHover.containsMouse
                    text: Eitr.I18n.tr("Add themes")
                    foreground: picker.foreground
                    background: picker.background
                }
            }
            Text {
                visible: picker.searchable && picker.searchText.length > 0
                anchors.horizontalCenter: parent.horizontalCenter
                y: Math.max(PanelStyle.padding, (content.height - content.previewHeight) / 2 - 36 - PanelStyle.selectionRowHeight - 12 - 40)
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
