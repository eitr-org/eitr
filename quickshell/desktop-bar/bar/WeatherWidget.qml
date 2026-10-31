import ".."
import QtQuick
import Eitr as Eitr

Item {
    id: weather
    property var host
    signal clicked()
    property bool autoRefresh: true
    property bool compact: false
    property string text: "󰖐"
    property string location: ""
    property string condition: ""
    property string temp: ""
    property string feels: ""
    property string wind: ""
    property string humidity: ""
    property string forecast: ""
    property var latestData: ({})
    property int dataRevision: 0
    readonly property var snapshot: DesktopData.topics["weather.default"]
    function refresh() { DesktopData.refresh("weather.default"); }
    onSnapshotChanged: if (snapshot && snapshot.data.temp) updateData(snapshot.data)
    function updateData(data) {
        dataRevision++;
        latestData = data;
        weather.text = String(data.text || weather.text);
        weather.location = String(data.location || "");
        weather.condition = String(data.condition || "");
        weather.temp = String(data.temp || "");
        weather.feels = String(data.feels || "");
        weather.wind = String(data.wind || "");
        weather.humidity = String(data.humidity || "");
        weather.forecast = String(data.forecast || "");
    }

    readonly property string temperature: weather.temp || (weather.text.indexOf(" ") >= 0 ? weather.text.slice(weather.text.indexOf(" ") + 1).trim() : "")
    readonly property real contentWidth: Math.max(26, label.implicitWidth + 8)
    width: contentWidth
    height: 24
    Component.onCompleted: if (autoRefresh) DesktopData.observe("weather.default", weather)
    Component.onDestruction: DesktopData.releaseOwner(weather)

    Row {
        id: label
        anchors.centerIn: parent
        spacing: 3
        Text {
            text: weather.text.split(" ")[0]
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: weather.compact ? 12 : 14
            font.bold: true
        }
        Text {
            visible: !weather.compact
            text: weather.temperature
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: weather.compact ? 12 : 14
            font.bold: true
        }
    }

    MouseArea {
        id: weatherMouse
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: weather.clicked()
    }

    BarTooltip {
        background: host.workspaceMenuBg
        foreground: host.fg
        target: weather
        hovered: weatherMouse.containsMouse
        // Vertical bars show only the icon; the temperature moves to the tooltip.
        text: weather.compact && weather.temperature ? Eitr.I18n.tr("Weather") + " · " + weather.temperature : Eitr.I18n.tr("Weather")
    }

}
