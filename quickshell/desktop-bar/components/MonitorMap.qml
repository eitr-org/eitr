import ".."
import QtQuick
import Eitr as Eitr
import "../MonitorGeometry.js" as Geometry
import "../PanelStyle.js" as PanelStyle

Item {
    id: map
    property var monitors: []
    property var settings: []
    property var pending: null
    property string primary: ""
    property string selected: ""
    required property color foreground
    property color background: "transparent"
    property color accent: foreground
    property color gold: accent
    property bool compact: false
    signal selectedMonitor(string name)
    implicitHeight: compact ? 160 : 230
    readonly property var rectangles: Geometry.fit(Geometry.screens(monitors, settings, pending), width, height, 16)
    Repeater {
        model: map.rectangles
        Rectangle {
            id: screen
            required property var modelData
            x: modelData.x; y: modelData.y
            width: modelData.width; height: modelData.height
            radius: DesktopStyle.radius(6)
            clip: true
            opacity: modelData.disabled ? 0.35 : 1
            color: Qt.alpha(map.foreground, modelData.name === map.selected ? 0.18 : 0.06)
            border.width: modelData.pending ? 0 : modelData.name === map.primary || activeFocus ? 2 : 1
            border.color: modelData.name === map.primary ? map.gold : activeFocus ? map.accent : Qt.alpha(map.foreground, 0.4)
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: modelData.name + " " + modelData.model + " " + modelData.resolution
            Keys.onReturnPressed: map.selectedMonitor(modelData.name)
            Keys.onSpacePressed: map.selectedMonitor(modelData.name)
            Canvas {
                anchors.fill: parent
                visible: screen.modelData.pending
                property var rectangle: screen.modelData
                property color ink: screen.modelData.name === map.primary ? map.gold : map.foreground
                onRectangleChanged: requestPaint()
                onInkChanged: requestPaint()
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d"); context.reset();
                    context.strokeStyle = ink; context.lineWidth = 2;
                    context.setLineDash([5, 4]); context.beginPath();
                    context.roundedRect(1, 1, width - 2, height - 2, 6, 6); context.stroke();
                }
            }
            Column {
                anchors.centerIn: parent
                width: Math.max(0, parent.width - 12)
                spacing: 3
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: screen.modelData.name + (map.compact && screen.modelData.model ? " · " + screen.modelData.model : ""); color: map.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; elide: Text.ElideRight }
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; visible: !map.compact && text !== ""; text: screen.modelData.model; color: map.foreground; font.family: DesktopFonts.family; font.pixelSize: 11; elide: Text.ElideRight }
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: screen.modelData.resolution; color: map.foreground; font.family: DesktopFonts.family; font.pixelSize: 11; elide: Text.ElideRight }
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; visible: screen.modelData.name === map.primary; text: Eitr.I18n.tr("Main"); color: map.gold; font.family: DesktopFonts.family; font.pixelSize: 11 }
            }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { screen.forceActiveFocus(); map.selectedMonitor(screen.modelData.name); } }
        }
    }
}
