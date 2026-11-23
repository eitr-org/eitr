import ".."
import QtQuick
import Eitr as Eitr
import "../MediaModel.js" as MediaModel

Item {
    required property var host
    required property var barHost
    required property var barWeatherRef
    required property var calendarMenuRef
    required property var mediaMenuRef
    required property var mediaStripRef
    required property var obsMenuRef
    required property var recordingMenuRef
    required property var weatherMenuRef
    readonly property alias verticalMiddleItem: verticalMiddle
    readonly property alias verticalMediaItem: verticalMedia
    readonly property alias verticalCaptureItem: verticalCapture
    readonly property alias verticalPinItem: verticalPin
    readonly property alias verticalCalendarIconItem: verticalCalendarIcon
    readonly property alias verticalWeatherIconItem: verticalWeatherIcon

    readonly property alias clockPluginsItem: clockPlugins
    id: verticalMiddle
    anchors.alignWhenCentered: false
    anchors.horizontalCenterOffset: 0
    anchors.centerIn: parent
    anchors.verticalCenterOffset: barHost.centeredLayout ? (barHost.leadingReveal - barHost.trailingReveal) / 2 : 0
    width: parent.width
    height: 40
    Column {
        id: verticalMedia
        anchors.horizontalCenterOffset: 0
        anchors.bottom: barHost.centeredLayout ? verticalPin.top : verticalCapture.top
        anchors.bottomMargin: barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: barHost.centeredLayout ? barHost.itemGap : 2
        visible: mediaStripRef.present && barHost.expanded
        MediaIndicator {
            anchors.horizontalCenter: parent.horizontalCenter
            rotation: 90
            style: verticalMiddle.host.barMediaStyle
            playing: mediaStripRef.playing
            active: verticalMiddle.host.barVisible && verticalMiddle.host.verticalBar && barHost.expanded
            foreground: verticalMiddle.host.barFg
            background: verticalMiddle.host.workspaceMenuBg
            title: mediaStripRef.title
            onDetailsRequested: barHost.toggleKind("media")
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: "󰒮"; tooltip: Eitr.I18n.tr("Previous"); open: true
            clickable: !!mediaStripRef.player && mediaStripRef.player.canGoPrevious
            onClicked: mediaStripRef.player.previous()
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: MediaModel.playGlyph(mediaStripRef.player, mediaStripRef.playing); tooltip: mediaStripRef.title; open: true
            clickable: MediaModel.canPlayControl(mediaStripRef.player)
            onClicked: MediaModel.playControl(mediaStripRef.player)
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: "󰒭"; tooltip: Eitr.I18n.tr("Next"); open: true
            clickable: !!mediaStripRef.player && mediaStripRef.player.canGoNext
            onClicked: mediaStripRef.player.next()
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: "󰝚"; tooltip: Eitr.I18n.tr("Media"); open: true; clickable: true
            onClicked: barHost.toggleKind("media")
        }
    }
    CaptureIndicator {
        host: verticalMiddle.host
        id: verticalCapture
        anchors.bottom: clockPlugins.height > 0 ? clockPlugins.top : verticalCalendarIcon.top
        anchors.horizontalCenterOffset: 0
        anchors.bottomMargin: (shown ? (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3) : 0)
            + (barHost.islandsLayout ? (clockPlugins.height <= 0 ? (barHost.islandSurfaces ? barHost.islandSurfaces.aroundClock : 0) : (barHost.islandSurfaces ? barHost.islandSurfaces.beforeClockPlugins : 0)) : 0)
        anchors.horizontalCenter: parent.horizontalCenter
        recording: obsMenuRef.obsState.recording || obsMenuRef.obsState.streaming
        recordingPaused: obsMenuRef.obsState.paused && !obsMenuRef.obsState.streaming
        streaming: obsMenuRef.obsState.streaming
        dictating: verticalMiddle.host.dictating
        transcribing: verticalMiddle.host.transcribing
        dictationLevels: verticalMiddle.host.dictationLevels
        onRecordingClicked: barHost.togglePanel(recordingMenuRef)
        activity: barHost.clockActivity
        vertical: true
        onMeetingClicked: calendarMenuRef.showDay(new Date())
        onTimerClicked: barHost.showClock(barHost.clockActivity ? barHost.clockActivity.timerPage : "timers")
        onBellClicked: barHost.showKind("notifications")
        // Stacked in the vertical bar's column, the dot is centred in every layout.
        centered: true
    }
    VerticalBarIcon {
        host: verticalMiddle.host
        id: verticalPin
        anchors.horizontalCenterOffset: 0
        anchors.bottom: verticalCapture.top
        anchors.bottomMargin: barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3
        anchors.horizontalCenter: parent.horizontalCenter
        icon: verticalMiddle.host.barPinned ? "󰐃" : "󰐄"
        tooltip: verticalMiddle.host.barPinned ? Eitr.I18n.tr("Unpin bar") : Eitr.I18n.tr("Pin bar open")
        visible: barHost.centeredLayout && barHost.expanded
        open: true; clickable: true
        onClicked: verticalMiddle.host.updateBarSetting("pinned", verticalMiddle.host.barPinned ? "no" : "yes")
    }
    BarZoneItems {
        id: clockPlugins
        host: verticalMiddle.host
        barHost: verticalMiddle.barHost
        zone: "clockStart"
        vertical: true
        observing: !barHost.dynamicLayout
        slotSpacing: barHost.itemGap
        open: !barHost.dropLayout && barHost.expanded
        clipReveal: true
        reveal: barHost.dynamicLayout ? 0 : 1
        Behavior on reveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
        opacity: reveal
        enabled: opacity > 0
        anchors.bottom: verticalCalendarIcon.top
        anchors.bottomMargin: barHost.islandsLayout ? barHost.islandSpacing + (barHost.islandSurfaces ? barHost.islandSurfaces.aroundClock : 0) : barHost.centeredLayout ? barHost.itemGap : 3
        anchors.horizontalCenter: verticalCalendarIcon.horizontalCenter
        onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
    }

    ClockButton {
        host: verticalMiddle.host
        id: verticalCalendarIcon
        anchors.alignWhenCentered: false
        activity: barHost.clockActivity
        anchors.centerIn: parent
        // Drop keeps the time at the screen's centre while its pill grows to one side.
        anchors.verticalCenterOffset: barHost.dropLayout ? (barHost.dropSurfaces ? barHost.dropSurfaces.timeOffset : 0) : 0
        compact: true
        onClicked: barHost.togglePanel(barHost.dropLayout ? barHost.panel("dashboard") : calendarMenuRef)
        onRightClicked: if (barHost.dropLayout) barHost.panel("dashboard").show("controls")
    }
    Item {
        anchors.top: verticalCalendarIcon.bottom
        anchors.topMargin: barHost.islandsLayout ? (barHost.islandSurfaces ? barHost.islandSurfaces.aroundClock : 0) : 0
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
        height: barHost.dropLayout || verticalWeatherIcon.height <= 0 ? 0 : barHost.dynamicLayout ? 0 : barHost.notchLayout ? barHost.weatherReveal : (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3) + verticalWeatherIcon.height
        clip: barHost.dropLayout || barHost.notchLayout || barHost.dynamicLayout
        BarZoneItems {
            id: verticalWeatherIcon
            host: verticalMiddle.host
            barHost: verticalMiddle.barHost
            zone: "clockEnd"
            vertical: true
            observing: !barHost.dynamicLayout
            y: parent.height - height
            anchors.horizontalCenter: parent.horizontalCenter
            slotSpacing: barHost.itemGap
            open: !barHost.dropLayout && barHost.expanded
            onPanelRequested: function(plugin, panel, target) { barHost.openPluginPanel(plugin, panel, target); }
        }
    }
}
