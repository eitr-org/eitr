import ".."
pragma ComponentBehavior: Bound
import QtQuick
import "../PanelStyle.js" as PanelStyle

// The two dashboard rails share surfaces, motion and clipped per-pill input regions.
Item {
    id: rail
    required property var entries
    required property color foreground
    required property color background
    required property color accent
    property bool horizontal: false
    property bool trailing: false
    property bool opened: false
    property bool ready: false
    property string current: ""
    property real gap: 20
    property real pillSize: 32
    property string clockFormat: PluginRegistry.clockFormat
    readonly property real naturalLength: entries.length * pillSize + Math.max(0, entries.length - 1) * gap
    // Bumped as pills are created and destroyed, so the click areas follow them.
    property int pillRevision: 0
    readonly property var inputSurfaces: {
        pillRevision;
        const result = [];
        for (let index = 0; index < pills.count; index++) {
            // A pill being created or destroyed has no item yet.
            const pill = pills.itemAt(index);
            if (pill && pill.inputTarget) result.push(pill.inputTarget);
        }
        return result;
    }
    function ensureCurrent() {
        const index = entries.findIndex(entry => !entry.plugin && entry.id === current);
        if (index < 0) return;
        const start = index * (pillSize + gap), length = horizontal ? width : height;
        const offset = horizontal ? viewport.contentX : viewport.contentY;
        const next = Math.max(0, Math.min(offset, start), start + pillSize - length);
        if (horizontal) viewport.contentX = next;
        else viewport.contentY = next;
    }
    onCurrentChanged: Qt.callLater(ensureCurrent)
    onEntriesChanged: Qt.callLater(ensureCurrent)
    onWidthChanged: Qt.callLater(ensureCurrent)
    onHeightChanged: Qt.callLater(ensureCurrent)
    signal chosen(string page)
    signal panelRequested(string plugin, string panel)
    visible: entries.length > 0

    Flickable {
        id: viewport
        anchors.fill: parent
        clip: true
        contentWidth: rail.horizontal ? rail.naturalLength : width
        contentHeight: rail.horizontal ? height : rail.naturalLength
        flickableDirection: rail.horizontal ? Flickable.HorizontalFlick : Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds
        Repeater {
            id: pills
            onItemAdded: rail.pillRevision++
            onItemRemoved: rail.pillRevision++
            model: rail.entries
            Item {
                id: slot
                required property var modelData
                required property int index
                x: rail.horizontal ? index * (rail.pillSize + rail.gap) : 0
                y: rail.horizontal ? 0 : index * (rail.pillSize + rail.gap)
                width: rail.pillSize; height: rail.pillSize
                property real reveal: 0
                readonly property bool selected: !modelData.plugin && rail.current === modelData.id
                readonly property color ink: selected ? PanelStyle.readableInk(rail.accent, rail.foreground, rail.background) : rail.foreground
                function animate() {
                    motion.stop();
                    closing.stop();
                    if (DesktopStyle.reduceMotion) { reveal = rail.opened ? 1 : 0; return; }
                    if (!rail.opened) { closing.restart(); return; }
                    if (rail.ready) motion.restart();
                }
                Component.onCompleted: animate()
                Connections {
                    target: rail
                    function onOpenedChanged() { slot.animate(); }
                    function onReadyChanged() { slot.animate(); }
                }
                Connections { target: DesktopStyle; function onReduceMotionChanged() { slot.animate(); } }
                SequentialAnimation {
                    id: motion
                    PauseAnimation { duration: 20 + Math.min(slot.index, 7) * 12 }
                    NumberAnimation { target: slot; property: "reveal"; to: 1; duration: 140; easing.type: Easing.OutCubic }
                }
                NumberAnimation { id: closing; target: slot; property: "reveal"; to: 0; duration: 140; easing.type: Easing.InCubic }
                Rectangle {
                    id: pill
                    readonly property real travel: (1 - slot.reveal) * (rail.pillSize + rail.gap) * (rail.trailing ? -1 : 1)
                    x: rail.horizontal ? 0 : travel
                    y: rail.horizontal ? travel : 0
                    width: slot.width; height: slot.height; radius: height / 2
                    color: slot.selected ? rail.accent : rail.background
                    opacity: slot.reveal
                    PanelButton {
                        anchors.fill: parent
                        visible: !slot.modelData.plugin
                        icon: true; iconSize: 17; text: slot.modelData.glyph || ""
                        foreground: slot.ink; color: "transparent"; radius: height / 2
                        Accessible.name: slot.modelData.title
                        Accessible.role: Accessible.PageTab
                        Accessible.selected: slot.selected
                        onClicked: rail.chosen(slot.modelData.id)
                    }
                    Loader {
                        anchors.fill: parent
                        active: !!slot.modelData.plugin
                        sourceComponent: PluginComponent {
                            entry: slot.modelData
                            active: rail.opened && rail.ready && slot.inputTarget.visible
                            observing: rail.opened && rail.ready && slot.inputTarget.visible
                            iconSlot: true; surface: false
                            verticalBar: rail.horizontal
                            clockFormat: rail.clockFormat
                            foreground: rail.foreground; background: rail.background; accent: rail.accent
                            onPanelRequested: function(plugin, panel) { rail.panelRequested(plugin, panel); }
                        }
                        id: plugin
                    }
                    HoverHandler { id: hover }
                    BarTooltip {
                        target: pill; hovered: hover.hovered && rail.opened
                        text: slot.modelData.title + (plugin.item && plugin.item.detail ? " · " + plugin.item.detail : "")
                        foreground: rail.foreground; background: rail.background
                    }
                }
                // The mask follows only the visible intersection, including during a flick.
                property Item inputTarget: Item {
                    parent: rail
                    readonly property real pillLeft: slot.x + pill.x - viewport.contentX
                    readonly property real pillTop: slot.y + pill.y - viewport.contentY
                    x: Math.max(0, pillLeft); y: Math.max(0, pillTop)
                    width: Math.max(0, Math.min(rail.width, pillLeft + pill.width) - x)
                    height: Math.max(0, Math.min(rail.height, pillTop + pill.height) - y)
                    property real radius: rail.pillSize / 2
                    visible: rail.visible && slot.reveal > 0 && width > 0 && height > 0
                }
            }
        }
    }
}
