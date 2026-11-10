import "../.."
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle
import "../../WeatherIcons.js" as WeatherIcons
import "../../ReminderModel.js" as ReminderModel

// Drop's first page: today and the weather beside the month, then the next days'
// forecast and what is planned for today.
Column {
    id: page
    required property var barHost
    required property color foreground
    required property color accent
    required property color background
    required property date now
    readonly property var weather: (DesktopData.topics["weather.default"] || {}).data || ({})
    readonly property bool hasWeather: !!weather.temp && weather.temp !== "--"
    readonly property var agenda: barHost.calendarMenu ? ReminderModel.dayItems(barHost.calendarMenu.reminders || [], barHost.calendarMenu.events || [], now) : []
    // The month shown in the grid; arrows browse it and it returns to today on reopening.
    property int monthOffset: 0
    readonly property date shownMonth: new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)
    spacing: 10

    component Caption: Text {
        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        textFormat: Text.PlainText; elide: Text.ElideRight
    }
    component Label: Text {
        color: page.accent
        font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.DemiBold
        font.capitalization: Font.AllUppercase; font.letterSpacing: 1.4
        textFormat: Text.PlainText
    }

    Row {
        width: parent.width
        spacing: 10
        // Today: the date set large, the weather under it.
        DropCard {
            id: today
            foreground: page.foreground
            width: Math.round((parent.width - parent.spacing) * 0.44); height: 246
            Column {
                x: 18; y: 16; width: parent.width - 36
                spacing: 0
                Label { text: page.now.toLocaleDateString(Qt.locale(), "dddd") }
                Row {
                    spacing: 10
                    Text {
                        text: page.now.getDate()
                        color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 64; font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                    Column {
                        anchors.bottom: parent.bottom; anchors.bottomMargin: 14
                        Text {
                            text: page.now.toLocaleDateString(Qt.locale(), "MMMM")
                            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 18; font.weight: Font.DemiBold
                        }
                        Caption { text: page.now.getFullYear() }
                    }
                }
                Item { width: 1; height: 6 }
                Rectangle { width: parent.width; height: 1; color: Qt.alpha(page.foreground, 0.12) }
                Item { width: 1; height: 10 }
                Row {
                    spacing: 12
                    visible: page.hasWeather
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: String(page.weather.text || "").split(" ")[0]
                        color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 40
                    }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        Text {
                            text: page.weather.temp || ""
                            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 28; font.weight: Font.DemiBold
                        }
                        Caption { width: today.width - 100; text: [page.weather.condition, page.weather.location].filter(Boolean).join(" · ") }
                    }
                }
                Caption { visible: !page.hasWeather; text: Eitr.I18n.tr("Weather unavailable") }
                Item { width: 1; height: 8 }
                Row {
                    visible: page.hasWeather
                    spacing: 18
                    Repeater {
                        model: [{label: "Feels", key: "feels"}, {label: "Wind", key: "wind"}, {label: "Humidity", key: "humidity"}]
                        Column {
                            required property var modelData
                            spacing: 2
                            Caption { text: Eitr.I18n.tr(parent.modelData.label); font.pixelSize: 11 }
                            Text {
                                text: page.weather[parent.modelData.key] || "--"
                                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                            }
                        }
                    }
                }
            }
            MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: page.barHost.togglePanel(page.barHost.weatherMenu)
            }
        }
        // The month, browsable with its arrows; today is filled with the accent and days
        // with plans carry a dot.
        DropCard {
            id: month
            foreground: page.foreground
            width: parent.width - today.width - parent.spacing; height: 246
            readonly property int lead: (page.shownMonth.getDay() - Qt.locale().firstDayOfWeek % 7 + 7) % 7
            readonly property real cell: (width - 24) / 7
            Item {
                x: 12; y: 10; width: parent.width - 24; height: 28
                Text {
                    x: 4; anchors.verticalCenter: parent.verticalCenter
                    text: page.shownMonth.toLocaleDateString(Qt.locale(), "MMMM yyyy")
                    color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                }
                Row {
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    spacing: 4
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
                x: 12; y: 44
                columns: 7
                Repeater {
                    model: 7
                    Caption {
                        required property int index
                        width: month.cell; height: 22; horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 11
                        text: Qt.locale().dayName((Qt.locale().firstDayOfWeek + index) % 7, Locale.NarrowFormat)
                    }
                }
                Repeater {
                    model: 42
                    Item {
                        required property int index
                        readonly property date day: new Date(page.shownMonth.getFullYear(), page.shownMonth.getMonth(), index - month.lead + 1)
                        readonly property bool inMonth: day.getMonth() === page.shownMonth.getMonth()
                        readonly property bool today: day.toDateString() === page.now.toDateString()
                        readonly property bool planned: inMonth && page.barHost.calendarMenu
                            && ReminderModel.dayItems(page.barHost.calendarMenu.reminders || [], page.barHost.calendarMenu.events || [], day).length > 0
                        width: month.cell; height: 29
                        Rectangle {
                            anchors.centerIn: parent; width: 26; height: 26; radius: 13
                            visible: parent.today; color: page.accent
                        }
                        Text {
                            anchors.centerIn: parent
                            text: parent.day.getDate()
                            color: parent.today ? PanelStyle.readableInk(page.accent, page.foreground, page.background) : page.foreground
                            opacity: parent.inMonth ? 1 : 0.3
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                            font.weight: parent.today ? Font.Bold : Font.Normal; font.features: PanelStyle.tabularFigures
                        }
                        Rectangle {
                            visible: parent.planned && !parent.today
                            anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 1
                            width: 4; height: 4; radius: 2; color: page.accent
                        }
                    }
                }
            }
        }
    }

    Row {
        width: parent.width
        spacing: 10
        // The next three days.
        DropCard {
            foreground: page.foreground
            width: today.width; height: 84
            Row {
                anchors.centerIn: parent
                spacing: 0
                Repeater {
                    model: (page.weather.forecastDays || []).slice(0, 3)
                    Column {
                        required property var modelData
                        width: (today.width - 24) / 3
                        spacing: 2
                        Caption { anchors.horizontalCenter: parent.horizontalCenter; text: parent.modelData.day || ""; font.pixelSize: 11 }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: WeatherIcons.forecastIcon(String(parent.modelData.icon || ""))
                            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 22
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: (parent.modelData.high || "--") + "° " + (parent.modelData.low || "--") + "°"
                            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.weight: Font.DemiBold
                        }
                    }
                }
            }
            Caption { anchors.centerIn: parent; visible: !(page.weather.forecastDays || []).length; text: Eitr.I18n.tr("No forecast") }
        }
        // Today's plans from the calendar and reminders.
        DropCard {
            foreground: page.foreground
            width: month.width; height: 84
            Column {
                x: 16; y: 12; width: parent.width - 32
                spacing: 5
                Label { text: Eitr.I18n.tr("Today") }
                Repeater {
                    model: page.agenda.slice(0, 2)
                    Row {
                        required property var modelData
                        spacing: 8
                        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 6; height: 6; radius: 3; color: page.accent }
                        Text {
                            width: month.width - 90
                            text: parent.modelData.text || ""
                            color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                            elide: Text.ElideRight; textFormat: Text.PlainText
                        }
                        Caption {
                            visible: !parent.modelData.allDay
                            text: Qt.formatTime(new Date(parent.modelData.due * 1000), Qt.locale().timeFormat(Locale.ShortFormat))
                        }
                    }
                }
                Caption { visible: page.agenda.length === 0; text: Eitr.I18n.tr("Nothing planned") }
            }
            MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: page.barHost.togglePanel(page.barHost.calendarMenu)
            }
        }
    }
}
