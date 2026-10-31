import QtQuick
import Eitr as Eitr

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
        visible: mediaStripRef.player !== null && barHost.expanded
        MediaIndicator {
            anchors.horizontalCenter: parent.horizontalCenter
            rotation: 90
            style: verticalMiddle.host.barMediaStyle
            playing: mediaStripRef.playing
            active: verticalMiddle.host.barVisible && verticalMiddle.host.verticalBar && barHost.expanded
            foreground: verticalMiddle.host.fg
            background: verticalMiddle.host.workspaceMenuBg
            title: mediaStripRef.title
            onDetailsRequested: barHost.togglePanel(mediaMenuRef)
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: "󰒮"; tooltip: Eitr.I18n.tr("Previous"); open: true
            clickable: !!mediaStripRef.player && mediaStripRef.player.canGoPrevious
            onClicked: mediaStripRef.player.previous()
        }
        VerticalBarIcon {
            host: verticalMiddle.host
            icon: mediaStripRef.playing ? "󰏤" : "󰐊"; tooltip: mediaStripRef.title; open: true
            clickable: !!mediaStripRef.player && mediaStripRef.player.canTogglePlaying
            onClicked: mediaStripRef.player.togglePlaying()
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
            onClicked: barHost.togglePanel(mediaMenuRef)
        }
    }
    CaptureIndicator {
        host: verticalMiddle.host
        id: verticalCapture
        anchors.bottom: verticalCalendarIcon.top
        anchors.horizontalCenterOffset: 0
        anchors.bottomMargin: shown ? (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3) : 0
        anchors.horizontalCenter: parent.horizontalCenter
        height: shown ? 24 : 0
        recording: obsMenuRef.obsState.recording || obsMenuRef.obsState.streaming
        recordingPaused: obsMenuRef.obsState.paused && !obsMenuRef.obsState.streaming
        streaming: obsMenuRef.obsState.streaming
        dictating: verticalMiddle.host.dictating
        transcribing: verticalMiddle.host.transcribing
        dictationLevels: verticalMiddle.host.dictationLevels
        onRecordingClicked: barHost.togglePanel(recordingMenuRef)
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
    ClockButton {
        host: verticalMiddle.host
        id: verticalCalendarIcon
        anchors.centerIn: parent
        compact: true
        onClicked: barHost.togglePanel(calendarMenuRef)
    }
    Item {
        anchors.top: verticalCalendarIcon.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
        height: barHost.notchLayout ? barHost.weatherReveal : (barHost.islandsLayout ? barHost.islandSpacing : barHost.centeredLayout ? barHost.itemGap : 3) + verticalWeatherIcon.height
        clip: barHost.notchLayout
        WeatherWidget {
            host: verticalMiddle.host
            id: verticalWeatherIcon
            visible: barHost.expanded
            enabled: !barHost.notchLayout || barHost.weatherExpanded
            y: parent.height - height
            anchors.horizontalCenter: parent.horizontalCenter
            autoRefresh: false
            compact: true
            text: barWeatherRef.text
            temp: barWeatherRef.temp
            onClicked: barHost.togglePanel(weatherMenuRef)
        }
    }
}
