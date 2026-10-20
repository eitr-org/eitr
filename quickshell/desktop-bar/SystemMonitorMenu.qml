import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    property int maximumHeight: 900
    property var sections: []
    property string error: ""
    readonly property var sectionIcons: ({CPU: "\u{F0EE0}", GPU: "\u{F08AE}", RAM: "\u{F035B}", Storage: "\u{F02CA}"})

    function refresh() {
        if (!query.running) query.running = true;
    }

    implicitWidth: 468
    implicitHeight: Math.min(content.implicitHeight + verticalContentInset, maximumHeight)
    leftAligned: true
    onOpenedChanged: if (opened) refresh()
    Timer { interval: 2000; repeat: true; running: menu.opened; onTriggered: menu.refresh() }
    Process {
        id: query
        command: ["python3", Quickshell.shellDir + "/scripts/system-details.py"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            try {
                if (code !== 0) throw new Error("query failed");
                menu.sections = JSON.parse(output.text).sections;
                menu.error = "";
            } catch (e) { menu.error = Eitr.I18n.tr("Hardware information unavailable"); }
        }
    }
    Flickable {
        anchors.fill: parent
        anchors.margins: 0
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: content
            width: parent.width
            spacing: 14
            Text {
                visible: menu.sections.length === 0 || menu.error !== ""
                text: menu.error || Eitr.I18n.tr("Loading...")
                color: menu.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.controlSize
            }
            Repeater {
                model: menu.sections
                Column {
                    id: section
                    required property var modelData
                    required property int index
                    width: content.width
                    spacing: 7
                    PanelDivider {
                        visible: section.index > 0
                        width: parent.width
                        height: 8
                        foreground: menu.foreground
                    }
                    Row {
                        width: parent.width
                        Item {
                            width: parent.width - 70
                            height: title.implicitHeight
                            Text {
                                width: 28
                                anchors.verticalCenter: parent.verticalCenter
                                horizontalAlignment: Text.AlignHCenter
                                text: menu.sectionIcons[section.modelData.title] || "󰍛"
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: 20
                            }
                            Text {
                                id: title
                                x: 38
                                width: parent.width - x
                                text: section.modelData.title
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.headingSize
                                font.bold: true
                            }
                        }
                        Text {
                            width: 70
                            horizontalAlignment: Text.AlignRight
                            text: section.modelData.usage === null ? "--" : section.modelData.usage + "%"
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.controlSize
                        }
                    }
                    Text {
                        width: parent.width
                        text: section.modelData.name
                        elide: Text.ElideRight
                        color: menu.foreground
                        opacity: 0.72
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.bodySize
                    }
                    Rectangle {
                        visible: section.modelData.usage !== null
                        width: parent.width
                        height: visible ? 5 : 0
                        radius: 3
                        color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.12)
                        Rectangle {
                            width: parent.width * Math.max(0, Math.min(100, section.modelData.usage || 0)) / 100
                            height: parent.height
                            radius: 3
                            color: menu.foreground
                        }
                    }
                    Repeater {
                        model: section.modelData.rows
                        Row {
                            required property var modelData
                            width: section.width
                            Text {
                                width: parent.width * 0.5
                                text: parent.modelData[0]
                                color: menu.foreground
                                opacity: 0.65
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.secondarySize
                            }
                            Text {
                                width: parent.width * 0.5
                                horizontalAlignment: Text.AlignRight
                                text: parent.modelData[1]
                                elide: Text.ElideRight
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.secondarySize
                            }
                        }
                    }
                }
            }
        }
    }
}
