import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: root
    required property var catalog

    property string source: ""
    property bool iconOnly: false
    property bool plugin: false
    radius: DesktopStyle.radius(8)
    color: catalog.raised
    Image {
        anchors.centerIn: parent; width: parent.iconOnly ? 64 : parent.width; height: parent.iconOnly ? 64 : parent.height
        source: parent.source; fillMode: parent.iconOnly ? Image.PreserveAspectFit : Image.PreserveAspectCrop
        sourceSize: parent.iconOnly ? Qt.size(128, 128) : Qt.size(640, 360); asynchronous: true
        layer.enabled: GraphicsInfo.api !== GraphicsInfo.Software
        layer.effect: MultiEffect { maskEnabled: true; maskSource: imageMask }
    }
    StoreLabel { catalog: root.catalog; anchors.centerIn: parent; visible: parent.plugin && !parent.source; text: "󰏗"; font.pixelSize: 48; color: catalog.muted }
    Item { id: imageMask; anchors.fill: parent; layer.enabled: true; visible: false
        Rectangle { anchors.fill: parent; radius: parent.parent.radius; color: "white" }
    }
}
