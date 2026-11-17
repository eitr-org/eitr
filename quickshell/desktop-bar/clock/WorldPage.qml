import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

// World clock page: read-only view of cities configured for the official world-clock
// plugin, or a concise prompt to install it from Eitr Store when absent.
Flickable {
    id: worldPage
    required property color foreground
    required property color background
    required property color accent
    property string clockFormat: "24h"
    property bool active: false
    property bool live: true
    property var cities: []
    property string errorMessage: ""
    property bool refreshedOnce: false
    // The current minute; city times come from each city's UTC offset, so the helper runs only
    // when the cities change or an offset does (daylight saving), never on a timer.
    property real now: Date.now()
    function cityTime(city) {
        const shifted = new Date(now + (Number(city.utcOffsetMinutes) || 0) * 60000);
        const hours = shifted.getUTCHours(), minutes = String(shifted.getUTCMinutes()).padStart(2, "0");
        if (clockFormat === "12h") return (hours % 12 || 12) + ":" + minutes + (hours < 12 ? " AM" : " PM");
        return String(hours).padStart(2, "0") + ":" + minutes;
    }
    function dayDelta(city) {
        const shifted = new Date(now + (Number(city.utcOffsetMinutes) || 0) * 60000);
        const local = new Date(now);
        const cityDay = Date.UTC(shifted.getUTCFullYear(), shifted.getUTCMonth(), shifted.getUTCDate());
        const localDay = Date.UTC(local.getFullYear(), local.getMonth(), local.getDate());
        return Math.round((cityDay - localDay) / 86400000);
    }
    function offsetFromLocal(city) {
        return (Number(city.utcOffsetMinutes) || 0) + new Date(now).getTimezoneOffset();
    }
    signal storeRequested(string kind, string tab)
    contentHeight: contentColumn.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    readonly property bool pluginInstalled: {
        const installed = PluginRegistry.installed || [];
        for (let index = 0; index < installed.length; index += 1) {
            const entry = installed[index];
            if (entry && entry.id === "world-clock" && !!entry.official && !entry.blocked) return true;
        }
        return false;
    }

    readonly property string configPath: Eitr.Paths.config("eitr/plugins/world-clock.json")

    function refreshCities() {
        if (!live || !pluginInstalled || resolver.running) return;
        resolver.command = ["python3", Quickshell.shellDir + "/scripts/world-clock.py", "--config", configPath];
        resolver.running = true;
    }

    function formatOffset(minutes) {
        const value = Math.round(Number(minutes) || 0);
        if (value === 0) return Eitr.I18n.tr("Local time");
        const sign = value > 0 ? "+" : "-";
        const abs = Math.abs(value);
        const hours = Math.floor(abs / 60);
        const mins = abs % 60;
        if (mins === 0) return sign + hours + "h";
        return hours > 0 ? (sign + hours + "h " + mins + "m") : (sign + mins + "m");
    }

    function formatDayDelta(delta) {
        if (delta === -1) return Eitr.I18n.tr("Yesterday");
        if (delta === 1) return Eitr.I18n.tr("Tomorrow");
        return "";
    }

    onActiveChanged: if (active && pluginInstalled) refreshCities()
    onPluginInstalledChanged: {
        if (pluginInstalled) refreshCities();
        else cities = [];
    }

    FileView {
        path: worldPage.configPath
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: if (worldPage.pluginInstalled) worldPage.refreshCities()
        onLoadFailed: if (worldPage.pluginInstalled) worldPage.refreshCities()
    }

    Timer {
        // Wakes at the start of each minute while the page shows.
        interval: 60000 - Date.now() % 60000
        repeat: true
        triggeredOnStart: true
        running: worldPage.active && worldPage.pluginInstalled && worldPage.live
        onTriggered: {
            worldPage.now = Date.now();
            interval = 60000 - worldPage.now % 60000;
            const expired = worldPage.cities.some(city => (Number(city.validUntil) || 0) * 1000 <= worldPage.now);
            if (expired) worldPage.refreshCities();
        }
    }

    Process {
        id: resolver
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            const parsed = JsonState.parse(output.text, code, {cities: "array", error: "string"});
            if (parsed.ok) {
                worldPage.cities = parsed.data.cities;
                worldPage.errorMessage = parsed.data.error || "";
            } else {
                worldPage.errorMessage = parsed.error || Eitr.I18n.tr("Unable to read saved cities");
            }
            worldPage.refreshedOnce = true;
        }
    }

    Column {
        id: contentColumn
        width: worldPage.width
        spacing: 18

        FamilyPageHeader {
            foreground: worldPage.foreground
            rune: "ᛟ"
            group: Eitr.I18n.tr("Clock")
            title: Eitr.I18n.tr("World")
            description: Eitr.I18n.tr("Saved cities from the World Clock plugin, shown in your bar time format.")
        }

        ControlCard {
            visible: !worldPage.pluginInstalled
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: worldPage.foreground
            title: Eitr.I18n.tr("World Clock plugin")

            Text {
                width: parent.width
                wrapMode: Text.Wrap
                text: Eitr.I18n.tr("Install the official World Clock plugin from Eitr Store to follow saved cities here.")
                color: worldPage.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }

            PanelButton {
                id: storeBtn
                width: Math.max(132, Math.ceil(storeMetrics.advanceWidth) + 28)
                height: 36
                selected: true
                foreground: worldPage.foreground
                text: Eitr.I18n.tr("Open Eitr Store")
                onClicked: worldPage.storeRequested("plugins", "discover")
                TextMetrics { id: storeMetrics; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: storeBtn.text }
            }
        }

        ControlCard {
            visible: worldPage.pluginInstalled && worldPage.cities.length === 0
            surface: SettingsPalette.surface
            line: SettingsPalette.line
            gold: SettingsInk.gold
            carved: true
            foreground: worldPage.foreground
            title: Eitr.I18n.tr("Saved cities")

            Text {
                width: parent.width
                wrapMode: Text.Wrap
                text: worldPage.errorMessage !== ""
                    ? worldPage.errorMessage
                    : Eitr.I18n.tr("No saved cities yet. Add cities in the World Clock plugin settings to see them here.")
                color: worldPage.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }

        Repeater {
            model: worldPage.pluginInstalled ? worldPage.cities : []
            Rectangle {
                required property var modelData
                width: contentColumn.width
                implicitHeight: cityRow.implicitHeight + 24
                height: implicitHeight
                radius: DesktopStyle.radius(10)
                color: SettingsPalette.surface
                border.width: 1
                border.color: SettingsPalette.line

                readonly property string dayText: worldPage.formatDayDelta(worldPage.dayDelta(modelData))
                readonly property string offsetText: worldPage.formatOffset(worldPage.offsetFromLocal(modelData))
                readonly property string detailText: [dayText, offsetText, modelData.abbreviation || ""].filter(function(part) { return part !== ""; }).join(" · ")

                Item {
                    id: cityRow
                    anchors.fill: parent
                    anchors.margins: 12
                    implicitHeight: Math.max(cityInfo.implicitHeight, cityTime.implicitHeight)

                    Column {
                        id: cityInfo
                        anchors.left: parent.left
                        anchors.right: cityTime.left
                        anchors.rightMargin: 16
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 3

                        Row {
                            width: parent.width
                            spacing: 8

                            Text {
                                visible: (modelData.flag || "") !== ""
                                text: modelData.flag || ""
                                font.pixelSize: 16
                            }

                            Text {
                                text: modelData.name || modelData.zone
                                color: worldPage.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.headingSize
                                font.weight: Font.Medium
                                elide: Text.ElideRight
                            }

                            Rectangle {
                                visible: (modelData.label || "") !== ""
                                anchors.verticalCenter: parent.verticalCenter
                                radius: DesktopStyle.radius(4)
                                color: Qt.alpha(SettingsInk.gold, 0.16)
                                width: cityCode.implicitWidth + 10
                                height: 20
                                Text {
                                    id: cityCode
                                    anchors.centerIn: parent
                                    text: modelData.label || ""
                                    color: SettingsInk.gold
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.captionSize
                                    font.weight: Font.Medium
                                }
                            }
                        }

                        Text {
                            width: parent.width
                            text: detailText
                            color: worldPage.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.captionSize
                            elide: Text.ElideRight
                        }
                    }

                    Text {
                        id: cityTime
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        text: worldPage.cityTime(modelData)
                        color: worldPage.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: 26
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
            }
        }
    }
}
