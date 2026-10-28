import Eitr as Eitr
import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland
import "PanelStyle.js" as PanelStyle
import "WorkspaceModel.js" as WorkspaceModel

Rectangle {
    id: tile
    required property var workspace
    required property color foreground
    required property color background
    required property color accent
    required property bool capturing
    property bool selected: false
    property bool current: false
    signal chosen(int workspaceId)
    signal hovered()
    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
    color: background
    border.width: selected ? 2 : 1
    border.color: Qt.alpha(foreground, selected ? 0.8 : 0.2)
    HoverHandler { onHoveredChanged: if (hovered) tile.hovered() }
    Rectangle {
        id: roundedDesktopMask
        x: desktop.x; y: desktop.y
        width: desktop.width; height: desktop.height
        radius: Math.max(0, tile.radius - desktop.x)
        color: "white"
        antialiasing: true
        visible: false
        layer.enabled: true
    }
    Item {
        id: desktop
        x: 2; y: 2; width: parent.width - 4; height: parent.height - 4
        clip: true
        layer.enabled: true
        layer.effect: MultiEffect { maskEnabled: true; maskSource: roundedDesktopMask }
        readonly property var geometry: WorkspaceModel.frame(tile.workspace)
        readonly property real fit: Math.min(width / geometry.width, height / geometry.height)
        Image {
            anchors.fill: parent
            source: "file://" + Quickshell.env("HOME") + "/.cache/current-wallpaper-image"
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            sourceSize: Qt.size(Math.ceil(desktop.width), Math.ceil(desktop.height))
        }
        Repeater {
            model: tile.workspace.windows
            Rectangle {
                id: thumbnail
                required property var modelData
                readonly property var info: modelData.lastIpcObject || {}
                readonly property var at: info.at || [0, 0]
                readonly property var dimensions: info.size || [800, 600]
                x: (desktop.width - desktop.geometry.width * desktop.fit) / 2 + (at[0] - desktop.geometry.x) * desktop.fit
                y: (desktop.height - desktop.geometry.height * desktop.fit) / 2 + (at[1] - desktop.geometry.y) * desktop.fit
                width: Math.max(1, dimensions[0] * desktop.fit)
                height: Math.max(1, dimensions[1] * desktop.fit)
                color: Qt.alpha(tile.foreground, 0.08)
                border.width: 1; border.color: Qt.alpha(tile.foreground, 0.18)
                clip: true
                ScreencopyView {
                    id: preview
                    anchors.centerIn: parent
                    width: Math.min(parent.width, implicitWidth)
                    height: Math.min(parent.height, implicitHeight)
                    constraintSize: Qt.size(thumbnail.width, thumbnail.height)
                    captureSource: tile.capturing ? thumbnail.modelData.wayland : null
                    live: false
                    Timer {
                        interval: 1000; repeat: true
                        running: tile.capturing && thumbnail.modelData.wayland !== null
                        onTriggered: preview.captureFrame()
                    }
                }
                Text {
                    anchors.centerIn: parent
                    width: Math.max(0, parent.width - 12)
                    visible: !preview.hasContent
                    text: thumbnail.info.class || thumbnail.modelData.title || Eitr.I18n.tr("Window")
                    color: tile.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                    horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                }
            }
        }
    }
    Rectangle {
        x: 10; y: 10; z: 10
        width: numberLabel.implicitWidth + 16; height: 34
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(tile.background, 0.92)
        border.width: tile.current ? 2 : 1
        border.color: tile.current ? tile.accent : Qt.alpha(tile.foreground, 0.3)
        Text {
            id: numberLabel
            anchors.centerIn: parent
            text: String(tile.workspace.id).padStart(2, "0")
            color: tile.foreground
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize; font.bold: true
        }
    }
    MouseArea {
        z: 20
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: tile.chosen(tile.workspace.id)
    }
}
