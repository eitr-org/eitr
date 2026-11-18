import ".."
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: root
    required property var centerRef
    required property color foreground
    required property color background
    required property color accent

    property bool diskRunning: false
    property bool networkRunning: false
    property var diskResult: null
    property var networkResult: null
    property string diskError: ""
    property string networkError: ""
    property string diskQueryId: ""
    property string networkQueryId: ""

    function runDisk() {
        if (diskRunning) return;
        diskRunning = true;
        diskError = "";
        diskQueryId = DesktopData.querySpeed("disk", {}, root, function(error, data) {
            root.diskQueryId = "";
            root.diskRunning = false;
            if (error) {
                root.diskError = error === "timeout"
                    ? Eitr.I18n.tr("Disk test timed out.")
                    : Eitr.I18n.tr("Disk test failed.");
                return;
            }
            if (data && data.kind === "disk") root.diskResult = data;
        });
    }

    function cancelDisk() {
        if (diskQueryId) {
            DesktopData.cancelQuery(diskQueryId);
            diskQueryId = "";
        }
        diskRunning = false;
    }

    function runNetwork() {
        if (networkRunning) return;
        networkRunning = true;
        networkError = "";
        networkQueryId = DesktopData.querySpeed("network", {}, root, function(error, data) {
            root.networkQueryId = "";
            root.networkRunning = false;
            if (error) {
                root.networkError = error === "timeout"
                    ? Eitr.I18n.tr("Network test timed out.")
                    : Eitr.I18n.tr("Network test failed.");
                return;
            }
            if (data && data.kind === "network") root.networkResult = data;
        });
    }

    function cancelNetwork() {
        if (networkQueryId) {
            DesktopData.cancelQuery(networkQueryId);
            networkQueryId = "";
        }
        networkRunning = false;
    }

    Component.onDestruction: {
        cancelDisk();
        cancelNetwork();
    }

    width: parent ? parent.width : 0
    spacing: 12

    Rectangle {
        width: parent.width
        implicitHeight: diskCol.implicitHeight + 24
        radius: DesktopStyle.radius(10)
        color: Qt.alpha(root.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(root.foreground, 0.15)

        Column {
            id: diskCol
            x: 12; y: 12
            width: parent.width - 24
            spacing: 10
            RowLayout {
                width: parent.width
                Text {
                    Layout.fillWidth: true
                    text: Eitr.I18n.tr("Disk")
                    color: root.accent
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    font.weight: Font.Bold
                }
                PanelLoadingIndicator {
                    width: 20; height: 20
                    visible: root.diskRunning
                    busy: root.diskRunning
                    foreground: root.foreground; background: root.background
                }
            }
            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                text: Eitr.I18n.tr("Sequential write and read of a 256 MB temporary file in your cache folder on the root drive.")
                color: root.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            RowLayout {
                visible: !!root.diskResult
                width: parent.width
                spacing: 16
                Column {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Write speed")
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Text {
                        text: root.diskResult ? Eitr.I18n.tr("%1 MB/s", [String(root.diskResult.writeMBps)]) : ""
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.figureSize
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
                Column {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Read speed")
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Text {
                        text: root.diskResult ? Eitr.I18n.tr("%1 MB/s", [String(root.diskResult.readMBps)]) : ""
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.figureSize
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
            }
            Text {
                visible: root.diskError !== ""
                width: parent.width
                wrapMode: Text.WordWrap
                text: root.diskError
                color: root.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            PanelButton {
                width: parent.width; height: 32
                text: root.diskRunning ? Eitr.I18n.tr("Cancel") : Eitr.I18n.tr("Run Disk Test")
                leadingIcon: root.diskRunning ? "󰅖" : "󰋊"
                foreground: root.foreground
                onClicked: if (root.diskRunning) root.cancelDisk(); else root.runDisk()
            }
        }
    }

    Rectangle {
        width: parent.width
        implicitHeight: netCol.implicitHeight + 24
        radius: DesktopStyle.radius(10)
        color: Qt.alpha(root.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(root.foreground, 0.15)

        Column {
            id: netCol
            x: 12; y: 12
            width: parent.width - 24
            spacing: 10
            RowLayout {
                width: parent.width
                Text {
                    Layout.fillWidth: true
                    text: Eitr.I18n.tr("Network")
                    color: root.accent
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    font.weight: Font.Bold
                }
                PanelLoadingIndicator {
                    width: 20; height: 20
                    visible: root.networkRunning
                    busy: root.networkRunning
                    foreground: root.foreground; background: root.background
                }
            }
            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                text: Eitr.I18n.tr("Contacts speed.cloudflare.com over HTTPS to measure latency, download and upload.")
                color: root.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            RowLayout {
                visible: !!root.networkResult
                width: parent.width
                spacing: 12
                Column {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Latency")
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Text {
                        text: root.networkResult ? Eitr.I18n.tr("%1 ms", [String(root.networkResult.latencyMs)]) : ""
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.figureSize
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
                Column {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Download")
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Text {
                        text: root.networkResult ? Eitr.I18n.tr("%1 Mbps", [String(root.networkResult.downloadMbps)]) : ""
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.figureSize
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
                Column {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Upload")
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Text {
                        text: root.networkResult ? Eitr.I18n.tr("%1 Mbps", [String(root.networkResult.uploadMbps)]) : ""
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.figureSize
                        font.weight: Font.Bold
                        font.features: PanelStyle.tabularFigures
                    }
                }
            }
            Text {
                visible: root.networkError !== ""
                width: parent.width
                wrapMode: Text.WordWrap
                text: root.networkError
                color: root.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            PanelButton {
                width: parent.width; height: 32
                text: root.networkRunning ? Eitr.I18n.tr("Cancel") : Eitr.I18n.tr("Run Network Test")
                leadingIcon: root.networkRunning ? "󰅖" : "󰖟"
                foreground: root.foreground
                onClicked: if (root.networkRunning) root.cancelNetwork(); else root.runNetwork()
            }
        }
    }
}
