import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../WeatherIcons.js" as WeatherIcons

// The weather opened in place on Drop's home page: now, large, with how it feels, the wind
// and humidity; beside it the coming days, each with a bar spanning its low to its high on a
// scale shared by all of them. The search button looks up another city (through the same
// weather queries as the Weather panel); the choice lasts until × or the dashboard closes.
Item {
    id: detail
    required property var weather
    required property color foreground
    required property color accent
    required property color background
    signal closed()
    // A city picked from the search, its weather, and the search itself.
    property var city: null
    property var cityWeather: ({})
    property bool loading: false
    property bool searching: false
    property var cities: []
    property string searchError: ""
    property string request: ""
    readonly property var shown: city ? cityWeather : weather
    readonly property bool hasWeather: !!shown.temp && shown.temp !== "--"
    function reset() {
        DesktopData.cancelQuery(request); request = "";
        city = null; cityWeather = ({}); loading = false; stopSearch();
    }
    function startSearch() { searching = true; cities = []; searchError = ""; cityField.text = ""; Qt.callLater(() => cityField.forceActiveFocus()); }
    function stopSearch() { searching = false; cities = []; searchError = ""; debounce.stop(); }
    function choose(value) {
        stopSearch();
        DesktopData.cancelQuery(request);
        city = value; cityWeather = ({}); loading = true;
        const key = JSON.stringify(value);
        request = DesktopData.queryWeather("city", {city: value}, detail, function(error, data) {
            if (key !== JSON.stringify(detail.city)) return;
            detail.request = ""; detail.loading = false;
            detail.cityWeather = error ? {temp: "--", condition: "Unavailable", location: value.name} : data;
        });
    }
    Timer {
        id: debounce
        interval: 300
        onTriggered: {
            const query = cityField.text.trim();
            if (!detail.searching || query.length < 2) return;
            DesktopData.cancelQuery(detail.request);
            detail.request = DesktopData.queryWeather("search", {query: query}, detail, function(error, result) {
                detail.request = "";
                if (!detail.searching || query !== cityField.text.trim()) return;
                detail.cities = result.cities || [];
                detail.searchError = error ? Eitr.I18n.tr("City search unavailable") : result.error ? Eitr.I18n.tr(result.error) : "";
            });
        }
    }
    Component.onDestruction: DesktopData.releaseOwner(detail)
    readonly property var days: (shown.forecastDays || []).slice(0, 4)
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
            visible: !detail.searching
            x: back.width + 8; anchors.verticalCenter: parent.verticalCenter
            width: parent.width - x - tools.width - 8
            text: detail.shown.location || Eitr.I18n.tr("Weather")
            color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.Bold
            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2; elide: Text.ElideRight
        }
        PanelTextField {
            id: cityField
            visible: detail.searching
            x: back.width + 8; width: parent.width - x - tools.width - 8; height: 28
            anchors.verticalCenter: parent.verticalCenter
            foreground: detail.foreground; accent: detail.accent
            placeholderText: Eitr.I18n.tr("Search a city…")
            onTextChanged: { detail.cities = []; detail.searchError = ""; debounce.restart(); }
            Keys.onEscapePressed: detail.stopSearch()
            onAccepted: if (detail.cities.length) detail.choose(detail.cities[0])
        }
        Row {
            id: tools
            anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            PanelLoadingIndicator {
                width: 24; height: 24
                busy: detail.loading || detail.request !== ""
                foreground: detail.foreground; background: detail.background
            }
            PanelButton {
                width: 24; height: 24; icon: true
                text: detail.searching ? "\uF00D" : "\uF002"; foreground: detail.foreground
                Accessible.name: detail.searching ? Eitr.I18n.tr("Close search") : Eitr.I18n.tr("Search a city")
                onClicked: detail.searching ? detail.stopSearch() : detail.startSearch()
            }
            PanelButton {
                visible: !!detail.city && !detail.searching
                width: 24; height: 24; icon: true; text: "\u{F01A4}"; foreground: detail.foreground
                Accessible.name: Eitr.I18n.tr("Back to your location")
                onClicked: detail.reset()
            }
        }
    }

    // City results take the page while searching.
    Column {
        visible: detail.searching
        x: back.x; y: 44; width: parent.width - 8
        spacing: 4
        Repeater {
            model: detail.cities
            PanelButton {
                required property var modelData
                width: parent.width; height: 34
                leadingIcon: "󰍎"; textAlignment: Text.AlignLeft
                text: [modelData.name, modelData.admin1 || "", modelData.country || ""].filter(value => value !== "").join(", ")
                foreground: detail.foreground
                onClicked: detail.choose(modelData)
            }
        }
        Caption {
            visible: detail.searchError !== "" || (detail.cities.length === 0 && cityField.text.trim().length < 2)
            text: detail.searchError || Eitr.I18n.tr("Type at least two letters")
        }
    }

    // Now.
    Column {
        id: now
        visible: !detail.searching
        x: 6; y: 48; width: 220
        spacing: 14
        Row {
            spacing: 16
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: detail.hasWeather ? String(detail.shown.text || "").split(" ")[0] : "󰖐"
                color: detail.accent; font.family: DesktopFonts.family; font.pixelSize: 56
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    text: detail.hasWeather ? detail.shown.temp : "--"
                    color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: 44; font.weight: Font.Bold
                }
                Caption { width: 130; text: detail.hasWeather ? detail.shown.condition || "" : Eitr.I18n.tr("Weather unavailable") }
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
                        text: detail.shown[parent.modelData.key] || "--"
                        color: detail.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                    }
                    Caption { text: Eitr.I18n.tr(parent.modelData.label); font.pixelSize: 11 }
                }
            }
        }
    }

    Rectangle {
        id: rule
        visible: !detail.searching
        x: now.x + now.width + 24; y: 44
        width: 1; height: parent.height - y - 4
        color: Qt.alpha(detail.foreground, 0.14)
    }

    // The coming days.
    Column {
        visible: !detail.searching
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
