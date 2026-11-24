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
        width: Math.min(290, control.Window.width - 16)
        margins: 8
        height: Math.min(column.implicitHeight + topPadding + bottomPadding, control.Window.height - 16)
        padding: 12; focus: true
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
                        required property int index
                        width: column.width; spacing: 4
                        Rectangle {
                            visible: group.index > 0
                            width: parent.width; height: 1
                            color: Qt.alpha(catalog.foreground, PanelStyle.dividerAlpha)
                        }
                        Loader {
                            active: !group.modelData.multiple
                            visible: active
                            width: parent.width
                            sourceComponent: ChoiceDropdown {
                                objectName: "store-filter-" + group.modelData.id
                                foreground: catalog.foreground
                                background: catalog.background
                                floatingLabel: Eitr.I18n.tr(group.modelData.label)
                                choices: group.modelData.options
                                current: catalog.filterValue(group.modelData)
                                popup.z: menu.z + 1
                                onChosen: value => catalog.chooseFilter(group.modelData, value)
                                Connections {
                                    target: menu
                                    function onAboutToHide() { expanded = false; }
                                }
                            }
                        }
                        StoreLabel {
                            visible: group.modelData.multiple
                            catalog: control.catalog; width: parent.width
                            leftPadding: 10; topPadding: 4
                            text: Eitr.I18n.tr(group.modelData.label)
                            color: catalog.muted
                        }
                        Repeater {
                            model: group.modelData.multiple ? group.modelData.options : []
                            PanelButton {
                                required property var modelData
                                objectName: "store-filter-" + group.modelData.id + "-" + modelData.id
                                width: group.width; height: PanelStyle.selectionRowHeight
                                foreground: catalog.foreground
                                text: Eitr.I18n.tr(modelData.label)
                                textAlignment: Text.AlignLeft; textInset: 10
                                leadingIcon: selected ? "\u{F0132}" : "\u{F0131}"
                                readonly property var value: catalog.filterValue(group.modelData)
                                selected: value.includes(modelData.id)
                                color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(selected, pointer.hovered))
                                border.width: PanelStyle.selectionBorderWidth(selected)
                                border.color: Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
                                Accessible.role: Accessible.CheckBox
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
