import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import "WeatherIcons.js" as WeatherIcons
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    implicitWidth: 588
    implicitHeight: weatherColumn.implicitHeight + verticalContentInset
    keyTarget: weatherContent
    property var weatherData: ({})
    property var defaultWeatherData: ({})
    property var city: null
    property bool searching: false
    property var cities: []
    property string searchError: ""
    property string requestedCity: ""
    property string requestedSearch: ""
    signal defaultWeatherUpdated(var data)
    readonly property bool loading: weatherQuery.running
    readonly property string temperature: String(weatherData.temp || "--").split("°")[0]
    readonly property string unit: String(weatherData.temp || "").indexOf("°") >= 0 ? "°" + String(weatherData.temp).split("°")[1] : ""
    readonly property string alternate: isFinite(Number(temperature)) && temperature !== "" ? unit === "°F" ? Math.round((Number(temperature) - 32) * 5 / 9) + "°C" : unit === "°C" ? Math.round(Number(temperature) * 9 / 5 + 32) + "°F" : "" : ""

    function refresh() {
        if (!weatherQuery.running) {
            requestedCity = JSON.stringify(city);
            weatherQuery.command = ["python3", Quickshell.shellDir + "/scripts/weather-popup.py", "weather", requestedCity];
            weatherQuery.running = true;
        }
    }
    function cancelSearch() {
        searching = false;
        cities = [];
        searchError = "";
        debounce.stop();
        if (opened) weatherContent.forceActiveFocus();
    }
    function selectCity(value) {
        city = value;
        cancelSearch();
        refresh();
    }
    function restoreDefault() {
        city = null;
        cancelSearch();
        weatherData = defaultWeatherData;
        refresh();
    }
    function forecastIcon(code) {
        return WeatherIcons.forecastIcon(code);
    }
    onOpenedChanged: {
        if (opened) {
            city = null;
            weatherData = defaultWeatherData;
            refresh();
        } else {
            city = null;
            cancelSearch();
        }
    }
    Timer { interval: 900000; running: menu.opened; repeat: true; onTriggered: menu.refresh() }
    Timer {
        id: debounce
        interval: 300
        onTriggered: {
            if (searchQuery.running || !menu.searching || cityInput.text.trim().length < 2) return;
            menu.requestedSearch = cityInput.text.trim();
            searchQuery.command = ["python3", Quickshell.shellDir + "/scripts/weather-popup.py", "search", menu.requestedSearch];
            searchQuery.running = true;
        }
    }
    Process {
        id: weatherQuery
        stdout: StdioCollector { id: weatherOutput }
        onExited: function(code) {
            if (!menu.opened) return;
            if (menu.requestedCity !== JSON.stringify(menu.city)) {
                menu.refresh();
                return;
            }
            try {
                if (code !== 0) throw new Error("weather unavailable");
                menu.weatherData = JSON.parse(weatherOutput.text);
                if (menu.city === null) menu.defaultWeatherUpdated(menu.weatherData);
            } catch (e) {
                if (menu.city === null && menu.weatherData.temp) return;
                menu.weatherData = {temp: "--", condition: "Unavailable", location: menu.city ? menu.city.name : "Weather"};
            }
        }
    }
    Process {
        id: searchQuery
        stdout: StdioCollector { id: searchOutput }
        onExited: function(code) {
            if (!menu.searching) return;
            if (menu.requestedSearch !== cityInput.text.trim()) { debounce.restart(); return; }
            try {
                if (code !== 0) throw new Error("search unavailable");
                var result = JSON.parse(searchOutput.text);
                menu.cities = result.cities;
                menu.searchError = result.error;
            } catch (e) { menu.searchError = "City search unavailable"; }
        }
    }
    Item {
        id: weatherContent
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: {
            if (menu.searching) menu.cancelSearch();
            else menu.opened = false;
        }
        Column {
            id: weatherColumn
            x: 0
            y: 0
            width: parent.width
            spacing: 14
            Item {
                width: parent.width
                height: 116
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 12
                    Text { width: Math.max(76, paintedWidth); horizontalAlignment: Text.AlignHCenter; text: String(menu.weatherData.text || "󰖐").split(" ")[0]; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 64 }
                    Text { text: menu.temperature; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 56; font.bold: true }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 5
                        Text { text: menu.unit; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 20 }
                        Text { text: menu.alternate; color: menu.foreground; opacity: 0.72; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                    }
                }
                Column {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: 250
                    spacing: 12
                    Item {
                        width: parent.width
                        height: 30
                        Row {
                            visible: !menu.searching
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 6
                            Item {
                                width: 20; height: 23
                                anchors.verticalCenter: parent.verticalCenter
                                PanelHeading { anchors.centerIn: parent; scale: 0.7; width: 28; text: ""; foreground: menu.foreground; accent: menu.accent; rune: "weather" }
                            }
                            Text { width: cityMouse.width - 26; anchors.verticalCenter: parent.verticalCenter; text: String(menu.weatherData.location || Eitr.I18n.tr("Weather")).toUpperCase(); elide: Text.ElideRight; color: menu.foreground; opacity: 0.72; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true }
                        }
                        MouseArea {
                            id: cityMouse
                            hoverEnabled: true
                            width: parent.width - cityControls.width - 6
                            height: parent.height
                            enabled: !menu.searching
                            cursorShape: Qt.PointingHandCursor
                            onClicked: { menu.searching = true; cityInput.text = ""; cityInput.forceActiveFocus(); }
                        }
                        BarTooltip {
                            target: cityMouse
                            hovered: cityMouse.containsMouse && !menu.searching
                            text: String(menu.weatherData.location || Eitr.I18n.tr("Weather"))
                            foreground: menu.foreground
                            background: menu.background
                        }
                        Rectangle {
                            visible: menu.searching
                            width: parent.width - cityControls.width - 6
                            height: 30
                            radius: DesktopStyle.radius(PanelStyle.controlRadius)
                            color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08)
                            border.color: cityInput.activeFocus ? menu.accent : Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.12)
                            Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Search city"); visible: cityInput.text === ""; color: menu.foreground; opacity: 0.58; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                            TextInput {
                                id: cityInput
                                HoverHandler { cursorShape: Qt.IBeamCursor }
                                activeFocusOnTab: true
                                anchors.fill: parent
                                anchors.margins: 8
                                verticalAlignment: TextInput.AlignVCenter
                                clip: true
                                color: menu.foreground
                                selectionColor: menu.accent
                                selectedTextColor: menu.background
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                                onTextChanged: { menu.cities = []; menu.searchError = ""; debounce.restart(); }
                                Keys.onEscapePressed: menu.cancelSearch()
                            }
                        }
                        Row {
                            id: cityControls
                            anchors.right: parent.right
                            spacing: 6
                            PanelButton {
                                id: refreshButton
                                width: 30
                                height: 30
                                icon: true
                                text: "\uF021"
                                foreground: menu.foreground
                                loading: menu.loading
                                onClicked: menu.refresh()
                                HoverHandler { id: refreshHover }
                                BarTooltip { target: refreshButton; hovered: refreshHover.hovered; text: menu.loading ? Eitr.I18n.tr("Updating") : Eitr.I18n.tr("Refresh"); foreground: menu.foreground; background: menu.background }
                            }
                            PanelButton { visible: menu.searching || menu.city !== null; width: 30; height: 30; icon: true; text: "\uF00D"; foreground: menu.foreground; onClicked: menu.restoreDefault() }
                        }
                    }
                    Text { text: menu.weatherData.condition || ""; color: menu.foreground; opacity: 0.72; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.bold: true }
                    Row {
                        spacing: 25
                        Repeater {
                            model: [{label: "FEELS", key: "feels"}, {label: "WIND", key: "wind"}, {label: "HUMID", key: "humidity"}]
                            Column {
                                required property var modelData
                                spacing: 5
                                Text { text: Eitr.I18n.tr(parent.modelData.label); color: menu.foreground; opacity: 0.58; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true }
                                Text { text: menu.weatherData[parent.modelData.key] || "--"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; font.bold: true }
                            }
                        }
                    }
                }
            }
            Column {
                id: results
                visible: menu.searching && (menu.cities.length > 0 || menu.searchError !== "")
                width: parent.width
                spacing: 4
                Repeater {
                    model: menu.cities
                    PanelButton {
                        required property var modelData
                        width: results.width
                        height: 34
                        text: [modelData.name, modelData.admin1 || "", modelData.country || ""].filter(value => value !== "").join(", ")
                        foreground: menu.foreground
                        onClicked: menu.selectCity(modelData)
                    }
                }
                Text { visible: menu.searchError !== ""; text: menu.searchError; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
            }
            PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
            Row {
                width: parent.width
                Repeater {
                    model: 3
                    Item {
                        required property int index
                        readonly property var day: (menu.weatherData.forecastDays || [])[index] || {}
                        width: parent.width / 3
                        height: 60
                        Row {
                            anchors.centerIn: parent
                            spacing: 14
                            Text { anchors.verticalCenter: parent.verticalCenter; text: menu.forecastIcon(String(parent.parent.day.icon || "")); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 28 }
                            Column {
                                spacing: 2
                                Text { text: parent.parent.parent.day.day || ""; color: menu.foreground; opacity: 0.58; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true }
                                Text { text: (parent.parent.parent.day.high || "--") + "°  " + (parent.parent.parent.day.low || "--") + "°"; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; font.bold: true }
                            }
                        }
                    }
                }
            }
        }
    }
}
