import ".."
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../ChoiceLists.js" as ChoiceLists

Flickable {
    id: overview
    required property color foreground
    required property color background
    required property color accent
    property bool observing: false
    property bool live: true
    property var hardware: DesktopData.topics["hardware.details"] || ({})
    property var account: (DesktopData.topics["account.picture"] || {}).data || ({})
    property var themePalette: ({})
    property string version: ""
    property bool sourceRelease: false
    property string channel: ""
    property real uptimeSeconds: 0
    property url artSource: ""
    property var tokens: []
    readonly property var monitor: DisplayService.topology.monitors.find(display => display.name === DisplayService.topology.primary) || DisplayService.topology.monitors[0] || ({})
    readonly property var sections: (hardware.data || {}).sections || []
    readonly property string unavailable: Eitr.I18n.tr("Unavailable")
    function updateDemand() {
        DesktopData.releaseOwner(overview);
        tokens = [];
        if (!observing) { paletteReload.stop(); return; }
        tokens = [DesktopData.observe("hardware.details", overview), DesktopData.observe("account.picture", overview)];
        if (live) {
            uptime.reload(); release.reload(); appearance.reload();
            paletteReload.restart(); channelQuery.running = true;
        }
    }
    onObservingChanged: updateDemand()
    Component.onCompleted: if (observing) updateDemand()
    Component.onDestruction: DesktopData.releaseOwner(overview)
    contentHeight: dashboard.height
    boundsBehavior: Flickable.StopAtBounds; clip: true
    ScrollBar.vertical: ScrollBar {
        width: 4; policy: ScrollBar.AsNeeded
        contentItem: Rectangle { radius: 2; color: Qt.alpha(overview.foreground, 0.25) }
    }
    FileView {
        id: uptime
        path: overview.observing && overview.live ? "/proc/uptime" : ""
        printErrors: false
        onLoaded: overview.uptimeSeconds = Number(text().trim().split(/\s+/)[0]) || 0
    }
    Timer { interval: 30000; running: overview.observing; repeat: true; onTriggered: uptime.reload() }
    FileView {
        id: release
        onLoadFailed: if (!overview.sourceRelease) overview.sourceRelease = true
        path: overview.live ? Eitr.Paths.code(overview.sourceRelease ? "distro/release.json" : "release.json") : ""
        printErrors: false
        onLoaded: {
            try { const data = JSON.parse(text()); overview.version = data.version + " · " + data.codename; }
            catch (error) { console.warn("Invalid release metadata:", error); }
        }
    }
    FileView {
        id: appearance
        path: overview.live ? Eitr.Paths.config("eitr/appearance.json") : ""
        printErrors: false; watchChanges: overview.observing
        onFileChanged: if (overview.observing) reload()
        onLoaded: {
            try { const path = Eitr.Paths.settings(text()).wallpaper || ""; overview.artSource = path ? "file://" + path : ""; }
            catch (error) { console.warn("Invalid appearance settings:", error); }
        }
    }
    PreferenceWatch {
        path: overview.live ? Eitr.Paths.config("theme/current/colors.toml") : ""
        ancestor: overview.live ? Eitr.Paths.config("theme") : ""
        onChanged: if (overview.observing) paletteReload.restart()
    }
    Timer {
        id: paletteReload
        interval: 40
        onTriggered: {
            if (!overview.observing) return;
            if (paletteQuery.running) restart();
            else paletteQuery.running = true;
        }
    }
    Timer {
        interval: 5000; running: paletteQuery.running || channelQuery.running
        onTriggered: { paletteQuery.running = false; channelQuery.running = false; }
    }
    Process {
        id: paletteQuery
        command: ["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/workspace-color.py")]
        stdout: StdioCollector { onStreamFinished: {
            try { overview.themePalette = JSON.parse(text).palette || ({}); }
            catch (error) { console.warn("Invalid theme palette:", error); }
        } }
    }
    Process {
        id: channelQuery
        command: ["/usr/lib/eitr/eitr-system", "channel-status"]
        stdout: StdioCollector { onStreamFinished: overview.channel = text.trim() }
    }
    component Caption: Text {
        color: SettingsInk.gold
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        wrapMode: Text.WordWrap
    }
    component Heading: Text {
        color: overview.foreground; font.family: SiteStyle.carved; font.pixelSize: PanelStyle.headingSize
    }
    Column {
        id: dashboard
        width: overview.width; spacing: 26
        SettingsPageHeader { page: "system"; foreground: overview.foreground }
        Row {
            spacing: 18
            Eitr.Avatar {
                size: 64
                source: overview.account.path ? "file://" + overview.account.path + "?v=" + (overview.account.version || 0) : ""
                initial: overview.account.initial || ""
                accent: overview.accent; background: overview.background
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter; spacing: 6
                Heading { text: overview.account.name || Eitr.I18n.tr("You") }
                Caption { text: Eitr.I18n.tr("Your desktop, at a glance") }
            }
        }
        Rectangle {
            width: parent.width; height: Math.max(180, Math.min(240, overview.height * 0.28))
            radius: DesktopStyle.radius(16); color: Qt.tint(overview.background, Qt.alpha(overview.accent, 0.12)); clip: true
            Image { anchors.fill: parent; source: overview.artSource; fillMode: Image.PreserveAspectCrop; sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio) }
            Canvas {
                anchors.fill: parent
                property real corner: parent.radius
                property color ink: overview.background
                onCornerChanged: requestPaint()
                onInkChanged: requestPaint()
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d");
                    context.reset(); context.fillStyle = ink;
                    context.beginPath(); context.rect(0, 0, width, height);
                    context.moveTo(corner, 0); context.quadraticCurveTo(0, 0, 0, corner);
                    context.lineTo(0, height - corner); context.quadraticCurveTo(0, height, corner, height);
                    context.lineTo(width - corner, height); context.quadraticCurveTo(width, height, width, height - corner);
                    context.lineTo(width, corner); context.quadraticCurveTo(width, 0, width - corner, 0);
                    context.closePath(); context.fill();
                }
            }
            Caption { visible: !overview.artSource.toString(); anchors.centerIn: parent; text: Eitr.I18n.tr("Current wallpaper") }
        }
        Row {
            width: parent.width; spacing: 14
            Repeater {
                model: ["CPU", "GPU", "RAM"]
                Rectangle {
                    id: metric
                    required property string modelData
                    readonly property var section: overview.sections.find(entry => entry.title === modelData) || ({})
                    width: (dashboard.width - 28) / 3; height: 116
                    radius: DesktopStyle.radius(10)
                    color: Qt.alpha(overview.foreground, 0.04)
                    border.width: 1; border.color: Qt.alpha(overview.foreground, PanelStyle.dividerAlpha)
                    Column {
                        anchors.fill: parent; anchors.margins: 14; spacing: 8
                        Caption { text: Eitr.I18n.tr(metric.modelData) }
                        Text { text: typeof metric.section.usage === "number" ? Math.round(metric.section.usage) + "%" : "—"; color: overview.foreground; font.family: DesktopFonts.family; font.pixelSize: 30; font.features: PanelStyle.tabularFigures }
                        Caption { width: parent.width; text: metric.section.name || overview.unavailable; maximumLineCount: 1; elide: Text.ElideRight }
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true; title: Eitr.I18n.tr("System information"); foreground: overview.foreground
        GridLayout {
            width: parent.width; columns: width > 520 ? 2 : 1; columnSpacing: 28; rowSpacing: 20
            ColumnLayout {
                Layout.fillWidth: true; spacing: 6
                Caption { text: Eitr.I18n.tr("Eitr version") }
                Heading { text: overview.version || overview.unavailable }
                Caption { text: Eitr.I18n.tr("Update channel: %1", [overview.channel ? Eitr.I18n.tr(ChoiceLists.label(ChoiceLists.updateChannels, overview.channel)) : overview.unavailable]) }
            }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 6
                Caption { text: Eitr.I18n.tr("Main display") }
                Heading { text: overview.monitor.width ? overview.monitor.width + " × " + overview.monitor.height : overview.unavailable }
                Caption { text: overview.monitor.refreshRate ? Eitr.I18n.tr("%1 Hz", [Number(overview.monitor.refreshRate).toFixed(1)]) : overview.unavailable }
            }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 6
                Caption { text: Eitr.I18n.tr("Uptime") }
                Heading { text: overview.uptimeSeconds ? Eitr.I18n.tr("%1 h %2 min", [Math.floor(overview.uptimeSeconds / 3600), Math.floor(overview.uptimeSeconds / 60) % 60]) : overview.unavailable }
            }
        }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Theme palette"); foreground: overview.foreground
            Flow {
                width: parent.width; spacing: 8
                Repeater {
                    model: ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"].filter(key => /^#[0-9a-f]{6}$/i.test(String(overview.themePalette[key])))
                    Rectangle { required property string modelData; width: 28; height: 28; radius: DesktopStyle.radius(6); color: overview.themePalette[modelData]; border.width: 1; border.color: Qt.alpha(overview.foreground, 0.15); Accessible.name: modelData + " " + color }
                }
            }
        }
    }
}
