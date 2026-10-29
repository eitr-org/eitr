import QtQuick
import QtQml.Models
import Quickshell
import "EdgeSlopes.js" as EdgeSlopes

Region {
    id: mask
    required property Item surface
    required property string edge
    required property real depth
    required property real bendRound
    readonly property bool vertical: edge === "left" || edge === "right"
    readonly property real length: vertical ? surface.height : surface.width
    readonly property point origin: surface.parent.mapToItem(null, surface.x, surface.y)
    width: 0
    height: 0
    // One-pixel slices follow the same rounded slope as the painted surface.
    property Instantiator slices: Instantiator {
        model: mask.surface.visible ? Math.ceil(mask.depth) : 0
        delegate: Region {
            required property int index
            readonly property real inset: EdgeSlopes.boundary(mask.depth + mask.bendRound,
                mask.depth, mask.bendRound, index + 0.5)
            readonly property real across: mask.edge === "bottom" || mask.edge === "right" ? mask.depth - index - 1 : index
            x: Math.ceil(mask.origin.x + (mask.vertical ? across : inset))
            y: Math.ceil(mask.origin.y + (mask.vertical ? inset : across))
            width: mask.vertical ? 1 : Math.max(0, Math.floor(mask.length - 2 * inset))
            height: mask.vertical ? Math.max(0, Math.floor(mask.length - 2 * inset)) : 1
        }
        onObjectAdded: function(index, object) { mask.regions.push(object); }
        onObjectRemoved: function(index, object) {
            var entries = mask.regions;
            var position = entries.indexOf(object);
            if (position >= 0) entries.splice(position, 1);
        }
    }
}
