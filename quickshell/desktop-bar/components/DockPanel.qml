import ".."
import QtQuick
import "../JsonState.js" as JsonState
import Quickshell

Item {
    id: panel
    property Item inlineParent: null
    readonly property bool embedded: !!inlineParent
    property Item attachmentTarget
    // The bar item a Dynamic/Islands card grows from, when it is not the attachment target.
    property Item morphAnchor: null
    property string attachmentEdge: "top"
    property string alignment: "right"
    property real leadingOffset: 0
    function openSettings(destination) {
        if (embedded) return;
        if (hostWindow && hostWindow.host) hostWindow.host.showSettings(destination);
        opened = false;
    }
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
    // Placement inputs exclude any trailing join that edge contact itself removes.
    readonly property real navigationBand: morphIsland ? 40 : 0
    property real edgeContactWidth: desiredWidth
    property real edgeContactHeight: desiredHeight
    readonly property bool verticalAttachment: attachmentEdge === "left" || attachmentEdge === "right"
    readonly property real placementExtent: {
        var desired = verticalAttachment ? edgeContactHeight : edgeContactWidth;
        return detached ? Math.min(desired, availableExtent - (verticalAttachment
            ? edgeInsets[0] + edgeInsets[2] : edgeInsets[1] + edgeInsets[3])) : desired;
    }
    readonly property real availableExtent: parent ? (verticalAttachment ? parent.height : parent.width) : 0
    readonly property real placementStart: {
        if (!strip || !parent || !attachmentTarget) return 0;
        var desired = centeredPlacement || alignment === "center" ? (availableExtent - placementExtent) / 2
            : alignment === "left" ? (verticalAttachment ? leadingOffset : 0) : availableExtent - placementExtent;
        return Math.max(verticalAttachment ? edgeInsets[0] : edgeInsets[3],
            Math.min(availableExtent - placementExtent - (verticalAttachment ? edgeInsets[2] : edgeInsets[1]), desired));
    }
    readonly property bool touchesLeadingEdge: placementStart <= 0
    readonly property bool touchesTrailingEdge: !!parent && placementStart + placementExtent >= availableExtent
    readonly property real desiredWidth: implicitWidth + (verticalAttachment ? navigationBand : 0)
    readonly property real desiredHeight: implicitHeight + (verticalAttachment ? 0 : navigationBand)
    readonly property var hostWindow: attachmentTarget ? attachmentTarget.QsWindow.window : null
    readonly property bool detached: !!hostWindow && (!!hostWindow.centeredLayout || !!hostWindow.notchLayout || !!hostWindow.islandsLayout || !!hostWindow.dynamicLayout || !!hostWindow.dropLayout)
    // Centered, Dynamic and Drop gather the bar at the centre, so their panels open there too.
    readonly property bool centeredPlacement: !!hostWindow && (!!hostWindow.centeredLayout || !!hostWindow.dynamicLayout || !!hostWindow.dropLayout)
    readonly property var edgeInsets: detached ? (!centeredPlacement && hostWindow.outerGaps ? hostWindow.outerGaps : [12, 12, 12, 12]) : [0, 0, 0, 0]
    readonly property real attachmentGap: detached ? hostWindow.panelGap : 0
    readonly property var focusWindows: hostWindow ? (hostWindow.panelFocusWindows || [hostWindow]) : []
    readonly property Item strip: hostWindow ? hostWindow.stripItem : null
    // Dynamic: the owning island grows into this panel, which then draws no surface of its own.
    readonly property Item morphIsland: hostWindow && hostWindow.dynamicLayout && !FocusMode.enabled && hostWindow.dynamicSurfaces
        ? hostWindow.dynamicSurfaces.islandFor(panel) : null
    readonly property point morphOrigin: morphIsland && strip ? hostWindow.dynamicSurfaces.panelOrigin(panel, strip.x, strip.y) : Qt.point(0, 0)
    // Islands: a card grows out of the pill holding this panel's icon, from the pill's
    // edge toward the panel's usual side, covering the bar row while open.
    readonly property bool islandsActive: !!hostWindow && !!hostWindow.islandsLayout && !FocusMode.enabled && !!hostWindow.islandSurfaces
    readonly property Item livePill: islandsActive ? hostWindow.islandSurfaces.pillFor(morphAnchor || attachmentTarget) : null
    // From the moment it is asked to open until it has folded away, a panel keeps the
    // pill it grows from: pills slide aside meanwhile and the lookup can flicker, which
    // swapped the hidden pill back and forth and left its icons invisible.
    readonly property bool holdsPill: opened || visible || (!!hostWindow && hostWindow.pendingPanel === panel)
    property Item heldPill: null
    onHoldsPillChanged: heldPill = holdsPill ? livePill : null
    onLivePillChanged: if (holdsPill && !heldPill) heldPill = livePill
    // Leaving Islands while a panel is open drops the held pill, or its icons would stay
    // hidden under a card that no longer exists.
    onIslandsActiveChanged: heldPill = islandsActive && holdsPill ? livePill : null
    readonly property Item morphPill: !islandsActive ? null : holdsPill ? heldPill || livePill : livePill
    readonly property rect pillRect: {
        if (!morphPill || !parent || !strip) return Qt.rect(0, 0, 0, 0);
        var moved = morphPill.x + morphPill.y + morphPill.width + morphPill.height + strip.x + strip.y;
        var at = morphPill.mapToItem(parent, 0, 0);
        return Qt.rect(at.x, at.y, morphPill.width, morphPill.height);
    }
    function pillStart(start, length, size, limit) {
        var grow = morphPill ? morphPill.grow : "center";
        var desired = grow === "start" ? start : grow === "end" ? start + length - size : start + (length - size) / 2;
        return Math.max(0, Math.min(limit - size, desired));
    }
    // Only an open (or folding) panel sits in the bar window. A closed panel left there
    // kept a stale window when the bar's screen was unplugged, and Qt crashed on it.
    parent: inlineParent || (hostWindow && (opened || revealProgress > 0) ? hostWindow.contentItem : null)
    z: 100
    width: detached && parent && strip ? Math.min(desiredWidth, parent.width - (attachmentEdge === "left" || attachmentEdge === "right" ? strip.width + attachmentGap + ((hostWindow.islandsLayout || hostWindow.dynamicLayout || hostWindow.dropLayout) ? hostWindow.islandGap : 0) + (attachmentEdge === "left" ? edgeInsets[1] : edgeInsets[3]) : edgeInsets[1] + edgeInsets[3])) : desiredWidth
    height: detached && parent && strip ? Math.min(desiredHeight, parent.height - (attachmentEdge === "top" || attachmentEdge === "bottom" ? strip.height + attachmentGap + ((hostWindow.islandsLayout || hostWindow.dynamicLayout || hostWindow.dropLayout) ? hostWindow.islandGap : 0) + (attachmentEdge === "top" ? edgeInsets[2] : edgeInsets[0]) : edgeInsets[0] + edgeInsets[2])) : desiredHeight
    PanelSizeBehavior on width { ownerPanel: panel }
    PanelSizeBehavior on height { ownerPanel: panel }
    x: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (morphIsland) return morphOrigin.x;
        if (morphPill) return attachmentEdge === "left" ? pillRect.x : attachmentEdge === "right" ? pillRect.x + pillRect.width - width
            : pillStart(pillRect.x, pillRect.width, width, parent.width);
        if (attachmentEdge === "left") return strip.x + strip.width + attachmentGap;
        if (attachmentEdge === "right") return strip.x - width - attachmentGap;
        var desired = centeredPlacement ? (parent.width - width) / 2 : alignment === "left" ? 0 : alignment === "right" ? parent.width - width : (parent.width - width) / 2;
        return Math.max(edgeInsets[3], Math.min(parent.width - width - edgeInsets[1], desired));
    }
    y: {
        if (!strip || !parent || !attachmentTarget) return 0;
        if (morphIsland) return morphOrigin.y;
        if (morphPill) return attachmentEdge === "top" ? pillRect.y : attachmentEdge === "bottom" ? pillRect.y + pillRect.height - height
            : pillStart(pillRect.y, pillRect.height, height, parent.height);
        if (attachmentEdge === "top") return strip.y + strip.height + attachmentGap;
        if (attachmentEdge === "bottom") return strip.y - height - attachmentGap;
        var desired = centeredPlacement ? (parent.height - height) / 2 : alignment === "left" ? leadingOffset : alignment === "right" ? parent.height - height : (parent.height - height) / 2;
        return Math.max(edgeInsets[0], Math.min(parent.height - height - edgeInsets[2], desired));
    }
}
