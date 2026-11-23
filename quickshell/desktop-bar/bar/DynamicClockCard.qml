import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ReminderModel.js" as ReminderModel

Item {
    id: card
    required property var host
    required property var clock
    required property var calendar
    property bool opened: false
    signal dashboardRequested()
    signal controlsRequested()
    signal weatherRequested()
    readonly property var locale: Qt.locale()
    readonly property real midnight: clock ? new Date(clock.now.getFullYear(), clock.now.getMonth(), clock.now.getDate()).getTime() : 0
    readonly property var week: opened && calendar ? ReminderModel.weekDays(
        new Date(midnight), locale, calendar.reminders || [], calendar.events || []) : []
    readonly property real preferredWidth: 328
    readonly property real preferredHeight: 190

    MouseArea {
        parent: card.parent
        anchors.fill: parent
        z: -1
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: mouse => mouse.button === Qt.RightButton ? card.controlsRequested() : card.dashboardRequested()
    }
    Item {
        anchors.centerIn: parent
        width: card.preferredWidth
        height: card.preferredHeight
        scale: Math.min(card.width / width, card.height / height)
        Column {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: 8
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
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: PanelStyle.padding / 2
            active: card.opened && PluginRegistry.weatherEnabled
            sourceComponent: WeatherWidget {
                objectName: "dropClockWeather"
                host: card.host
                autoRefresh: true
                labelSize: PanelStyle.captionSize
                visible: temperature !== "" && temperature !== "--"
                onClicked: card.weatherRequested()
            }
        }
    }
}
