import ".."
import QtQuick
import QtQml.Models
import Quickshell

Region {
    id: mask
    required property var surfaces
    width: 0
    height: 0
    property Instantiator pills: Instantiator {
        model: mask.surfaces
        delegate: Region {
            required property var modelData
            item: modelData.visible ? modelData : null
            radius: Math.min(modelData.radius, modelData.width / 2, modelData.height / 2)
        }
        onObjectAdded: function(index, object) { mask.regions.push(object); }
        onObjectRemoved: function(index, object) {
            var entries = mask.regions;
            var position = entries.indexOf(object);
            if (position >= 0) entries.splice(position, 1);
        }
    }
}
