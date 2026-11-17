pragma ComponentBehavior: Bound
import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// One zone bucket in Settings > Desktop Bar > Icons: holds draggable and keyboard-movable icon chips.
Rectangle {
    id: zoneCard
    required property var page
    required property string zoneId
    required property string title
    required property string caption
    required property var items
    required property color foreground
    required property color accent
    required property color gold
    required property Item overlayLayer
    readonly property bool isDropTarget: page.dragActive && page.dropZone === zoneId

    property point indicatorPos: Qt.point(4, 4)
    property real indicatorHeight: 24

    Component.onCompleted: page.registerZone(zoneId, zoneCard)
    Component.onDestruction: page.unregisterZone(zoneId, zoneCard)

    function flowChips() {
        const list = [];
        for (const child of chipFlow.children || []) {
            if (child.chipId !== undefined && child.visible) list.push(child);
        }
        return list;
    }

    function computeDropIndex(layerPoint) {
        const pt = overlayLayer.mapToItem(chipFlow, layerPoint.x, layerPoint.y);
        const chips = flowChips();
        const sourceIdx = chips.findIndex(chip => chip.chipId === page.draggingId);
        if (!chips.length) {
            indicatorPos = Qt.point(2, 4);
            indicatorHeight = 24;
            return 0;
        }
        const rows = [];
        for (let i = 0; i < chips.length; i++) {
            const chip = chips[i];
            let row = rows.find(entry => Math.abs(entry.y - chip.y) < chip.height * 0.5);
            if (!row) {
                row = {y: chip.y, height: chip.height, items: []};
                rows.push(row);
            }
            row.items.push({index: i, chip: chip});
        }
        let targetRow = rows[0];
        let bestRowDist = Math.abs(pt.y - (rows[0].y + rows[0].height / 2));
        for (const row of rows) {
            const dist = Math.abs(pt.y - (row.y + row.height / 2));
            if (dist < bestRowDist) {
                bestRowDist = dist;
                targetRow = row;
            }
        }
        let rawIdx = targetRow.items[targetRow.items.length - 1].index + 1;
        let barX = targetRow.items[targetRow.items.length - 1].chip.x + targetRow.items[targetRow.items.length - 1].chip.width + 2;
        const barY = targetRow.y + 3;
        for (const entry of targetRow.items) {
            if (pt.x < entry.chip.x + entry.chip.width / 2) {
                rawIdx = entry.index;
                barX = entry.chip.x - 4;
                break;
            }
        }
        indicatorPos = Qt.point(Math.max(0, Math.min(chipFlow.width - 2, barX)), barY);
        indicatorHeight = Math.max(20, targetRow.height - 6);
        return sourceIdx >= 0 && rawIdx > sourceIdx ? rawIdx - 1 : rawIdx;
    }

    objectName: "bar-icons-zone-" + zoneId
    implicitHeight: zoneInner.implicitHeight + 20
    radius: DesktopStyle.radius(PanelStyle.controlRadius)
    color: isDropTarget ? Qt.alpha(gold, 0.08) : Qt.alpha(foreground, 0.03)
    border.width: 1
    border.color: isDropTarget ? gold : Qt.alpha(foreground, 0.12)

    Column {
        id: zoneInner
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 8

        Row {
            width: parent.width
            spacing: 8
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: zoneCard.title
                color: zoneCard.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                font.bold: true
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: zoneCard.caption
                color: Qt.alpha(zoneCard.foreground, 0.62)
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
        }

        Item {
            width: parent.width
            height: Math.max(36, chipFlow.implicitHeight)

            Text {
                anchors.centerIn: parent
                visible: zoneCard.items.length === 0
                text: Eitr.I18n.tr("Drop icons here")
                color: Qt.alpha(zoneCard.foreground, 0.45)
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }

            Flow {
                id: chipFlow
                width: parent.width
                spacing: 6

                Repeater {
                    model: zoneCard.items
                    delegate: Rectangle {
                        id: chip
                        required property var modelData
                        readonly property string chipId: modelData.id
                        readonly property bool isGrabbed: zoneCard.page.grabbedId === chipId
                        readonly property bool isDraggingSource: zoneCard.page.dragActive && zoneCard.page.draggingId === chipId
                        readonly property bool isHovered: chipArea.containsMouse

                        objectName: "bar-icon-chip-" + chipId
                        width: chipRow.implicitWidth + 18
                        height: 32
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        opacity: isDraggingSource ? 0.3 : 1
                        color: isGrabbed ? Qt.alpha(zoneCard.gold, 0.22)
                            : isHovered ? Qt.alpha(zoneCard.foreground, 0.12) : Qt.alpha(zoneCard.foreground, 0.06)
                        border.width: isGrabbed || activeFocus ? 1.5 : 1
                        border.color: isGrabbed ? zoneCard.gold : activeFocus ? zoneCard.accent : Qt.alpha(zoneCard.foreground, isHovered ? 0.28 : 0.15)
                        activeFocusOnTab: true

                        onIsHoveredChanged: {
                            if (isHovered) zoneCard.page.hoveredId = chipId;
                            else if (zoneCard.page.hoveredId === chipId) zoneCard.page.hoveredId = "";
                        }

                        Keys.onPressed: function(event) {
                            const key = event.key;
                            if (key === Qt.Key_Return || key === Qt.Key_Enter || key === Qt.Key_Space) {
                                zoneCard.page.toggleGrab(chipId);
                                event.accepted = true;
                            } else if (key === Qt.Key_Escape && isGrabbed) {
                                zoneCard.page.cancelInteraction();
                                event.accepted = true;
                            } else if (key === Qt.Key_Left || key === Qt.Key_Right || key === Qt.Key_Up || key === Qt.Key_Down) {
                                const dir = key === Qt.Key_Left ? "left" : key === Qt.Key_Right ? "right" : key === Qt.Key_Up ? "up" : "down";
                                if (isGrabbed) zoneCard.page.moveGrabbed(chipId, dir);
                                else zoneCard.page.moveFocusAdjacent(chipId, dir);
                                event.accepted = true;
                            }
                        }

                        Row {
                            id: chipRow
                            anchors.centerIn: parent
                            spacing: 6
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: chip.modelData.glyph || "󰐱"
                                color: chip.isGrabbed ? zoneCard.gold : zoneCard.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: 14
                                font.bold: true
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: chip.modelData.title
                                color: zoneCard.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                        }

                        MouseArea {
                            id: chipArea
                            anchors.fill: parent
                            hoverEnabled: true
                            preventStealing: true
                            cursorShape: zoneCard.page.dragActive && zoneCard.page.draggingId === chip.chipId ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                            property point pressPoint: Qt.point(0, 0)
                            onPressed: function(mouse) {
                                pressPoint = Qt.point(mouse.x, mouse.y);
                                chip.forceActiveFocus();
                                zoneCard.page.beginDrag(chip.modelData, chipArea, pressPoint);
                            }
                            onPositionChanged: function(mouse) {
                                if (!pressed) return;
                                if (!zoneCard.page.dragActive && (Math.abs(mouse.x - pressPoint.x) > 6 || Math.abs(mouse.y - pressPoint.y) > 6)) {
                                    zoneCard.page.updateDrag(chipArea, Qt.point(mouse.x, mouse.y));
                                } else if (zoneCard.page.dragActive) {
                                    zoneCard.page.updateDrag(chipArea, Qt.point(mouse.x, mouse.y));
                                }
                            }
                            onReleased: zoneCard.page.finishDrag()
                            onCanceled: zoneCard.page.clearDrag()
                        }
                    }
                }
            }

            Rectangle {
                visible: zoneCard.isDropTarget
                x: zoneCard.indicatorPos.x
                y: zoneCard.indicatorPos.y
                width: 2.5
                height: zoneCard.indicatorHeight
                radius: 1
                color: zoneCard.gold
                z: 10
            }
        }
    }
}
