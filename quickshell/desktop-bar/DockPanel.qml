import QtQuick
import Quickshell

Item {
    id: panel
    property Item attachmentTarget
    property string attachmentEdge: "top"
    property string alignment: "right"
    property real leadingOffset: 0
    property bool opened: false
    readonly property int transitionDuration: 320
    property real revealProgress: opened ? 1 : 0
    visible: opened || revealProgress > 0
    Behavior on revealProgress {
        NumberAnimation {
            duration: panel.transitionDuration
            easing.type: panel.opened ? Easing.OutCubic : Easing.InCubic
        }
    }
    readonly property var hostWindow: attachmentTarget ? attachmentTarget.QsWindow.window : null
    readonly property bool detached: !!hostWindow && !!hostWindow.centeredLayout
    readonly property real attachmentGap: detached ? hostWindow.panelGap : 0
    readonly property var focusWindows: hostWindow ? (hostWindow.panelFocusWindows || [hostWindow]) : []
    readonly property Item strip: hostWindow ? hostWindow.stripItem : null
    parent: hostWindow ? hostWindow.contentItem : null
    z: 100
    width: detached && parent && strip ? Math.min(implicitWidth, parent.width - (attachmentEdge === "left" || attachmentEdge === "right" ? strip.width + attachmentGap + 12 : 24)) : implicitWidth
    height: detached && parent && strip ? Math.min(implicitHeight, parent.height - (attachmentEdge === "top" || attachmentEdge === "bottom" ? strip.height + attachmentGap + 12 : 24)) : implicitHeight
    PanelSizeBehavior on width { ownerPanel: panel }
    PanelSizeBehavior on height { ownerPanel: panel }
    x: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (attachmentEdge === "left") return strip.x + strip.width + attachmentGap;
        if (attachmentEdge === "right") return strip.x - width - attachmentGap;
        var desired = detached ? (parent.width - width) / 2 : alignment === "left" ? 0 : alignment === "right" ? parent.width - width : (parent.width - width) / 2;
        return Math.max(0, Math.min(parent.width - width, desired));
    }
    y: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (attachmentEdge === "top") return strip.y + strip.height + attachmentGap;
        if (attachmentEdge === "bottom") return strip.y - height - attachmentGap;
        var desired = detached ? (parent.height - height) / 2 : alignment === "left" ? leadingOffset : alignment === "right" ? parent.height - height : (parent.height - height) / 2;
        return Math.max(0, Math.min(parent.height - height, desired));
    }
}
