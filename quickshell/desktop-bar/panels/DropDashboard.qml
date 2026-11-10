import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Drop's dashboard, opened by clicking its time pill: Dashboard (time and date, weather,
// the month, the song playing and quick shortcuts), Media (the full player) and
// Performance (CPU, GPU, RAM and storage rings from the hardware domain).
ThemedPopup {
    id: dashboard
    required property var barHost
    required property var player
    property bool hold: false
    property string tab: "dashboard"
    centered: true
    implicitWidth: 560
    implicitHeight: content.implicitHeight + verticalContentInset
    onOpenedChanged: if (!opened) tab = "dashboard"
    readonly property var weather: barHost.barWeather
    readonly property bool playing: !!player
    property date now: new Date()
    Timer { interval: 1000; running: dashboard.opened; repeat: true; triggeredOnStart: true; onTriggered: dashboard.now = new Date() }

    // Hardware is read only while the Performance tab is showing.
    property string hardwareToken: ""
    readonly property var hardware: DesktopData.topics["hardware.details"]
    readonly property var sections: hardware && hardware.data && hardware.data.sections ? hardware.data.sections : []
    readonly property bool watchingHardware: opened && tab === "performance"
    onWatchingHardwareChanged: {
        if (watchingHardware) hardwareToken = DesktopData.observe("hardware.details", dashboard);
        else if (hardwareToken) { DesktopData.release(hardwareToken); hardwareToken = ""; }
    }
    Component.onDestruction: DesktopData.releaseOwner(dashboard)

    component Card: Rectangle {
        radius: DesktopStyle.radius(PanelStyle.controlRadius + 4)
        color: Qt.alpha(dashboard.foreground, 0.06)
        border.width: 1
        border.color: Qt.alpha(dashboard.foreground, PanelStyle.selectionBorderAlpha)
    }
    component Caption: Text {
        color: dashboard.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }

    Column {
        id: content
        width: parent.width
        spacing: 12
        TabStrip {
            width: parent.width
            foreground: dashboard.foreground; gold: dashboard.accent
            choices: [{id: "dashboard", label: "Dashboard"}, {id: "media", label: "Media"}, {id: "performance", label: "Performance"}]
            current: dashboard.tab
            onChosen: value => dashboard.tab = value
        }

        // Dashboard: time and weather, then the month beside the song playing, then shortcuts.
        Column {
            visible: dashboard.tab === "dashboard"
            width: parent.width
            spacing: 10
            Row {
                width: parent.width
                spacing: 10
                Card {
                    width: (parent.width - parent.spacing) / 2; height: 96
                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: Qt.formatTime(dashboard.now, Qt.locale().timeFormat(Locale.ShortFormat))
                            color: dashboard.foreground; font.family: DesktopFonts.family; font.pixelSize: 38; font.weight: Font.DemiBold
                        }
                        Caption {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: dashboard.now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
                        }
                    }
                }
                Card {
                    width: (parent.width - parent.spacing) / 2; height: 96
                    Row {
                        anchors.centerIn: parent
                        spacing: 14
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: dashboard.weather ? dashboard.weather.text.split(" ")[0] : ""
                            color: dashboard.foreground; font.family: DesktopFonts.family; font.pixelSize: 34
                        }
                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2
                            Text {
                                text: dashboard.weather ? dashboard.weather.temperature : ""
                                color: dashboard.foreground; font.family: DesktopFonts.family; font.pixelSize: 26; font.weight: Font.DemiBold
                            }
                            Caption { text: dashboard.weather ? dashboard.weather.condition : "" }
                        }
                    }
                    MouseArea {
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                        onClicked: dashboard.barHost.togglePanel(dashboard.barHost.weatherMenu)
                    }
                }
            }
            Row {
                width: parent.width
                spacing: 10
                Card {
                    id: month
                    width: (parent.width - parent.spacing) / 2; height: 214
                    readonly property date first: new Date(dashboard.now.getFullYear(), dashboard.now.getMonth(), 1)
                    // Weeks start on the locale's first day; six rows always fit the month.
                    readonly property int lead: (first.getDay() - Qt.locale().firstDayOfWeek % 7 + 7) % 7
                    Column {
                        anchors.fill: parent; anchors.margins: 10
                        spacing: 6
                        Text {
                            text: dashboard.now.toLocaleDateString(Qt.locale(), "MMMM yyyy")
                            color: dashboard.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                        }
                        Grid {
                            columns: 7
                            Repeater {
                                model: 7
                                Caption {
                                    required property int index
                                    width: (month.width - 20) / 7; horizontalAlignment: Text.AlignHCenter
                                    text: Qt.locale().dayName((Qt.locale().firstDayOfWeek + index) % 7, Locale.NarrowFormat)
                                }
                            }
                            Repeater {
                                model: 42
                                Item {
                                    required property int index
                                    readonly property date day: new Date(month.first.getFullYear(), month.first.getMonth(), index - month.lead + 1)
                                    readonly property bool inMonth: day.getMonth() === month.first.getMonth()
                                    readonly property bool today: inMonth && day.getDate() === dashboard.now.getDate()
                                    width: (month.width - 20) / 7; height: 23
                                    Rectangle {
                                        anchors.centerIn: parent; width: 22; height: 22; radius: 11
                                        visible: parent.today; color: dashboard.accent
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: parent.day.getDate()
                                        color: parent.today ? PanelStyle.readableInk(dashboard.accent, dashboard.foreground, dashboard.background) : dashboard.foreground
                                        opacity: parent.inMonth ? 1 : 0.35
                                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                                    }
                                }
                            }
                        }
                    }
                    MouseArea {
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                        onClicked: dashboard.barHost.togglePanel(dashboard.barHost.calendarMenu)
                    }
                }
                Card {
                    width: (parent.width - parent.spacing) / 2; height: 214
                    clip: true
                    MediaCard {
                        visible: dashboard.playing
                        anchors.fill: parent; anchors.margins: 10
                        compact: true
                        player: dashboard.player; hold: dashboard.hold; active: dashboard.opened && dashboard.tab === "dashboard"
                        foreground: dashboard.foreground; accent: dashboard.accent
                    }
                    Caption {
                        visible: !dashboard.playing
                        anchors.centerIn: parent
                        text: Eitr.I18n.tr("Nothing playing")
                    }
                }
            }
            Row {
                spacing: 8
                Repeater {
                    model: [{glyph: "󰖩", label: "WiFi", panel: "wifiMenu"},
                            {glyph: "󰂯", label: "Bluetooth", panel: "bluetoothMenu"},
                            {glyph: "󰕾", label: "Sound", panel: "volumeMenu"},
                            {glyph: "󰂚", label: "Notifications", panel: "notificationCenter"},
                            {glyph: "󰒓", label: "Control Center", panel: "controlCenter"}]
                    PanelButton {
                        required property var modelData
                        width: 40; height: 40; icon: true; outlined: true
                        text: modelData.glyph; foreground: dashboard.foreground
                        Accessible.name: Eitr.I18n.tr(modelData.label)
                        onClicked: dashboard.barHost.togglePanel(dashboard.barHost[modelData.panel])
                    }
                }
            }
        }

        // Media: the whole player.
        Card {
            visible: dashboard.tab === "media"
            width: parent.width; height: 320
            clip: true
            MediaCard {
                visible: dashboard.playing
                anchors.fill: parent; anchors.margins: 12
                player: dashboard.player; hold: dashboard.hold; active: dashboard.opened && dashboard.tab === "media"
                foreground: dashboard.foreground; accent: dashboard.accent
            }
            Caption { visible: !dashboard.playing; anchors.centerIn: parent; text: Eitr.I18n.tr("Nothing playing") }
        }

        // Performance: one ring per component, from the same data as the Hardware panel.
        Row {
            visible: dashboard.tab === "performance"
            width: parent.width
            spacing: 10
            Repeater {
                model: dashboard.sections
                Card {
                    id: ring
                    required property var modelData
                    readonly property real share: Math.max(0, Math.min(1, (parseFloat(modelData.usage) || 0) / 100))
                    width: (parent.width - parent.spacing * (dashboard.sections.length - 1)) / Math.max(1, dashboard.sections.length)
                    height: 150
                    Canvas {
                        id: arc
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: 14; width: 92; height: 92
                        readonly property real share: ring.share
                        onShareChanged: requestPaint()
                        onPaint: {
                            const context = getContext("2d");
                            context.reset();
                            context.lineWidth = 7; context.lineCap = "round";
                            context.strokeStyle = Qt.alpha(dashboard.foreground, 0.15);
                            context.beginPath(); context.arc(46, 46, 40, 0, Math.PI * 2); context.stroke();
                            context.strokeStyle = dashboard.accent;
                            context.beginPath(); context.arc(46, 46, 40, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * share); context.stroke();
                        }
                    }
                    Text {
                        anchors.centerIn: arc
                        text: ring.modelData.usage
                        color: dashboard.foreground; font.family: DesktopFonts.family; font.pixelSize: 16; font.weight: Font.DemiBold
                    }
                    Caption {
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: arc.y + arc.height + 10
                        text: ring.modelData.title
                    }
                }
            }
            Caption {
                visible: dashboard.sections.length === 0
                text: Eitr.I18n.tr("Loading…")
            }
        }
    }
}
