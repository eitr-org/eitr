import QtQuick
import Quickshell
import Quickshell.Wayland
import "themes/eitr" as Design
import "UnlockPolicy.js" as Policy

Scope {
    id: effect
    property var screens: Quickshell.screens
    property bool authenticated: false
    property bool locked: true
    property bool secure: true
    property bool reduced: true
    readonly property var snapshots: captures.snapshots
    property var spectrum: []
    property string style: "bifrost"
    property bool expired: false
    UnlockSnapshots {
        id: captures
        authenticated: effect.authenticated
        reduced: effect.reduced
    }
    function resetCapture() { captures.resetCapture(); }
    function capture(sourceItem, screenName) { captures.capture(sourceItem, screenName); }
    // This deadline does not depend on shader loading or animation completion.
    Timer { interval: 1050; running: effect.authenticated; onTriggered: effect.expired = true }
    Variants {
        model: effect.screens
        PanelWindow {
            id: window
            required property var modelData
            readonly property var snapshot: effect.snapshots[modelData.name] || null
            property bool finished: false
            property real progress: 0
            screen: modelData
            color: "transparent"
            visible: !finished && Policy.eligible(effect.authenticated, effect.locked, effect.secure,
                                                 effect.reduced, frame.status === Image.Ready, effect.expired)
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "eitr-unlock-sweep"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            mask: Region {}
            onVisibleChanged: if (visible) animation.start()
            // The last lockscreen frame, shown only outside the opening Bifröst gate.
            Image {
                id: frame
                visible: false
                width: window.width; height: window.height
                source: window.snapshot ? window.snapshot.url : ""
                fillMode: Image.Stretch
            }
            Item {
                width: sweep.leftEdge; height: window.height; clip: true
                Image { width: window.width; height: window.height; source: frame.source; fillMode: Image.Stretch }
            }
            Item {
                x: sweep.rightEdge; width: window.width - x; height: window.height; clip: true
                Image { x: -parent.x; width: window.width; height: window.height; source: frame.source; fillMode: Image.Stretch }
            }
            Design.Sweep { id: sweep; anchors.fill: parent; progress: window.progress; spectrum: effect.spectrum; style: effect.style; source: frame }
            NumberAnimation { id: animation; target: window; property: "progress"; from: 0; to: 1; duration: 820; onFinished: window.finished = true }
        }
    }
}
