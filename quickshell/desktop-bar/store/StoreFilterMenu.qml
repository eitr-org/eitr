import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: control
    required property var catalog
    property alias expanded: menu.visible
    property alias popup: menu
    PanelButton {
        anchors.fill: parent
        foreground: catalog.foreground
        icon: true; text: "\uf0b0"
        Accessible.name: Eitr.I18n.tr("Filters")
        onClicked: menu.open()
        Rectangle {
            anchors.right: parent.right; anchors.top: parent.top
            width: 6; height: 6; radius: 3; color: catalog.gold
            visible: catalog.filtersActive
        }
    }
    Popup {
        id: menu
        x: control.width - width; y: control.height + 4
        width: 290
        height: Math.min(column.implicitHeight + 8, control.Window.height - control.mapToItem(null, 0, 0).y - control.height - 16)
        padding: 4; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: DesktopStyle.motionDuration(120) } }
        exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: DesktopStyle.motionDuration(90) } }
        background: ChoiceListSurface { foreground: catalog.foreground; surface: catalog.background }
        contentItem: Flickable {
            contentHeight: column.implicitHeight; clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            Column {
                id: column; width: parent.width; spacing: 6
                Repeater {
                    model: catalog.filterGroups
                    Column {
                        id: group
                        required property var modelData
                        width: column.width; spacing: 4
                        StoreLabel {
                            catalog: control.catalog; width: parent.width
                            leftPadding: 10; topPadding: 4
                            text: Eitr.I18n.tr(group.modelData.label)
                            color: catalog.muted
                        }
                        Repeater {
                            model: group.modelData.options
                            PanelButton {
                                required property var modelData
                                width: group.width; height: PanelStyle.selectionRowHeight
                                foreground: selected ? catalog.gold : catalog.foreground
                                text: Eitr.I18n.tr(modelData.label)
                                textAlignment: Text.AlignLeft; textInset: 10
                                readonly property var value: group.modelData.id === "source" ? catalog.sourceFilter : catalog.filterValue(group.modelData)
                                selected: group.modelData.multiple ? value.includes(modelData.id) : value === modelData.id
                                color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(selected, pointer.hovered))
                                border.width: PanelStyle.selectionBorderWidth(selected)
                                border.color: Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
                                Accessible.role: group.modelData.multiple ? Accessible.CheckBox : Accessible.RadioButton
                                Accessible.checked: selected
                                HoverHandler { id: pointer }
                                onClicked: catalog.chooseFilter(group.modelData, modelData.id)
                            }
                        }
                    }
                }
            }
        }
    }
}
