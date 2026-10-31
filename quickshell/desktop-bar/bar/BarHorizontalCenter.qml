import ".."
import QtQuick
import Eitr as Eitr

Item {
    id: centerSection
    required property var host
    required property var barHost
    required property var hardwareStatusRef
    required property var mediaMenuRef
    required property var obsMenuRef
    required property var recordingMenuRef
    required property var verticalCalendarIconRef
    required property var verticalWeatherIconRef
    required property var workspacesRef
    readonly property alias centerInfoItem: centerInfo
    readonly property alias barCaptureItem: barCapture
    readonly property alias barPinItem: barPin
    readonly property alias mediaStripItem: mediaStrip
    readonly property alias barWeatherItem: barWeather
    readonly property alias calendarMenuItem: calendarMenu
    readonly property alias weatherMenuItem: weatherMenu
    anchors.fill: parent
    ClockButton {

        host: centerSection.host
        id: centerInfo
        anchors.alignWhenCentered: false
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: barHost.centeredLayout ? (barHost.leadingReveal - barHost.trailingReveal) / 2 : 0
        anchors.verticalCenterOffset: 0
        onClicked: barHost.togglePanel(calendarMenu)
    }

    CaptureIndicator {

        host: centerSection.host
        id: barCapture
        anchors.right: centerInfo.left
        anchors.rightMargin: shown ? (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 6) : 0
        anchors.verticalCenter: parent.verticalCenter
        recording: obsMenuRef.obsState.recording || obsMenuRef.obsState.streaming
        recordingPaused: obsMenuRef.obsState.paused && !obsMenuRef.obsState.streaming
        streaming: obsMenuRef.obsState.streaming
        dictating: centerSection.host.dictating
        transcribing: centerSection.host.transcribing
        dictationLevels: centerSection.host.dictationLevels
        onRecordingClicked: barHost.togglePanel(recordingMenuRef)
    }

    StatusIcon {

        host: centerSection.host
        id: barPin
        visible: barHost.centeredLayout && barHost.expanded
        anchors.right: barCapture.left
        anchors.rightMargin: barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 6
        anchors.verticalCenter: parent.verticalCenter
        icon: centerSection.host.barPinned ? "󰐃" : "󰐄"
        tooltip: centerSection.host.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
        open: true; clickable: true
        onClicked: centerSection.host.updateBarSetting("pinned", centerSection.host.barPinned ? "no" : "yes")
    }

    MediaStrip {
        id: mediaStrip
        mediaStyle: centerSection.host.barMediaStyle
        audioEnabled: centerSection.host.barVisible && !centerSection.host.verticalBar && barHost.expanded
        opacity: barHost.expanded ? 1 : 0
        enabled: barHost.expanded
        anchors.right: barHost.centeredLayout ? barPin.left : barCapture.left
        anchors.rightMargin: barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 12
        anchors.verticalCenter: parent.verticalCenter
        itemSpacing: barHost.centeredLayout ? barHost.itemGap : 1
        indicatorSpacing: barHost.centeredLayout ? barHost.itemGap : 6
        availableWidth: barHost.centeredLayout
            ? Math.max(0, barHost.width / 2 - centerInfo.width / 2 - workspacesRef.width - hardwareStatusRef.width - barPin.width - barCapture.width - barHost.itemGap * (barCapture.shown ? 5 : 4) - barHost.endPadding)
            : Math.max(0, centerInfo.x - hardwareStatusRef.mapToItem(centerInfo.parent, hardwareStatusRef.width, 0).x - (barHost.islandsLayout ? 2 * barHost.islandSpacing + (barCapture.shown ? barCapture.width + barHost.islandSpacing : 0) : 24))
        foreground: centerSection.host.fg
        background: centerSection.host.workspaceMenuBg
        onDetailsRequested: barHost.togglePanel(mediaMenuRef)
    }

    Item {
        anchors.left: centerInfo.right
        anchors.verticalCenter: centerInfo.verticalCenter
        width: barHost.notchLayout ? barHost.weatherReveal : (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 6) + barWeather.width
        height: barWeather.height
        clip: barHost.notchLayout
        WeatherWidget {
            host: centerSection.host
            id: barWeather
            x: parent.width - width
            opacity: barHost.expanded ? 1 : 0
            enabled: barHost.expanded && (!barHost.notchLayout || barHost.weatherExpanded)
            onClicked: barHost.togglePanel(weatherMenu)
        }
    }

    CalendarMenu {
        id: calendarMenu
        surfaceColor: centerSection.host.barBackground()
        target: centerSection.host.verticalBar ? verticalCalendarIconRef : centerInfo
        barEdge: centerSection.host.barEdge
        centered: true
        accent: centerSection.host.activeBg
        foreground: centerSection.host.fg
        background: centerSection.host.workspaceMenuBg
    }

    WeatherMenu {
        id: weatherMenu
        surfaceColor: centerSection.host.barBackground()
        target: centerSection.host.verticalBar ? verticalWeatherIconRef : centerInfo
        barEdge: centerSection.host.barEdge
        centered: true
        accent: centerSection.host.activeBg
        foreground: centerSection.host.fg
        background: centerSection.host.workspaceMenuBg
    }

}
