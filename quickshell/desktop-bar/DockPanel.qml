import QtQuick
import "JsonState.js" as JsonState
import Quickshell

Item {
    id: panel
    property Item attachmentTarget
    property string attachmentEdge: "top"
    property string alignment: "right"
    property real leadingOffset: 0
    property bool opened: false
    readonly property int transitionDuration: DesktopStyle.motionDuration(320)
    readonly property bool transitioning: revealProgress > 0 && revealProgress < 1
    // Queries start on opened; a first snapshot releases the wait after layout settles.
    property bool waitForFreshData: false
    property bool preparing: false
    property bool revealReady: false
    property double revealStartedAt: 0
    function remainingResizeDuration() {
        return transitioning && opened
            ? Math.max(0, transitionDuration - (Date.now() - revealStartedAt)) : transitionDuration;
    }
    // Data that arrives while the panel unfolds waits for the unfold to finish:
    // rebuilding lists mid-animation stalls rendering and makes the panel jump.
    property var deferredUpdates: []
    signal revealed()
    function updateContent(action) {
        if (opened && revealReady && revealProgress < 1) {
            deferredUpdates = deferredUpdates.concat([action]);
            return;
        }
        action();
        dataReady();
    }
    function flushDeferredUpdates() {
        const pending = deferredUpdates;
        deferredUpdates = [];
        pending.forEach(action => action());
    }
    onRevealProgressChanged: {
        if (revealProgress < 1 || !opened) return;
        flushDeferredUpdates();
        revealed();
    }
    function dataReady() {
        if (opened && preparing) layoutReady.restart();
    }
    function applySnapshot(name, value) {
        updateContent(function() { if (JsonState.changed(panel[name], value)) panel[name] = value; });
    }
    property Timer layoutReady: Timer {
        interval: 0
        onTriggered: panel.startReveal()
    }
    function startReveal() {
        if (!opened || !preparing) return;
        preparationCap.stop();
        preparing = false;
        revealStartedAt = Date.now();
        revealReady = true;
    }
    property Timer preparationCap: Timer {
        interval: 100
        onTriggered: panel.startReveal()
    }
    function prepareOpening() {
        layoutReady.stop();
        preparationCap.stop();
        if (opened) {
            preparing = true;
            if (waitForFreshData) preparationCap.start();
            else layoutReady.start();
        } else {
            preparing = false;
            revealReady = false;
            flushDeferredUpdates();
        }
    }
    Component.onCompleted: if (opened) prepareOpening()
    property Connections opening: Connections {
        target: panel
        function onOpenedChanged() { panel.prepareOpening(); }
    }
    property real revealProgress: opened && revealReady ? 1 : 0
    visible: opened || revealProgress > 0
    Behavior on revealProgress {
        NumberAnimation {
            duration: panel.transitionDuration
            easing.type: panel.opened ? Easing.OutCubic : Easing.InCubic
        }
    }
    readonly property real desiredWidth: implicitWidth
    readonly property real desiredHeight: implicitHeight
    readonly property var hostWindow: attachmentTarget ? attachmentTarget.QsWindow.window : null
    readonly property bool detached: !!hostWindow && (!!hostWindow.centeredLayout || !!hostWindow.notchLayout || !!hostWindow.islandsLayout)
    readonly property bool centeredPlacement: !!hostWindow && !!hostWindow.centeredLayout
    readonly property var edgeInsets: detached ? (!centeredPlacement && hostWindow.outerGaps ? hostWindow.outerGaps : [12, 12, 12, 12]) : [0, 0, 0, 0]
    readonly property real attachmentGap: detached ? hostWindow.panelGap : 0
    readonly property var focusWindows: hostWindow ? (hostWindow.panelFocusWindows || [hostWindow]) : []
    readonly property Item strip: hostWindow ? hostWindow.stripItem : null
    parent: hostWindow ? hostWindow.contentItem : null
    z: 100
    width: detached && parent && strip ? Math.min(desiredWidth, parent.width - (attachmentEdge === "left" || attachmentEdge === "right" ? strip.width + attachmentGap + (hostWindow.islandsLayout ? hostWindow.islandGap : 0) + (attachmentEdge === "left" ? edgeInsets[1] : edgeInsets[3]) : edgeInsets[1] + edgeInsets[3])) : desiredWidth
    height: detached && parent && strip ? Math.min(desiredHeight, parent.height - (attachmentEdge === "top" || attachmentEdge === "bottom" ? strip.height + attachmentGap + (hostWindow.islandsLayout ? hostWindow.islandGap : 0) + (attachmentEdge === "top" ? edgeInsets[2] : edgeInsets[0]) : edgeInsets[0] + edgeInsets[2])) : desiredHeight
    PanelSizeBehavior on width { ownerPanel: panel }
    PanelSizeBehavior on height { ownerPanel: panel }
    x: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (attachmentEdge === "left") return strip.x + strip.width + attachmentGap;
        if (attachmentEdge === "right") return strip.x - width - attachmentGap;
        var desired = centeredPlacement ? (parent.width - width) / 2 : alignment === "left" ? 0 : alignment === "right" ? parent.width - width : (parent.width - width) / 2;
        return Math.max(edgeInsets[3], Math.min(parent.width - width - edgeInsets[1], desired));
    }
    y: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (attachmentEdge === "top") return strip.y + strip.height + attachmentGap;
        if (attachmentEdge === "bottom") return strip.y - height - attachmentGap;
        var desired = centeredPlacement ? (parent.height - height) / 2 : alignment === "left" ? leadingOffset : alignment === "right" ? parent.height - height : (parent.height - height) / 2;
        return Math.max(edgeInsets[0], Math.min(parent.height - height - edgeInsets[2], desired));
    }
}
