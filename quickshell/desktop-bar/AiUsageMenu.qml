import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle
import "AiSelectionModel.js" as Selection
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    implicitWidth: 468
    property int maximumHeight: 1000
    implicitHeight: Math.min(maximumHeight, Math.max(300,
        content.implicitHeight + 64 + hero.height + 10 + tabs.height + 16 + footer.implicitHeight + 16 + 2))
    property var usage: ({providers: []})
    property var selectedProviders: []
    property bool detectionReceived: false
    onUsageChanged: { detectionReceived = true; reconcileSelection(); }
    property bool selectionReady: false
    property bool selectionWritable: false
    readonly property var availableProviders: (usage.providers || []).map(providerData => providerData.name)
    readonly property var enabledProviders: (usage.providers || []).filter(providerData => selectedProviders.indexOf(providerData.name) !== -1)
    readonly property var provider: enabledProviders[0] || {name: "", windows: []}
    function reconcileSelection() {
        if (!selectionReady || !detectionReceived) return;
        selectedProviders = Selection.reconcile(availableProviders, selectedProviders);
        saveSelection();
    }
    function saveSelection() {
        if (selectionWritable && detectionReceived)
            selectionSettings.setText(JSON.stringify({version: 1, providers: selectedProviders}) + "\n");
    }
    function toggleProvider(name) {
        selectedProviders = Selection.toggle(availableProviders, selectedProviders, name);
        saveSelection();
    }
    onAvailableProvidersChanged: reconcileSelection()
    FileView {
        id: selectionSettings
        path: Eitr.Paths.config("quickshell/desktop-bar/ai-usage-settings.json")
        atomicWrites: true
        printErrors: false
        onLoaded: {
            try {
                var settings = Eitr.Paths.settings(text());
                menu.selectedProviders = Array.isArray(settings.providers) ? settings.providers : [];
                menu.selectionWritable = true;
            } catch (error) {
                console.warn("Invalid AI usage selection settings:", error);
            }
            menu.selectionReady = true;
            menu.reconcileSelection();
        }
        onLoadFailed: function(error) {
            menu.selectionWritable = error === FileViewError.FileNotFound;
            menu.selectionReady = true;
            menu.reconcileSelection();
        }
    }
    property bool freshReceived: false
    readonly property bool loading: query.running
    property string status: "Checking usage..."
    onSelectedProvidersChanged: contentViewport.contentY = 0
    function refresh() {
        if (!loading) {
            status = "Updating...";
            query.running = true;
        }
    }
    function resetLabel(timestamp) {
        var seconds = Math.max(0, Math.floor(timestamp - Date.now() / 1000));
        return "Resets " + Qt.formatDateTime(new Date(timestamp * 1000), "ddd MMM dd, HH:mm") + " · " + Math.floor(seconds / 3600) + "h " + Math.floor(seconds % 3600 / 60) + "m";
    }
    onOpenedChanged: if (opened) {
        contentViewport.contentY = 0;
        freshReceived = false;
        if (!cached.running) cached.running = true;
        refresh();
    }
    Timer { interval: 300000; repeat: true; running: menu.opened; onTriggered: menu.refresh() }
    Process {
        id: cached
        command: ["python3", Quickshell.shellDir + "/scripts/ai-popup.py", "cached"]
        stdout: StdioCollector { id: cachedOutput }
        onExited: {
            try {
                var data = JSON.parse(cachedOutput.text);
                if (data.providers && !menu.freshReceived) menu.usage = data;
            } catch (e) {}
        }
    }
    Process {
        id: query
        command: ["python3", Quickshell.shellDir + "/scripts/ai-popup.py"]
        stdout: StdioCollector { id: output }
        onExited: function(code) {
            try {
                if (code !== 0) throw new Error("query failed");
                menu.usage = JSON.parse(output.text);
                menu.freshReceived = true;
                menu.status = "Last checked " + Qt.formatDateTime(new Date(menu.usage.updated * 1000), "HH:mm");
            } catch (e) { menu.status = "Could not update usage. Try refreshing."; }
        }
    }
    Item {
        anchors.fill: parent
        anchors.margins: 0
        Item {
            id: hero
            width: parent.width
            height: 40
            PanelHeading {
                width: parent.width - refreshButton.width - 8
                anchors.verticalCenter: parent.verticalCenter
                text: menu.enabledProviders.length > 1 ? Eitr.I18n.tr("AI Usage") : menu.provider.name === "Claude" ? Eitr.I18n.tr("Claude Code") : menu.provider.name || Eitr.I18n.tr("AI Usage")
                subtitle: menu.enabledProviders.length > 1 ? "" : (menu.provider.plan || Eitr.I18n.tr("Plan unavailable")).toUpperCase()
                foreground: menu.foreground; accent: menu.accent; rune: "wisdom"
            }
            PanelButton {
                id: refreshButton
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                text: "󰑓"; icon: true; height: 32
                loading: menu.loading
                foreground: menu.foreground
                onClicked: menu.refresh()
                HoverHandler { id: refreshHover }
                BarTooltip { target: refreshButton; hovered: refreshHover.hovered; text: menu.loading ? Eitr.I18n.tr("Updating") : Eitr.I18n.tr("Refresh"); foreground: menu.foreground; background: menu.background }
            }
        }
        Row {
            id: tabs
            visible: menu.availableProviders.length > 1
            height: visible ? 32 : 0
            anchors.top: hero.bottom
            anchors.topMargin: visible ? 10 : 0
            width: parent.width
            spacing: 6
            Repeater {
                model: menu.availableProviders
                PanelButton {
                    required property string modelData
                    width: (tabs.width - tabs.spacing * (menu.availableProviders.length - 1)) / Math.max(1, menu.availableProviders.length)
                    height: 32
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    text: modelData === "Claude" ? Eitr.I18n.tr("Claude Code") : modelData
                    outlined: true
                    selected: menu.selectedProviders.indexOf(modelData) !== -1
                    foreground: menu.foreground
                    onClicked: menu.toggleProvider(modelData)
                }
            }
        }
        Flickable {
            id: contentViewport
            anchors.top: tabs.bottom
            anchors.topMargin: 16
            anchors.bottom: footer.top
            anchors.bottomMargin: 16
            width: parent.width
            contentHeight: content.height
            interactive: contentHeight > height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: content
                width: parent.width
                spacing: 14
                PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
                Text {
                    visible: menu.enabledProviders.length === 0
                    width: parent.width; wrapMode: Text.Wrap
                    text: menu.loading || cached.running ? Eitr.I18n.tr("Detecting configured AI clients…") : Eitr.I18n.tr("No signed-in AI clients detected. Install and sign in to Claude Code, Codex, or Grok to show usage here.")
                    color: menu.foreground; opacity: 0.7
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Repeater {
                    model: menu.enabledProviders
                    Column {
                        id: section
                        required property var modelData
                        width: content.width
                        spacing: 14
                        PanelHeading {
                            visible: menu.enabledProviders.length > 1
                            width: parent.width
                            text: section.modelData.name === "Claude" ? Eitr.I18n.tr("Claude Code") : section.modelData.name
                            subtitle: (section.modelData.plan || Eitr.I18n.tr("Plan unavailable")).toUpperCase()
                            foreground: menu.foreground; accent: menu.accent; rune: "wisdom"
                        }
                        Text { text: Eitr.I18n.tr("LIMITS"); color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { visible: !!section.modelData.error; width: parent.width; text: section.modelData.error || ""; wrapMode: Text.Wrap; color: menu.foreground; opacity: 0.7; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                        Repeater {
                            model: section.modelData.windows || []
                            Column {
                                id: limit
                                required property var modelData
                                readonly property real used: Math.max(0, Math.min(100, Number(modelData.used)))
                                width: content.width
                                spacing: 7
                                Item {
                                    width: parent.width; height: 17
                                    Text { text: limit.modelData.label === "5h window" ? Eitr.I18n.tr("Session") : limit.modelData.label; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                                    Text { anchors.right: parent.right; text: Eitr.I18n.tr("{percent}% used", {percent: Math.round(limit.used)}); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize }
                                }
                                Rectangle {
                                    width: parent.width; height: 6; radius: 3
                                    color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.12)
                                    Rectangle { width: parent.width * limit.used / 100; height: 6; radius: 3; color: menu.foreground }
                                }
                                Text { visible: !!limit.modelData.reset; width: parent.width; elide: Text.ElideRight; text: limit.modelData.reset ? menu.resetLabel(limit.modelData.reset) : ""; color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                            }
                        }
                    }
                }
            }
        }
        Text { id: footer; anchors.bottom: parent.bottom; width: parent.width; elide: Text.ElideRight; text: menu.status; color: menu.foreground; opacity: 0.6; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
}
