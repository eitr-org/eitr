import "../.."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle
import "../../WeatherIcons.js" as WeatherIcons

// The weather opened in place on Drop's home page: now, large, with how it feels, the wind
// and humidity; beside it the coming days, each with a bar spanning its low to its high on a
// scale shared by all of them.
Item {
    id: detail
    required property var weather
    required property color foreground
    required property color accent
    signal closed()
    readonly property bool hasWeather: !!weather.temp && weather.temp !== "--"
    readonly property var days: (weather.forecastDays || []).slice(0, 4)
    readonly property real coldest: Math.min.apply(null, days.map(day => Number(day.low)).filter(isFinite).concat([99]))
    readonly property real warmest: Math.max.apply(null, days.map(day => Number(day.high)).filter(isFinite).concat([-99]))

    component Caption: Text {
        color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        textFormat: Text.PlainText; elide: Text.ElideRight
    }

    Item {
        width: parent.width; height: 28
        PanelButton {
            id: back
            width: 24; height: 24; icon: true; anchors.verticalCenter: parent.verticalCenter
            text: "󰅁"; foreground: detail.foreground
            Accessible.name: Eitr.I18n.tr("Back")
            onClicked: detail.closed()
        }
        Text {
            x: back.width + 8; anchors.verticalCenter: parent.verticalCenter
            width: parent.width - x
            text: detail.weather.location || Eitr.I18n.tr("Weather")
            color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2; elide: Text.ElideRight
        }
    }

    // Now.
    Column {
        id: now
        x: 6; y: 48; width: 220
        spacing: 14
        Row {
            spacing: 16
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: detail.hasWeather ? String(detail.weather.text || "").split(" ")[0] : "󰖐"
                color: detail.accent; font.family: DesktopFonts.family; font.pixelSize: 56
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    text: detail.hasWeather ? detail.weather.temp : "--"
                    color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: 44; font.weight: Font.Bold
                }
                Caption { width: 130; text: detail.hasWeather ? detail.weather.condition || "" : Eitr.I18n.tr("Weather unavailable") }
            }
        }
        Row {
            visible: detail.hasWeather
            spacing: 22
            Repeater {
                model: [{label: "Feels like", key: "feels", glyph: "󰔏"}, {label: "Wind", key: "wind", glyph: "󰖝"}, {label: "Humidity", key: "humidity", glyph: "󰖌"}]
                Column {
                    required property var modelData
                    spacing: 3
                    Text { text: parent.modelData.glyph; color: detail.accent; font.family: DesktopFonts.family; font.pixelSize: 16 }
                    Text {
                        text: detail.weather[parent.modelData.key] || "--"
                        color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                    }
                    Caption { text: Eitr.I18n.tr(parent.modelData.label); font.pixelSize: 11 }
                }
            }
        }
    }

    Rectangle {
        id: rule
        x: now.x + now.width + 24; y: 44
        width: 1; height: parent.height - y - 4
        color: Qt.alpha(detail.foreground, 0.14)
    }

    // The coming days.
    Column {
        x: rule.x + 24; y: 48; width: parent.width - x - 4
        spacing: 6
        Caption { text: Eitr.I18n.tr("NEXT DAYS"); font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.2 }
        Caption { visible: detail.days.length === 0; text: Eitr.I18n.tr("No forecast") }
        Repeater {
            model: detail.days
            Item {
                id: day
                required property var modelData
                readonly property real low: Number(modelData.low)
                readonly property real high: Number(modelData.high)
                readonly property real span: Math.max(1, detail.warmest - detail.coldest)
                width: parent.width; height: 40
                Text {
                    width: 46; anchors.verticalCenter: parent.verticalCenter
                    text: day.modelData.day || ""
                    color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                }
                Text {
                    x: 50; width: 28; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignHCenter
                    text: WeatherIcons.forecastIcon(String(day.modelData.icon || ""))
                    color: detail.accent; font.family: DesktopFonts.family; font.pixelSize: 20
                }
                Text {
                    id: lowText
                    x: 86; width: 34; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight
                    text: (day.modelData.low || "--") + "°"
                    color: detail.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Rectangle {
                    id: track
                    x: lowText.x + lowText.width + 10; width: parent.width - x - 46
                    anchors.verticalCenter: parent.verticalCenter
                    height: 4; radius: 2; color: Qt.alpha(detail.foreground, 0.12)
                    Rectangle {
                        x: isFinite(day.low) ? track.width * (day.low - detail.coldest) / day.span : 0
                        width: isFinite(day.high) && isFinite(day.low) ? Math.max(4, track.width * (day.high - day.low) / day.span) : 0
                        height: parent.height; radius: 2; color: detail.accent
                    }
                }
                Text {
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    text: (day.modelData.high || "--") + "°"
                    color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
                }
            }
        }
    }
}
