pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

Item {
    id: host
    required property var entry
    required property color foreground
    required property color background
    required property color accent
    property bool active: true
    readonly property bool live: active && visible && enabled && opacity > 0 && !entry.disabled && error === ""
    property bool surface: entry.kind !== "barItems"
    readonly property bool barItem: entry.kind === "barItems"
    property string error: ""
    readonly property var menuEntries: api.menuEntries
    function menuSelect(id) { api.menuTriggered(id); }
    onActiveChanged: if (!active) { error = ""; api.detail = ""; api.menuEntries = []; }
    signal panelRequested(string plugin, string panel)
    signal failed(string plugin)
    readonly property bool tile: entry.kind === "tiles"
    readonly property string detail: entry.disabled ? Eitr.I18n.tr("Disabled") : error !== "" ? Eitr.I18n.tr("Could not load") : api.detail
    implicitHeight: tile ? PanelStyle.selectionRowHeight : error !== "" || entry.disabled ? 56 : Math.max(36, content.item ? content.item.implicitHeight : 36)
    activeFocusOnTab: tile || barItem
    function activate() {
        if ((tile || barItem) && entry.panel && !entry.disabled && error === "") panelRequested(entry.plugin, entry.panel);
    }
    Keys.onReturnPressed: activate()
    Keys.onEnterPressed: activate()
    Keys.onSpacePressed: activate()

    clip: true
    readonly property string helper: Eitr.Paths.code("walker/scripts/actions/install/plugins.py")
    function fail(message) {
        if (error !== "") return;
        error = String(message);
        console.warn("Plugin QML", entry.plugin, entry.id, error);
        if (!failure.running) {
            failure.running = true;
        }
        failed(entry.plugin);
    }
    QtObject {
        id: api
        property string detail: ""
        property var menuEntries: []
        signal menuTriggered(string id)
        function setMenu(entries) {
            if (!Array.isArray(entries) || entries.length > 20) return;
            const ids = [];
            const result = [];
            for (const entry of entries) {
                if (!entry || typeof entry.id !== "string" || !/^[a-z0-9-]{1,64}$/.test(entry.id)
                    || ids.indexOf(entry.id) !== -1 || typeof entry.text !== "string" || !entry.text.trim()
                    || entry.text.length > 72 || /[\x00-\x1f\x7f]/.test(entry.text)
                    || (entry.checked !== undefined && typeof entry.checked !== "boolean")) return;
                ids.push(entry.id);
                result.push({id: entry.id, text: entry.text, checked: entry.checked === true});
            }
            menuEntries = result;
        }
        property int spectrumBars: 64
        property bool spectrumSmoothing: false
        property int spectrumFrameRate: 30
        readonly property var spectrum: spectrumConsumer.spectrum
        readonly property bool audioActive: spectrumConsumer.audioActive
        readonly property string streamLine: host.latestLine
        signal streamReceived(string line)
        readonly property color foreground: host.foreground
        readonly property color background: host.background
        readonly property color accent: host.accent
        readonly property string fontFamily: DesktopFonts.family
        readonly property int bodySize: PanelStyle.bodySize
        readonly property int captionSize: PanelStyle.captionSize
        readonly property int headingSize: PanelStyle.headingSize
        readonly property real radius: DesktopStyle.radius(PanelStyle.controlRadius)
        readonly property string title: host.entry.title
        readonly property string icon: host.entry.icon || ""
        readonly property bool loading: data.running
        readonly property string dataText: dataOutput.text
        readonly property string dataError: dataErrorOutput.text
        function runDataCommand() {
            if (host.active && host.entry.dataCommand && !data.running && !host.entry.disabled && host.error === "") data.running = true;
        }
        function openPanel(panelId) { host.panelRequested(host.entry.plugin, panelId); }
        function reportError(message) { host.fail(message); }
    }
    SpectrumConsumer {
        id: spectrumConsumer
        active: host.live && (host.entry.capabilities || []).indexOf("audio-spectrum") !== -1
        bars: Math.max(8, Math.min(128, api.spectrumBars))
        frameRate: api.spectrumFrameRate
        plugin: true
        smoothing: api.spectrumSmoothing
    }
    property string latestLine: ""
    property bool streamFailed: false
    property int streamRetryDelay: 500
    onLiveChanged: if (!live) { streamRetry.stop(); streamFailed = false; streamRetryDelay = 500; latestLine = ""; }
    Process {
        id: stream
        command: ["python3", host.helper, "ui-stream", host.entry.plugin, host.entry.id]
        running: host.live && !!host.entry.dataStream && !host.streamFailed
        stdout: SplitParser {
            onRead: line => {
                host.latestLine = line;
                api.streamReceived(line);
            }
        }
        onExited: if (host.live) { host.streamFailed = true; streamRetry.start(); }
    }
    Timer {
        id: streamStable; interval: 10000; running: stream.running
        onTriggered: if (stream.running) host.streamRetryDelay = 500
    }
    Timer {
        id: streamRetry; interval: host.streamRetryDelay
        onTriggered: {
            host.streamRetryDelay = Math.min(30000, host.streamRetryDelay * 2);
            host.streamFailed = false;
        }
    }
    HoverHandler { id: hover }
    Rectangle {
        visible: host.surface
        anchors.fill: parent
        radius: DesktopStyle.radius(PanelStyle.controlRadius)
        color: Qt.alpha(host.foreground, PanelStyle.selectionAlpha(false, hover.hovered || host.activeFocus))
        border.width: PanelStyle.selectionBorderWidth(false)
        border.color: Qt.alpha(host.foreground, PanelStyle.selectionBorderAlpha)
    }
    MouseArea {
        anchors.fill: parent; enabled: host.tile || host.barItem
        cursorShape: host.entry.panel ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: { host.forceActiveFocus(); host.activate(); }
    }
    Loader {
        id: content
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: host.tile ? Math.min(96, item ? item.implicitWidth : 0) : host.barItem ? host.width : host.width - 2 * PanelStyle.selectionInset
        anchors.rightMargin: host.tile ? PanelStyle.selectionActionInset : host.barItem ? 0 : PanelStyle.selectionInset
        z: host.barItem ? -1 : 0
        active: host.active && !host.entry.disabled && host.error === ""
        asynchronous: true
        onActiveChanged: if (active) load()
        Component.onCompleted: if (active) load()
        function load() {
            setSource(host.entry.source, {api: api});
        }
        onStatusChanged: {
            if (status === Loader.Error) host.fail("Could not load " + host.entry.qml);
            if (status === Loader.Ready) {
                if (!item || !item.hasOwnProperty("api")) host.fail("Component must declare required property var api");
                else api.runDataCommand();
            }
        }
    }
    Text {
        visible: host.tile
        x: PanelStyle.selectionInset; width: PanelStyle.selectionIconSize
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: Text.AlignHCenter
        text: host.entry.icon || ""; textFormat: Text.PlainText
        color: host.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.selectionIconSize
    }
    Column {
        visible: host.tile
        x: PanelStyle.selectionTextInset
        width: Math.max(0, host.width - x - content.width - 2 * PanelStyle.selectionActionInset)
        anchors.verticalCenter: parent.verticalCenter
        spacing: PanelStyle.selectionDetailGap
        Text {
            width: parent.width; text: host.entry.title; textFormat: Text.PlainText; elide: Text.ElideRight
            color: host.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        Text {
            width: parent.width; visible: text !== ""; text: host.detail; textFormat: Text.PlainText; elide: Text.ElideRight
            color: host.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
        }
    }
    Text {
        anchors.fill: parent; anchors.margins: PanelStyle.selectionInset
        visible: !host.tile && (host.error !== "" || host.entry.disabled)
        text: host.entry.disabled ? Eitr.I18n.tr("Disabled") : Eitr.I18n.tr("Could not load")
        textFormat: Text.PlainText; wrapMode: Text.Wrap
        color: host.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    HoverHandler { id: statusHover }
    BarTooltip {
        target: host; hovered: statusHover.hovered && (host.entry.disabled || host.error !== "")
        text: host.entry.disabled ? Eitr.I18n.tr("Re-enable with eitr plugin enable-ui {plugin}", {plugin: host.entry.plugin})
            : Eitr.I18n.tr("Reopen to retry; disabled after 3 failures")
        foreground: host.foreground; background: host.background
    }
    Process {
        id: data
        command: ["python3", host.helper, "ui-data", host.entry.plugin, host.entry.id]
        stdout: StdioCollector { id: dataOutput }
        stderr: StdioCollector { id: dataErrorOutput }
    }
    Process {
        id: failure
        command: ["python3", host.helper, "ui-failure", host.entry.plugin, host.entry.commit]
        stdinEnabled: true
        onStarted: { write(host.error); stdinEnabled = false; }
    }
    Timer {
        interval: host.entry.refreshInterval || 1000
        running: host.active && !!host.entry.refreshInterval && host.error === "" && !host.entry.disabled
        repeat: true
        onTriggered: api.runDataCommand()
    }
}
