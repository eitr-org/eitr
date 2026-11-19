import ".."
import Eitr as Eitr
import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle
import "../DockModel.js" as DockModel

Item {
    id: card
    objectName: "dockPreviewCard"
    required property string dockEdge
    required property rect anchorRect
    required property real screenWidth
    required property real screenHeight
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property bool previewsEnabled: true
    property string appName: ""
    property string iconSource: ""
    property bool eitrTerminal: false
    property var windowAddresses: []
    property var windowMap: ({})

    signal focusRequested(string address)
    signal closeRequested(string address)

    readonly property bool capturing: opened && previewsEnabled
    readonly property bool hovered: cardHover.hovered
    property real revealProgress: opened ? 1 : 0
    Behavior on revealProgress {
        NumberAnimation {
            duration: DesktopStyle.motionDuration(160)
            easing.type: card.opened ? Easing.OutCubic : Easing.InCubic
        }
    }

    readonly property int tileWidth: 196
    readonly property int previewWidth: 184
    readonly property int previewHeight: 108
    readonly property int tilePadding: 6
    readonly property int tileHeight: tilePadding * 2 + previewHeight + 6 + 18
    readonly property int rowHeight: PanelStyle.selectionRowHeight
    readonly property int spacing: 8
    readonly property int padding: 12
    readonly property int headerHeight: 24
    readonly property int gap: 8
    readonly property int screenMargin: 8
    readonly property bool verticalDock: dockEdge === "left" || dockEdge === "right"
    readonly property real maxCardWidth: Math.max(200, screenWidth - screenMargin * 2 - (verticalDock ? anchorRect.width + gap : 0))
    readonly property real maxCardHeight: Math.max(120, screenHeight - screenMargin * 2 - (!verticalDock ? anchorRect.height + gap : 0))

    readonly property var layout: DockModel.previewGridLayout(
        windowAddresses.length, previewsEnabled, maxCardWidth, maxCardHeight,
        tileWidth, tileHeight, rowHeight, previewsEnabled ? spacing : PanelStyle.selectionRowGap,
        padding, headerHeight)
    readonly property var geometry: DockModel.previewCardGeometry(
        dockEdge, anchorRect, screenWidth, screenHeight, layout.cardWidth, layout.cardHeight, gap, screenMargin)

    x: geometry.x
    y: geometry.y
    width: geometry.width
    height: geometry.height
    visible: opened || revealProgress > 0
    opacity: revealProgress

    transform: Translate {
        readonly property real offset: 6 * (1 - card.revealProgress)
        x: card.dockEdge === "left" ? -offset : card.dockEdge === "right" ? offset : 0
        y: card.dockEdge === "top" ? -offset : card.dockEdge === "bottom" ? offset : 0
    }

    HoverHandler { id: cardHover }

    Rectangle {
        anchors.fill: parent
        radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
        color: card.background
        border.width: 1
        border.color: Qt.alpha(card.foreground, PanelStyle.selectionBorderAlpha)
    }

    Item {
        id: header
        x: card.padding
        y: card.padding
        width: Math.max(0, card.width - card.padding * 2)
        height: 18
        Text {
            anchors.left: parent.left
            anchors.right: countLabel.visible ? countLabel.left : parent.right
            anchors.rightMargin: countLabel.visible ? 8 : 0
            anchors.verticalCenter: parent.verticalCenter
            text: card.appName
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: card.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
            font.bold: true
        }
        Text {
            id: countLabel
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            visible: card.windowAddresses.length > 1
            text: String(card.windowAddresses.length)
            textFormat: Text.PlainText
            color: card.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
            font.features: PanelStyle.tabularFigures
        }
    }

    Flickable {
        id: scroll
        x: card.padding
        y: card.padding + card.headerHeight
        width: Math.max(0, card.width - card.padding * 2)
        height: Math.max(0, card.layout.viewportHeight)
        contentWidth: width
        contentHeight: card.layout.contentHeight
        interactive: card.layout.scrollable
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        Grid {
            id: grid
            width: scroll.width
            columns: card.previewsEnabled ? card.layout.columns : 1
            spacing: card.previewsEnabled ? card.spacing : PanelStyle.selectionRowGap

            Repeater {
                model: card.windowAddresses
                Rectangle {
                    id: itemTile
                    required property string modelData
                    readonly property var windowData: card.windowMap[modelData] || null
                    readonly property bool activeWindow: !!(windowData && windowData.active)
                    readonly property string windowTitle: windowData ? (windowData.title || card.appName || Eitr.I18n.tr("Window")) : ""
                    objectName: "dockPreviewItem-" + modelData
                    width: card.previewsEnabled ? card.tileWidth : card.layout.rowWidth
                    height: card.previewsEnabled ? card.tileHeight : card.rowHeight
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: Qt.rgba(card.foreground.r, card.foreground.g, card.foreground.b,
                        PanelStyle.selectionAlpha(activeWindow, itemMouse.containsMouse))
                    border.width: 1
                    border.color: activeWindow ? Qt.alpha(card.accent, 0.75)
                        : itemMouse.containsMouse ? Qt.alpha(card.foreground, 0.28)
                        : Qt.alpha(card.foreground, PanelStyle.selectionBorderAlpha)

                    Rectangle {
                        id: previewFrame
                        visible: card.previewsEnabled
                        x: card.tilePadding
                        y: card.tilePadding
                        width: card.previewWidth
                        height: card.previewHeight
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: Qt.alpha(card.foreground, 0.06)
                        border.width: 1
                        border.color: Qt.alpha(card.foreground, 0.1)
                        clip: true

                        ScreencopyView {
                            id: screencopy
                            objectName: "dockPreviewScreencopy-" + itemTile.modelData
                            anchors.centerIn: parent
                            width: Math.min(parent.width, implicitWidth)
                            height: Math.min(parent.height, implicitHeight)
                            constraintSize: Qt.size(previewFrame.width, previewFrame.height)
                            captureSource: card.capturing && itemTile.windowData && itemTile.windowData.wayland ? itemTile.windowData.wayland : null
                            live: false
                            onCaptureSourceChanged: if (captureSource) Qt.callLater(function() {
                                if (card.capturing && screencopy.captureSource) screencopy.captureFrame();
                            })
                            Timer {
                                interval: 1000
                                repeat: true
                                running: card.capturing && !!(itemTile.windowData && itemTile.windowData.wayland)
                                onTriggered: screencopy.captureFrame()
                            }
                        }

                        Item {
                            id: placeholder
                            anchors.fill: parent
                            visible: !screencopy.hasContent
                            Rectangle {
                                x: 10; y: 10
                                width: parent.width - 20; height: parent.height - 20
                                radius: DesktopStyle.radius(3)
                                color: Qt.alpha(card.background, 0.45)
                                border.width: 1
                                border.color: Qt.alpha(card.foreground, 0.12)
                                Rectangle {
                                    x: 0; y: 0; width: parent.width; height: 14
                                    radius: parent.radius
                                    color: Qt.alpha(card.foreground, 0.08)
                                }
                                Row {
                                    x: 7; y: 5; spacing: 4
                                    Repeater {
                                        model: 3
                                        Rectangle { width: 4; height: 4; radius: 2; color: Qt.alpha(card.foreground, 0.28) }
                                    }
                                }
                            }
                            Image {
                                id: placeholderIcon
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: 4
                                width: 28; height: 28
                                visible: card.iconSource !== "" && !card.eitrTerminal
                                source: card.iconSource
                                sourceSize: Qt.size(40, 40)
                                smooth: true; mipmap: true; asynchronous: true
                                opacity: 0.85
                            }
                            Image {
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: 4
                                width: 24; height: 24
                                visible: card.eitrTerminal
                                source: visible ? Quickshell.shellDir + "/assets/eitr-logo-white.svg" : ""
                                fillMode: Image.PreserveAspectFit
                                sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                                smooth: true
                                opacity: 0.85
                                layer.enabled: visible
                                layer.effect: MultiEffect { colorization: 1; colorizationColor: card.foreground }
                            }
                            Text {
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: 4
                                visible: placeholderIcon.status !== Image.Ready && !card.eitrTerminal
                                text: "󰀻"
                                color: card.foreground
                                opacity: PanelStyle.secondaryTextOpacity
                                font.family: PanelStyle.fontFamily
                                font.pixelSize: 22
                            }
                        }
                    }

                    Text {
                        visible: card.previewsEnabled
                        x: card.tilePadding
                        y: card.tilePadding + card.previewHeight + 6
                        width: card.previewWidth
                        height: 18
                        text: itemTile.windowTitle
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: card.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }

                    Row {
                        visible: !card.previewsEnabled
                        anchors.fill: parent
                        anchors.leftMargin: PanelStyle.selectionInset
                        anchors.rightMargin: PanelStyle.selectionInset
                        spacing: 8
                        Rectangle {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 6; height: 6; radius: 3
                            visible: itemTile.activeWindow
                            color: card.accent
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - (itemTile.activeWindow ? 14 : 0)
                            text: itemTile.windowTitle
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: card.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                        }
                    }

                    MouseArea {
                        id: itemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                        onClicked: function(event) {
                            if (event.button === Qt.MiddleButton) card.closeRequested(itemTile.modelData);
                            else if (event.button === Qt.LeftButton) card.focusRequested(itemTile.modelData);
                        }
                    }
                }
            }
        }
    }
}
