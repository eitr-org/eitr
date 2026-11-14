import ".."
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr

// The bar's left group: logo, Overview and workspaces, then the AI Usage, Hardware and
// Idle Lock icons. The panels they open stay with the bar, which passes them in.
RowLayout {
    id: group
    property var host
    property var barWindow
    property var styleMenu
    property var aiPanel
    property var hardwarePanel
    readonly property alias workspaces: workspaceRow
    readonly property alias workspaceButtonRow: workspaceButtons
    readonly property alias hardwareStatus: statusRow
    readonly property alias controlCenterLogo: logo
    readonly property alias overviewIcon: overview
    readonly property alias aiIcon: aiButton
    readonly property alias hardwareIcon: hardwareButton
    readonly property alias idleLockIcon: idleLockButton
    spacing: 0
    Row {
        id: workspaceRow
        // The fade lives in shownOpacity, so an Islands pill hiding this row under its card
        // overrides a plain binding and gets it back intact.
        property real shownOpacity: barWindow.expanded ? 1 : 0
        opacity: shownOpacity
        enabled: barWindow.expanded
        Behavior on shownOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }

        spacing: host.workspaceItemSpacing
        Layout.alignment: Qt.AlignVCenter

        EitrLogo {
            id: logo
            foreground: host.fg; background: host.workspaceMenuBg
            slotWidth: host.workspaceItemSize
            anchors.verticalCenter: parent.verticalCenter
            onClicked: barWindow.toggleControlCenter()
        }
        Item { width: barWindow.islandsLayout ? barWindow.islandSpacing - 2 * host.workspaceItemSpacing + barWindow.islandSurfaces.afterLogo : 0; height: 1; visible: barWindow.islandsLayout }
        StatusIcon {
            host: group.host
            id: overview
            icon: "󰕮"; tooltip: Eitr.I18n.tr("Overview"); open: true; clickable: true
            slotWidth: host.workspaceItemSize
            anchors.verticalCenter: parent.verticalCenter
            onClicked: barWindow.toggleOverview()
        }
        // The workspace buttons alone: an Islands workspaces pill hides these under its
        // card without hiding the logo, which shares this row.
        Row {
            id: workspaceButtons
            spacing: host.workspaceItemSpacing
            anchors.verticalCenter: parent.verticalCenter
            Repeater {
                model: host.workspaceRows(barWindow.screen).length

                BarButton {

                    host: group.host
                    text: host.workspaceLabel(index, barWindow.screen)
                    tooltip: active ? "" : host.workspaceApps(host.workspaceEntry(index, barWindow.screen).id)
                    visualStyle: host.workspaceStyle
                    active: host.workspaceActive(index + 1, barWindow.screen)
                    width: host.workspaceItemSize
                    buttonHeight: host.workspaceItemSize
                    anchors.verticalCenter: parent.verticalCenter
                    fontSize: 14
                    cornerRadius: 6
                    textOffsetY: 0
                    onClicked: host.focusWorkspace(host.workspaceEntry(index, barWindow.screen).number, barWindow.screen)
                    onRightClicked: barWindow.togglePanel(styleMenu)
                }

            }
        }


    }

    Row {
        id: statusRow
        // The fade lives in shownOpacity, so an Islands pill hiding this row under its card
        // overrides a plain binding and gets it back intact.
        property real shownOpacity: barWindow.expanded ? 1 : 0
        opacity: shownOpacity
        enabled: barWindow.expanded
        Behavior on shownOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(180) } }
        Layout.alignment: Qt.AlignVCenter
        Layout.leftMargin: barWindow.islandsLayout ? barWindow.islandSpacing + barWindow.islandSurfaces.afterWorkspaces : host.workspaceItemSpacing
        spacing: host.workspaceItemSpacing

        StatusIcon {

            host: group.host
            id: aiButton
            slotWidth: host.workspaceItemSize
            icon: ""
            iconSize: 16
            tooltip: Eitr.I18n.tr("AI Usage")
            open: true
            clickable: true
            onClicked: barWindow.togglePanel(aiPanel)
        }

        StatusIcon {

            host: group.host
            id: hardwareButton
            slotWidth: host.workspaceItemSize
            icon: "󰍛"
            iconSize: 18
            tooltip: Eitr.I18n.tr("Hardware")
            open: true
            clickable: true
            onClicked: barWindow.togglePanel(hardwarePanel)
        }

        // A plain switch: a click turns automatic idle locking on or off.
        StatusIcon {
            host: group.host
            id: idleLockButton
            slotWidth: host.workspaceItemSize
            icon: host.idleLockGlyph
            iconSize: 17
            tooltip: host.idleLockTooltip
            open: true
            clickable: true
            onClicked: host.switchIdleLock()
        }
        PluginBarItems {
            placementSlot: "start"
            clockFormat: host.barClock
            foreground: host.fg; background: host.barBackground(); accent: host.activeBg
            open: !barWindow.dropLayout && barWindow.expanded
            observing: !barWindow.dynamicLayout || barWindow.dynamicSurfaces.leadingIsland.expanded
            slotSize: host.workspaceItemSize; slotSpacing: host.workspaceItemSpacing
            onPanelRequested: function(plugin, panel, target) { barWindow.openPluginPanel(plugin, panel, target); }
        }
    }
}
