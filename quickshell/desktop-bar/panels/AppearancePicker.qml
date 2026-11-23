import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

SettingsAppearanceModel {
    id: picker
    property bool docked: false
    property Item dockedContent: null
    // Theme previews keep their 16:9 aspect on every screen shape; wallpapers stay landscape.
    readonly property real themeAspect: 16 / 9
    function wallpaperPreviewWidth(width) { return Math.min(768, width * 0.55); }
    function previewHeightFor(width, heightLimit) {
        return mode === "wallpaper" ? Math.min(475, heightLimit, wallpaperPreviewWidth(width) * 0.62)
            : Math.min(560, heightLimit, width * 0.68 / themeAspect);
    }
    onDockedContentChanged: Qt.callLater(function() {
        if (opened && contentLoader.item) contentLoader.item.forceActiveFocus();
    })
    onLoaded: Qt.callLater(function() { contentLoader.item && contentLoader.item.forceActiveFocus(); })
    // Shortcuts and Walker open the carousel on the display in use, like a desktop double-click.
    function focusedScreen() { return Eitr.Screens.focused(picker.defaultScreen); }
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
        visible: picker.opened && !picker.docked
        screen: picker.targetScreen
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        color: "transparent"
        WlrLayershell.namespace: "desktop-appearance-picker"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

        Rectangle {
            anchors.fill: parent
            color: picker.themeMode ? Qt.rgba(picker.background.r, picker.background.g, picker.background.b, 0.9) : "#b3000000"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: picker.opened = false
            onWheel: function(event) { picker.navigate(event.angleDelta.y > 0 ? -1 : 1); }
        }

        Loader {
            id: contentLoader
            parent: picker.dockedContent || overlay.contentItem
            focus: picker.opened
            anchors.fill: parent
            property bool retained: false
            active: picker.opened || retained
            onLoaded: { retained = true; item.forceActiveFocus(); }
            sourceComponent: Item {
                id: content
                clip: picker.docked
                anchors.fill: parent
                focus: true
                readonly property real headerHeight: PanelStyle.selectionRowHeight + 28
                readonly property real captionHeight: 38
                readonly property real previewHeightLimit: picker.docked ? Math.max(0, height - headerHeight - captionHeight) : height * 0.58
                readonly property real dockedPreviewWidth: Math.min(280, width * 0.56)
                readonly property real dockedAspect: picker.themeMode ? picker.themeAspect : 1.8
                readonly property real previewWidth: picker.docked ? previewHeight * dockedAspect
                    : picker.mode !== "wallpaper" ? previewHeight * picker.themeAspect : picker.wallpaperPreviewWidth(width)
                readonly property real previewHeight: picker.docked ? Math.min(previewHeightLimit, dockedPreviewWidth / dockedAspect)
                    : picker.previewHeightFor(width, previewHeightLimit)
                readonly property real previewTop: picker.docked ? headerHeight + (previewHeightLimit - previewHeight) / 2 : (height - previewHeight) / 2 - 24
                readonly property real sliceWidth: picker.docked ? Math.min(52, width * 0.08) : Math.min(108, width * 0.08)
                readonly property real step: sliceWidth * 0.74
                Keys.onPressed: function(event) {
                    if (event.key === Qt.Key_Escape) {
                        if (picker.searchText) picker.search("");
                        else picker.opened = false;
                    }
                    // Backspace only edits the search; Escape closes.
                    else if (event.key === Qt.Key_Backspace) {
                        if (picker.searchText) picker.search(picker.searchText.slice(0, -1));
                    }
                    else if (picker.themeMode && event.key === Qt.Key_Tab && (event.modifiers & Qt.ControlModifier)) picker.filterThemes(picker.mode === "theme" ? "theme-dark" : picker.mode === "theme-dark" ? "theme-light" : "theme");
                    else if (picker.mode === "wallpaper" && event.key === Qt.Key_Tab && (event.modifiers & Qt.ControlModifier)) picker.setWallpaperScope(picker.wallpaperScope === "all" ? "theme" : "all");
                    else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) picker.apply();
                    else if (event.key === Qt.Key_Left || (!picker.searchable && event.key === Qt.Key_H)) picker.navigate(-1);
                    else if (event.key === Qt.Key_Right || (!picker.searchable && event.key === Qt.Key_L) || event.key === Qt.Key_Tab) picker.navigate(1);
                    else if (picker.searchable && event.text && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)) && !/[\x00-\x1f\x7f]/.test(event.text)) picker.search(picker.searchText + event.text);
                    else return;
                    event.accepted = true;
                }
                Text {
                    id: modeIcon
                    visible: picker.docked
                    x: PanelStyle.padding
                    y: (content.headerHeight - height) / 2
                    text: picker.themeMode ? "󰸌" : "󰋩"
                    color: picker.accent
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.headingSize
                }
                PanelHeading {
                    objectName: "appearanceHeading"
                    x: picker.docked ? modeIcon.x + modeIcon.width + 8 : PanelStyle.padding
                    seal: !picker.docked
                    y: picker.docked ? (content.headerHeight - height) / 2 : PanelStyle.padding
                    width: picker.docked ? Math.max(0, filterFrame.x - x - 8) : parent.width - 2 * PanelStyle.padding
                    text: picker.docked && picker.searchText ? picker.searchText : picker.mode === "wallpaper" ? Eitr.I18n.tr("Wallpaper") : picker.mode === "font" ? Eitr.I18n.tr("Fonts") : Eitr.I18n.tr("Theme")
                    foreground: picker.foreground; accent: picker.accent; rune: "style"
                }
                Rectangle {
                    id: filterFrame
                    objectName: "appearanceFilters"
                    anchors.horizontalCenter: picker.docked ? undefined : parent.horizontalCenter
                    anchors.right: picker.docked ? parent.right : undefined
                    anchors.rightMargin: PanelStyle.padding
                    // Just above the selected card.
                    y: picker.docked ? (content.headerHeight - height) / 2 : Math.max(PanelStyle.padding, (content.height - content.previewHeight) / 2 - 36 - height)
                    width: filters.implicitWidth + 12
                    height: PanelStyle.selectionRowHeight + 12
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: picker.background
                    visible: picker.searchable
                    Row {
                        id: filters
                        anchors.centerIn: parent
                        spacing: PanelStyle.selectionRowGap
                        // Wallpapers: this theme's, or every installed theme's (only the picture changes).
                        ChoiceSegmented {
                            visible: picker.mode === "wallpaper"
                            width: picker.docked ? Math.min(240, content.width * 0.52) : 240
                            foreground: picker.foreground
                            choices: [{id: "theme", label: Eitr.I18n.tr("This theme")}, {id: "all", label: Eitr.I18n.tr("All themes")}]
                            current: picker.wallpaperScope
                            available: !picker.loading
                            onChosen: value => { picker.setWallpaperScope(value); contentLoader.item && contentLoader.item.forceActiveFocus(); }
                        }
                        ChoiceSegmented {
                            visible: picker.themeMode
                            width: picker.docked ? Math.min(180, content.width * 0.44) : 180
                            foreground: picker.foreground
                            choices: [{id: "theme-light", label: Eitr.I18n.tr("Light")}, {id: "theme-dark", label: Eitr.I18n.tr("Dark")}]
                            current: picker.mode
                            available: !picker.loading
                            onChosen: value => { picker.filterThemes(value); contentLoader.item && contentLoader.item.forceActiveFocus(); }
                        }

                        PanelButton {
                            id: addThemes
                            visible: picker.themeMode
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
                    visible: !picker.docked && picker.searchable && picker.searchText.length > 0
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
                        objectName: selected ? "appearanceSelectedPreview" : ""
                        required property int index
                        required property var modelData
                        readonly property int offset: index - picker.selectedIndex
                        readonly property bool selected: offset === 0
                        visible: picker.docked ? selected || Math.abs(offset) <= Math.floor((content.width - content.previewWidth - 2 * PanelStyle.padding) / (2 * content.step))
                            : Math.abs(offset) <= Math.ceil((content.width - content.previewWidth) / (2 * content.step)) + 1
                        width: selected ? content.previewWidth : content.sliceWidth
                        height: selected ? content.previewHeight : content.previewHeight * 0.91
                        x: selected ? (content.width - content.previewWidth) / 2 : (offset < 0 ? (content.width - content.previewWidth) / 2 + offset * content.step : (content.width + content.previewWidth) / 2 - content.sliceWidth * 0.26 + (offset - 1) * content.step)
                        y: content.previewTop + (content.previewHeight - height) / 2
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

                // The selected picture's name (a theme, or a wallpaper without its order number).
                Text {
                    id: selectedName
                    objectName: "appearanceSelectedName"
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: content.previewTop + content.previewHeight + (picker.docked ? 4 : 20)
                    width: content.previewWidth
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideMiddle
                    // The compact strip has room for one line, so the wallpaper's theme joins the name.
                    text: picker.items[picker.selectedIndex] ? picker.items[picker.selectedIndex].name
                        + (picker.docked && themeLine.wanted ? " · " + themeLine.text : "")
                        : picker.searchText ? (picker.themeMode ? Eitr.I18n.tr("No matching themes") : Eitr.I18n.tr("No matching wallpapers"))
                        : (picker.error || Eitr.I18n.tr("Loading..."))
                    color: picker.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.headingSize
                    font.bold: true
                }
                // With every theme's wallpapers, the theme each one comes from.
                Text {
                    id: themeLine
                    readonly property bool wanted: picker.mode === "wallpaper" && picker.wallpaperScope === "all" && !!picker.items[picker.selectedIndex]
                    visible: wanted && !picker.docked
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: selectedName.bottom; anchors.topMargin: 2
                    width: content.previewWidth
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    text: picker.items[picker.selectedIndex] ? (picker.items[picker.selectedIndex].theme || Eitr.I18n.tr("Your wallpapers")) : ""
                    color: picker.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
            }
        }
    }
}
