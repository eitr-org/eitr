pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

Item {
    id: widget
    required property var entry
    required property color foreground
    required property color background
    required property color accent
    property bool editing: false
    signal moved(real deltaX, real deltaY)
    signal resized(real deltaX, real deltaY)
    signal finished()
    Rectangle { anchors.fill: parent; color: widget.background; radius: DesktopStyle.radius(PanelStyle.controlRadius) }
    PluginComponent {
        anchors.fill: parent
        entry: widget.entry
        foreground: widget.foreground; background: widget.background; accent: widget.accent
    }
    Rectangle {
        anchors.fill: parent; visible: widget.editing; color: "transparent"
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        border.color: widget.accent; border.width: 2
    }
    Rectangle {
        visible: widget.editing; width: parent.width; height: 28
        color: widget.background; radius: DesktopStyle.radius(PanelStyle.controlRadius)
        Text {
            anchors.centerIn: parent; text: "⠿ " + widget.entry.title; textFormat: Text.PlainText
            width: parent.width - 12; elide: Text.ElideRight
            color: widget.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.SizeAllCursor
            property point start
            onPressed: function(mouse) { start = mapToGlobal(mouse.x, mouse.y); }
            onPositionChanged: function(mouse) {
                if (!pressed) return;
                const next = mapToGlobal(mouse.x, mouse.y);
                widget.moved(next.x - start.x, next.y - start.y); start = next;
            }
            onReleased: widget.finished()
            onCanceled: widget.finished()
        }
    }
    Rectangle {
        visible: widget.editing; width: 28; height: 28
        anchors.right: parent.right; anchors.bottom: parent.bottom
        color: widget.accent; radius: DesktopStyle.radius(PanelStyle.controlRadius)
        Text { anchors.centerIn: parent; text: "↘"; color: widget.background; font.pixelSize: 20 }
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.SizeFDiagCursor
            property point start
            onPressed: function(mouse) { start = mapToGlobal(mouse.x, mouse.y); }
            onPositionChanged: function(mouse) {
                if (!pressed) return;
                const next = mapToGlobal(mouse.x, mouse.y);
                widget.resized(next.x - start.x, next.y - start.y); start = next;
            }
            onReleased: widget.finished()
            onCanceled: widget.finished()
        }
    }
    PanelButton {
        visible: widget.editing
        anchors.bottom: parent.bottom; anchors.left: parent.left
        text: Eitr.I18n.tr("Done"); foreground: widget.foreground
        onClicked: PluginRegistry.editing = false
    }
}
