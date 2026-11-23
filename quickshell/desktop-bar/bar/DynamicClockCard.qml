import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ReminderModel.js" as ReminderModel

Item {
    id: card
    required property var host
    required property var barHost
    required property var clock
    required property var calendar
    property bool opened: false
    signal calendarRequested()
    signal weatherRequested()
    readonly property var locale: Qt.locale()
    readonly property real midnight: clock ? new Date(clock.now.getFullYear(), clock.now.getMonth(), clock.now.getDate()).getTime() : 0
    readonly property var week: opened && calendar ? ReminderModel.weekDays(
        new Date(midnight), locale, calendar.reminders || [], calendar.events || []) : []
    readonly property real preferredWidth: 328
    readonly property real preferredHeight: 190 + (clockControls.item && clockControls.item.contentWidth > 0 ? 30 : 0)

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.calendarRequested()
    }
    Item {
        anchors.centerIn: parent
        width: card.preferredWidth
        height: card.preferredHeight
        scale: Math.min(card.width / width, card.height / height)
        Column {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: clockControls.item && clockControls.item.contentWidth > 0 ? -4 : 8
            spacing: 5
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: card.locale.toString(card.clock.now, card.host.barClock === "24h" ? "HH:mm" : "h:mm AP")
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.clockDisplaySize
                font.features: PanelStyle.tabularFigures
                font.bold: true
                color: card.host.barFg
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: card.locale.toString(new Date(card.midnight), Eitr.I18n.tr("dddd, d MMMM"))
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                color: card.host.barFg
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                topPadding: 5
                spacing: 6
                Repeater {
                    model: card.week
                    delegate: Column {
                        id: cell
                        required property var modelData
                        readonly property color ink: modelData.weekend ? card.host.activeBg : card.host.barFg
                        spacing: 3
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: card.locale.dayName(cell.modelData.weekday, Locale.ShortFormat).charAt(0).toUpperCase()
                            color: cell.ink
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.captionSize
                        }
                        Rectangle {
                            width: 32; height: width; radius: width / 2
                            color: "transparent"
                            border.width: cell.modelData.today ? 1 : 0
                            border.color: card.host.activeBg
                            Text {
                                anchors.centerIn: parent
                                text: cell.modelData.date.getDate().toLocaleString(card.locale, 'f', 0)
                                color: cell.ink
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                        }
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 4; height: width; radius: width / 2
                            color: cell.ink
                            opacity: cell.modelData.plans ? 1 : 0
                        }
                    }
                }
            }
        }
        Loader {
            id: clockControls
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: PanelStyle.padding / 2
            width: parent.width - PanelStyle.padding * 2
            active: card.opened
            sourceComponent: Flickable {
                contentWidth: slots.implicitWidth
                height: slots.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                clip: true
                Row {
                    id: slots
                    x: Math.max(0, (parent.parent.width - width) / 2)
                    spacing: card.host.workspaceItemSpacing
                    Repeater {
                        model: ["clockStart", "clockEnd"]
                        delegate: BarZoneItems {
                            required property string modelData
                            host: card.host
                            barHost: card.barHost
                            zone: modelData
                            excludeWeather: true
                            registerIcons: false
                            visible: width > 0
                            onPanelRequested: (plugin, panel, target) => card.barHost.openPluginPanel(plugin, panel, target)
                        }
                    }
                }
            }
        }
        Loader {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: PanelStyle.padding / 2
            active: card.opened && PluginRegistry.weatherEnabled
            sourceComponent: WeatherWidget {
                host: card.host
                autoRefresh: true
                labelSize: PanelStyle.captionSize
                visible: temperature !== ""
                onClicked: card.weatherRequested()
            }
        }
    }
}
