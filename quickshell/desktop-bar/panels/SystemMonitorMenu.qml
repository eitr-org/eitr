import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle
import "../NetworkStatus.js" as NetworkStatus
import Quickshell

ThemedPopup {
    id: menu
    waitForFreshData: true
    property int maximumHeight: 900
    property var identity: null
    signal identityReceived(var identity)
    property var sections: []
    property string error: ""
    readonly property var sectionIcons: ({CPU: "\u{F0EE0}", GPU: "\u{F08AE}", RAM: "\u{F035B}", Storage: "\u{F02CA}"})

    // Components whose details are unfolded this session (title -> true).
    property var expanded: ({})
    function toggle(title) { let next = Object.assign({}, expanded); next[title] = !next[title]; expanded = next; }

    property string hardwareToken: ""
    readonly property var hardwareSnapshot: DesktopData.topics["hardware.details"]
    function refresh() { DesktopData.refresh("hardware.details"); }
    function receiveSnapshot() {
        const snapshot = hardwareSnapshot;
        if (!opened || !snapshot) return;
        menu.updateContent(function() {
            if (snapshot.data && snapshot.data.sections) {
                menu.identity = snapshot.data.identity;
                menu.identityReceived(menu.identity);
                menu.applySnapshot("sections", snapshot.data.sections);
            }
            menu.error = snapshot.status === "stale" || snapshot.status === "unavailable"
                ? Eitr.I18n.tr("Hardware information unavailable") : "";
        });
    }
    onHardwareSnapshotChanged: receiveSnapshot()
    // Network comes last, from the bar's own network data: speed is read only while the panel is open.
    property string trafficToken: ""
    // Usage colours: the panel's own below 75%, warning from 75%, critical from 90%.
    function levelColor(usage) {
        return usage === null || usage === undefined || usage < 75 ? foreground : usage < 90 ? DesktopStyle.warningColor : DesktopStyle.criticalColor;
    }
    readonly property var allSections: sections.length ? sections.concat([networkSection]) : []
    readonly property var traffic: (DesktopData.topics["throughput.network"] || {}).data || ({})
    readonly property var networkSummary: (DesktopData.topics["network.summary"] || {}).data || ({})
    function speed(bytes) {
        return NetworkStatus.speed(bytes, [Eitr.I18n.tr("%1 B/s"), Eitr.I18n.tr("%1 KB/s"), Eitr.I18n.tr("%1 MB/s"), Eitr.I18n.tr("%1 GB/s")]);
    }
    readonly property string connection: networkSummary.wired ? Eitr.I18n.tr("Wired")
        : NetworkStatus.connectionName(networkSummary) || Eitr.I18n.tr("Not connected")
    readonly property var networkSection: ({
        title: Eitr.I18n.tr("Network"), icon: "\u{F0200}", name: connection, usage: null,
        figure: "↓ " + speed(traffic.download),
        rows: [[Eitr.I18n.tr("Connection"), connection],
               [Eitr.I18n.tr("Download"), speed(traffic.download)],
               [Eitr.I18n.tr("Upload"), speed(traffic.upload)],
               [Eitr.I18n.tr("Adapters"), (traffic.interfaces || []).join(", ") || "—"]]
    })
    Component.onDestruction: DesktopData.releaseOwner(menu)
    implicitWidth: 468
    implicitHeight: Math.min(content.implicitHeight + verticalContentInset, maximumHeight)
    leftAligned: true
    onOpenedChanged: {
        if (opened) {
            hardwareToken = DesktopData.observe("hardware.details", menu);
            trafficToken = DesktopData.observe("throughput.network", menu);
            receiveSnapshot();
        } else {
            DesktopData.release(hardwareToken);
            DesktopData.release(trafficToken);
            hardwareToken = "";
            trafficToken = "";
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
            // The model is the count, not the list: a refresh replaces the list every two seconds,
            // and rebuilding the sections would reset the pointer under the cursor each time.
            Repeater {
                model: menu.allSections.length
                Column {
                    id: section
                    required property int index
                    readonly property var modelData: menu.allSections[index] || ({title: "", name: "", usage: null, rows: []})
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
                        Text {
                            width: 28
                            anchors.verticalCenter: parent.verticalCenter
                            horizontalAlignment: Text.AlignHCenter
                            text: section.modelData.icon || menu.sectionIcons[section.modelData.title] || "󰍛"
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
                            text: section.modelData.figure !== undefined ? section.modelData.figure
                                : section.modelData.usage === null ? "--" : Math.round(section.modelData.usage) + "%"
                            color: menu.levelColor(section.modelData.usage)
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
                    // The usage bar is part of the details, shown when the section unfolds.
                    Rectangle {
                        visible: section.expanded && section.modelData.usage !== null
                        width: parent.width
                        height: visible ? 4 : 0
                        radius: 2
                        color: Qt.alpha(menu.foreground, 0.12)
                        Rectangle {
                            width: parent.width * Math.max(0, Math.min(100, section.modelData.usage || 0)) / 100
                            height: parent.height
                            radius: 2
                            color: menu.levelColor(section.modelData.usage)
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
                onClicked: { menu.opened = false; Quickshell.execDetached([Eitr.Paths.code("walker/bin/menu-path/kitty"), "-e", "btop"]); }
            }
        }
    }
}
