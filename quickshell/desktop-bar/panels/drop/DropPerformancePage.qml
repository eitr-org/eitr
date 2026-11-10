import "../.."
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle

// Drop's Performance page, flat like the home page: CPU, GPU, RAM and storage in a 2×2
// grid split by thin rules, each with a usage ring, its model name and its key figures,
// from the Hardware panel's data. The hardware domain is observed only while this page shows.
Item {
    id: page
    required property color foreground
    required property color accent
    required property bool watching
    property string token: ""
    readonly property var hardware: DesktopData.topics["hardware.details"]
    readonly property var sections: hardware && hardware.data && hardware.data.sections ? hardware.data.sections.slice(0, 4) : []
    readonly property var icons: ({CPU: "\u{F0EE0}", GPU: "\u{F08AE}", RAM: "\u{F035B}", Storage: "\u{F02CA}"})
    // The figures worth a glance per component, by their row labels in the hardware data,
    // each worded so it reads on its own.
    readonly property var highlights: ({
        CPU: [["Frequency / temperature", value => value], ["Cores / threads", value => value.replace(/(\d+) \/ (\d+)/, Eitr.I18n.tr("%1 cores · %2 threads").replace("%1", "$1").replace("%2", "$2"))]],
        GPU: [["VRAM used / total", value => Eitr.I18n.tr("VRAM") + " " + value.replace(" GiB /", " /")], ["Temperature", value => Math.round(parseFloat(value)) + "°C"]],
        RAM: [["Used / total", value => value.replace(" GiB /", " /") + " " + Eitr.I18n.tr("used")], ["Swap used / total", value => Eitr.I18n.tr("Swap") + " " + value.replace(" GiB /", " /")]],
        Storage: [["Used / total", value => value + " " + Eitr.I18n.tr("used")], ["Free", value => value + " " + Eitr.I18n.tr("free")]]})
    onWatchingChanged: {
        if (watching) token = DesktopData.observe("hardware.details", page);
        else if (token) { DesktopData.release(token); token = ""; }
    }
    Component.onDestruction: DesktopData.releaseOwner(page)
    implicitHeight: 2 * cellHeight + 1
    readonly property real cellHeight: 104

    // Model names without the trademark clutter: "Intel Core i9-11900K" rather than
    // "11th Gen Intel(R) Core(TM) i9-11900K @ 3.50GHz".
    function shortName(name) {
        return String(name || "").replace(/\((R|TM|tm)\)/g, "").replace(/\s*@.*$/, "").replace(/^\d+(st|nd|rd|th) Gen /, "")
            .replace(/\s*(CPU|Processor)\b/g, "").replace(/\bGeForce /, "").split(" · ").slice(0, 2).join(" ")
            .replace(/\s+/g, " ").trim();
    }
    function figure(section, pick) {
        const row = (section.rows || []).find(row => row[0] === pick[0]);
        return row && row[1] ? pick[1](String(row[1])) : "";
    }

    Rectangle { x: page.width / 2; y: 6; width: 1; height: page.height - 12; color: Qt.alpha(page.foreground, 0.14); visible: page.sections.length > 1 }
    Rectangle { x: 6; y: page.cellHeight; width: page.width - 12; height: 1; color: Qt.alpha(page.foreground, 0.14); visible: page.sections.length > 2 }

    Repeater {
        model: page.sections
        Item {
            id: cell
            required property var modelData
            required property int index
            readonly property real share: Math.max(0, Math.min(1, (parseFloat(modelData.usage) || 0) / 100))
            readonly property var picks: page.highlights[modelData.title] || []
            x: (index % 2) * (page.width / 2 + 1); y: Math.floor(index / 2) * (page.cellHeight + 1)
            width: page.width / 2; height: page.cellHeight
            Canvas {
                id: arc
                x: 14; anchors.verticalCenter: parent.verticalCenter
                width: 66; height: 66
                property real share: cell.share
                Behavior on share { NumberAnimation { duration: DesktopStyle.motionDuration(500); easing.type: Easing.OutCubic } }
                onShareChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d");
                    context.reset();
                    context.lineWidth = 5; context.lineCap = "round";
                    context.strokeStyle = Qt.alpha(page.foreground, 0.12);
                    context.beginPath(); context.arc(33, 33, 29, 0, Math.PI * 2); context.stroke();
                    if (share <= 0) return;
                    context.strokeStyle = page.accent;
                    context.beginPath(); context.arc(33, 33, 29, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * share); context.stroke();
                }
            }
            Text {
                anchors.centerIn: arc
                text: cell.modelData.usage === null ? "--" : Math.round(cell.modelData.usage) + "%"
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 15; font.weight: Font.Bold
                font.features: PanelStyle.tabularFigures
            }
            Column {
                x: arc.x + arc.width + 14; anchors.verticalCenter: parent.verticalCenter
                width: cell.width - x - 12
                spacing: 3
                Row {
                    spacing: 6
                    Text { text: page.icons[cell.modelData.title] || "󰍛"; color: page.accent; font.family: PanelStyle.fontFamily; font.pixelSize: 13 }
                    Text {
                        text: cell.modelData.title
                        color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.Bold
                        font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
                    }
                }
                Text {
                    width: parent.width
                    text: page.shortName(cell.modelData.name)
                    color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.weight: Font.DemiBold
                    elide: Text.ElideRight; textFormat: Text.PlainText
                }
                Repeater {
                    model: cell.picks.map(pick => page.figure(cell.modelData, pick)).filter(Boolean)
                    Text {
                        required property string modelData
                        width: parent.width
                        text: modelData
                        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.features: PanelStyle.tabularFigures
                        elide: Text.ElideRight; textFormat: Text.PlainText
                    }
                }
            }
        }
    }
    Text {
        anchors.centerIn: parent
        visible: page.sections.length === 0
        text: Eitr.I18n.tr("Loading…")
        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
}
