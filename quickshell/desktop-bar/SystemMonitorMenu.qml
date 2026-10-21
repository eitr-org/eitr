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

    // Components whose details are unfolded this session (title -> true).
    property var expanded: ({})
    function toggle(title) { let next = Object.assign({}, expanded); next[title] = !next[title]; expanded = next; }

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
            // One big number per component; its details unfold on click.
            Repeater {
                model: menu.sections
                Column {
                    id: section
                    required property var modelData
                    required property int index
                    readonly property bool expanded: !!menu.expanded[modelData.title]
                    width: content.width
                    spacing: 8
                    PanelDivider {
                        visible: section.index > 0
                        width: parent.width
                        height: 8
                        foreground: menu.foreground
                    }
                    Item {
                        id: header
                        width: parent.width
                        height: 44
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: section.modelData.title
                        Keys.onPressed: function(event) {
                            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) { menu.toggle(section.modelData.title); event.accepted = true; }
                        }
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: -4
                            radius: DesktopStyle.radius(PanelStyle.controlRadius)
                            color: Qt.alpha(menu.foreground, headerMouse.containsMouse || header.activeFocus ? 0.08 : 0)
                        }
                        Text {
                            width: 28
                            anchors.verticalCenter: parent.verticalCenter
                            horizontalAlignment: Text.AlignHCenter
                            text: menu.sectionIcons[section.modelData.title] || "󰍛"
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: 20
                        }
                        Column {
                            x: 38
                            width: parent.width - x - usage.width - chevron.width - 16
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2
                            Text {
                                width: parent.width
                                text: section.modelData.title
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                                font.bold: true
                            }
                            Text {
                                width: parent.width
                                text: section.modelData.name
                                elide: Text.ElideRight
                                color: menu.foreground
                                opacity: PanelStyle.secondaryTextOpacity
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.secondarySize
                            }
                        }
                        Text {
                            id: usage
                            anchors.right: chevron.left
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: section.modelData.usage === null ? "--" : Math.round(section.modelData.usage) + "%"
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.figureSize
                            font.weight: Font.DemiBold
                            font.features: PanelStyle.tabularFigures
                        }
                        Text {
                            id: chevron
                            width: 16
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            horizontalAlignment: Text.AlignHCenter
                            text: section.expanded ? "\u{F0143}" : "\u{F0140}"
                            color: menu.foreground
                            opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family
                            font.pixelSize: 16
                        }
                        MouseArea {
                            id: headerMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: menu.toggle(section.modelData.title)
                        }
                    }
                    Rectangle {
                        visible: section.modelData.usage !== null
                        width: parent.width
                        height: visible ? 4 : 0
                        radius: 2
                        color: Qt.alpha(menu.foreground, 0.12)
                        Rectangle {
                            width: parent.width * Math.max(0, Math.min(100, section.modelData.usage || 0)) / 100
                            height: parent.height
                            radius: 2
                            color: menu.foreground
                        }
                    }
                    Column {
                        visible: section.expanded
                        width: parent.width
                        spacing: 4
                        Repeater {
                            model: section.modelData.rows
                            Row {
                                required property var modelData
                                width: parent.width
                                Text {
                                    width: parent.width * 0.5
                                    text: parent.modelData[0]
                                    color: menu.foreground
                                    opacity: PanelStyle.secondaryTextOpacity
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
                                    font.features: PanelStyle.tabularFigures
                                }
                            }
                        }
                    }
                }
            }
            PanelFooterLink {
                visible: menu.sections.length > 0
                text: Eitr.I18n.tr("Open System Monitor")
                foreground: menu.foreground
                onClicked: { menu.opened = false; Quickshell.execDetached(["kitty", "-e", "btop"]); }
            }
        }
    }
}
