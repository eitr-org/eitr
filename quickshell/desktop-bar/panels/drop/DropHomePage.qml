import "../.."
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle
import "../../WeatherIcons.js" as WeatherIcons
import "../../ReminderModel.js" as ReminderModel

// Drop's first page, drawn flat on the card: the weather and the next days on the left,
// a thin rule, then the month on the right with today ringed in the accent. Clicking a
// day swaps the weather for that day's plans; clicking it again goes back. Clicking the
// weather opens it in place over the whole page.
Item {
    id: page
    required property var barHost
    required property color foreground
    required property color accent
    required property color background
    required property date now
    readonly property var weather: (DesktopData.topics["weather.default"] || {}).data || ({})
    readonly property bool hasWeather: !!weather.temp && weather.temp !== "--"
    // The month shown in the grid; the arrows browse it and it returns to today on reopening.
    property int monthOffset: 0
    // The day whose plans replace the weather, or null for the weather.
    property var selectedDay: null
    property bool weatherOpen: false
    function sameDay(first, second) { return !!first && !!second && first.toDateString() === second.toDateString(); }
    readonly property date shownMonth: new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)
    readonly property var calendar: barHost.calendarMenu
    function weekend(day) { return Qt.locale().weekDays.indexOf(day === 0 ? 7 : day) < 0; }
    implicitHeight: 262

    component Caption: Text {
        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        textFormat: Text.PlainText; elide: Text.ElideRight
    }
    component Heading: Text {
        color: page.foreground
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
        font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
        textFormat: Text.PlainText; elide: Text.ElideRight
    }

    // Weather: now, where, and the next three days.
    Item {
        id: weatherSide
        x: 6; width: 196; height: parent.height
        visible: !page.selectedDay && !page.weatherOpen
        Row {
            y: 8
            spacing: 14
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: page.hasWeather ? String(page.weather.text || "").split(" ")[0] : "󰖐"
                color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 38
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    text: page.hasWeather ? page.weather.temp : "--"
                    color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 34; font.weight: Font.Bold
                }
                Caption { width: weatherSide.width - 66; text: page.hasWeather ? page.weather.condition || "" : Eitr.I18n.tr("Weather unavailable") }
            }
        }
        Item {
            y: 92; width: parent.width; height: 20
            Heading { width: parent.width - humidity.width - 8; anchors.verticalCenter: parent.verticalCenter; text: page.weather.location || "" }
            Caption {
                id: humidity
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                visible: page.hasWeather
                text: "󰖌 " + (page.weather.humidity || "--")
            }
        }
        Rectangle { y: 122; width: parent.width; height: 1; color: Qt.alpha(page.foreground, 0.14) }
        Row {
            y: 140
            Repeater {
                model: (page.weather.forecastDays || []).slice(0, 3)
                Column {
                    required property var modelData
                    width: weatherSide.width / 3
                    spacing: 5
                    Caption { text: parent.modelData.day || ""; font.weight: Font.DemiBold; font.letterSpacing: 1 }
                    Text {
                        text: WeatherIcons.forecastIcon(String(parent.modelData.icon || ""))
                        color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 20
                    }
                    Text {
                        text: (parent.modelData.high || "--") + "°"
                        color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
                    }
                    Caption { text: (parent.modelData.low || "--") + "°" }
                }
            }
        }
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            onClicked: page.weatherOpen = true
        }
    }

    DropWeatherDetail {
        visible: page.weatherOpen
        anchors.fill: parent
        weather: page.weather
        foreground: page.foreground; accent: page.accent
        onClosed: page.weatherOpen = false
    }

    DropDayAgenda {
        visible: !!page.selectedDay && !page.weatherOpen
        x: weatherSide.x; width: weatherSide.width; height: parent.height
        barHost: page.barHost; foreground: page.foreground; accent: page.accent
        day: page.selectedDay || page.now
        onClosed: page.selectedDay = null
    }

    Rectangle {
        id: rule
        visible: !page.weatherOpen
        x: weatherSide.x + weatherSide.width + 18; y: 4
        width: 1; height: parent.height - 8
        color: Qt.alpha(page.foreground, 0.14)
    }

    // The month: weekends in the accent, today ringed, days with plans dotted.
    Item {
        id: month
        visible: !page.weatherOpen
        x: rule.x + 19; width: parent.width - x - 4; height: parent.height
        readonly property int lead: (page.shownMonth.getDay() - Qt.locale().firstDayOfWeek % 7 + 7) % 7
        readonly property real cell: width / 7
        Item {
            width: parent.width; height: 28
            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                Text { anchors.verticalCenter: parent.verticalCenter; text: "󰃭"; color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 16 }
                Heading { anchors.verticalCenter: parent.verticalCenter; text: page.shownMonth.toLocaleDateString(Qt.locale(), "MMMM yyyy") }
            }
            Row {
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                Repeater {
                    model: [{glyph: "󰅁", step: -1}, {glyph: "󰅂", step: 1}]
                    PanelButton {
                        required property var modelData
                        width: 24; height: 24; icon: true
                        text: modelData.glyph; foreground: page.foreground
                        onClicked: page.monthOffset += modelData.step
                    }
                }
            }
        }
        Grid {
            y: 36
            columns: 7
            Repeater {
                model: 7
                Text {
                    required property int index
                    readonly property int weekday: (Qt.locale().firstDayOfWeek + index) % 7
                    width: month.cell; height: 24; horizontalAlignment: Text.AlignHCenter
                    text: Qt.locale().dayName(weekday, Locale.NarrowFormat)
                    color: page.weekend(weekday) ? page.accent : page.foreground
                    opacity: page.weekend(weekday) ? 1 : PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.DemiBold
                }
            }
            Repeater {
                model: 42
                Item {
                    required property int index
                    readonly property date day: new Date(page.shownMonth.getFullYear(), page.shownMonth.getMonth(), index - month.lead + 1)
                    readonly property bool inMonth: day.getMonth() === page.shownMonth.getMonth()
                    readonly property bool today: day.toDateString() === page.now.toDateString()
                    readonly property bool planned: inMonth && !!page.calendar
                        && ReminderModel.dayItems(page.calendar.reminders || [], page.calendar.events || [], day).length > 0
                    readonly property bool selected: page.sameDay(day, page.selectedDay)
                    width: month.cell; height: 33
                    Rectangle {
                        anchors.centerIn: parent; width: 28; height: 28; radius: 14
                        visible: parent.today || parent.selected || dayMouse.containsMouse
                        color: parent.selected && !parent.today ? Qt.alpha(page.foreground, 0.16)
                            : Qt.alpha(parent.today ? page.accent : page.foreground, dayMouse.containsMouse ? 0.22 : 0.12)
                        border.width: parent.today ? 2 : parent.selected ? 1 : 0
                        border.color: parent.today ? page.accent : Qt.alpha(page.foreground, 0.5)
                        Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(120) } }
                    }
                    MouseArea {
                        id: dayMouse
                        anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: page.selectedDay = parent.selected ? null : parent.day
                    }
                    Text {
                        anchors.centerIn: parent
                        text: parent.day.getDate()
                        color: parent.today || (parent.inMonth && page.weekend(parent.day.getDay())) ? page.accent : page.foreground
                        opacity: parent.inMonth ? 1 : 0.25
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                        font.weight: parent.today ? Font.Bold : Font.Normal; font.features: PanelStyle.tabularFigures
                    }
                    Rectangle {
                        visible: parent.planned && !parent.today
                        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 2
                        width: 4; height: 4; radius: 2; color: page.accent
                    }
                }
            }
        }
    }
}
