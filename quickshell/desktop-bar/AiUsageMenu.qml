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
        content.implicitHeight + 64 + hero.height + 10 + 16 + aiFooter.height + 8 + footer.implicitHeight + 16 + 2))
    property var usage: ({providers: []})
    property var foldedProviders: []
    property bool detectionReceived: false
    onUsageChanged: { detectionReceived = true; reconcileFolding(); }
    property bool selectionReady: false
    property bool selectionWritable: false
    readonly property var availableProviders: (usage.providers || []).map(providerData => providerData.name)
    function reconcileFolding() {
        if (!selectionReady || !detectionReceived) return;
        foldedProviders = Selection.reconcile(availableProviders, foldedProviders);
        saveFolding();
    }
    function saveFolding() {
        if (selectionWritable && detectionReceived)
            selectionSettings.setText(JSON.stringify({version: 2, foldedProviders: foldedProviders}) + "\n");
    }
    function toggleProvider(name) {
        foldedProviders = Selection.toggle(availableProviders, foldedProviders, name);
        saveFolding();
    }
    onAvailableProvidersChanged: reconcileFolding()
    FileView {
        id: selectionSettings
        path: Eitr.Paths.config("quickshell/desktop-bar/ai-usage-settings.json")
        atomicWrites: true
        printErrors: false
        onLoaded: {
            try {
                var settings = Eitr.Paths.settings(text());
                menu.foldedProviders = Selection.restore(settings);
                menu.selectionWritable = true;
            } catch (error) {
                console.warn("Invalid AI usage folding settings:", error);
            }
            menu.selectionReady = true;
            menu.reconcileFolding();
        }
        onLoadFailed: function(error) {
            menu.selectionWritable = error === FileViewError.FileNotFound;
            menu.selectionReady = true;
            menu.reconcileFolding();
        }
    }
    property bool freshReceived: false
    readonly property bool loading: query.running
    property string status: "Checking usage..."
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
                width: parent.width - 42
                anchors.verticalCenter: parent.verticalCenter
                text: Eitr.I18n.tr("AI Usage")
                foreground: menu.foreground; accent: menu.accent; rune: "wisdom"
            }
            PanelLoadingIndicator {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                busy: menu.loading
                foreground: menu.foreground; background: menu.background
            }
        }
        Flickable {
            id: contentViewport
            anchors.top: hero.bottom
            anchors.topMargin: 16
            anchors.bottom: aiFooter.top
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
                Text {
                    visible: menu.availableProviders.length === 0
                    width: parent.width; wrapMode: Text.Wrap
                    text: menu.loading || cached.running ? Eitr.I18n.tr("Detecting configured AI clients…") : Eitr.I18n.tr("No signed-in AI clients detected. Install and sign in to Claude Code, Codex, or Grok to show usage here.")
                    color: menu.foreground; opacity: 0.7
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Repeater {
                    model: menu.usage.providers || []
                    Column {
                        id: section
                        required property var modelData
                        width: content.width
                        spacing: 14
                        required property int index
                        readonly property bool folded: menu.foldedProviders.indexOf(modelData.name) !== -1
                        PanelButton {
                            id: sectionHeading
                            width: parent.width
                            height: PanelStyle.selectionRowHeight
                            text: ""
                            foreground: menu.foreground
                            onClicked: menu.toggleProvider(section.modelData.name)
                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: PanelStyle.selectionInset
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - chevron.width - 32
                                elide: Text.ElideRight
                                text: section.modelData.name === "Claude" ? Eitr.I18n.tr("Claude Code") : section.modelData.name
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                            Text {
                                id: chevron
                                anchors.right: parent.right
                                anchors.rightMargin: PanelStyle.selectionInset
                                anchors.verticalCenter: parent.verticalCenter
                                text: section.folded ? "›" : "⌄"
                                color: menu.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                        }
                        Repeater {
                            model: section.folded ? [] : (section.modelData.accounts || [])
                            Column {
                                id: accountSection
                                required property var modelData
                                width: parent.width
                                spacing: 14
                                Text {
                                    width: parent.width
                                    text: accountSection.modelData.label + " · " + (accountSection.modelData.plan || Eitr.I18n.tr("Plan unavailable"))
                                    elide: Text.ElideRight
                                    color: menu.foreground
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.bodySize
                                }
                                Text { visible: !!accountSection.modelData.error; width: parent.width; text: accountSection.modelData.error || ""; wrapMode: Text.Wrap; color: menu.foreground; opacity: 0.7; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                                Repeater {
                                    model: accountSection.modelData.windows || []
                                    Column {
                                        id: limit
                                        required property var modelData
                                        readonly property real used: Math.max(0, Math.min(100, Number(modelData.used)))
                                        width: content.width
                                        spacing: 7
                                        Item {
                                            width: parent.width; height: 17
                                            Text { text: limit.modelData.label === "5h window" ? Eitr.I18n.tr("Session") : limit.modelData.label; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                                            Text { anchors.right: parent.right; text: Eitr.I18n.tr("{percent}% used", {percent: Math.round(limit.used)}); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize; font.features: PanelStyle.tabularFigures }
                                        }
                                        Rectangle {
                                            width: parent.width; height: 6; radius: 3
                                            color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.12)
                                            Rectangle { width: parent.width * limit.used / 100; height: 6; radius: 3; color: menu.foreground }
                                        }
                                        Text { visible: !!limit.modelData.reset; width: parent.width; elide: Text.ElideRight; text: limit.modelData.reset ? menu.resetLabel(limit.modelData.reset) : ""; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        PanelFooterLink {
            id: aiFooter
            anchors.bottom: footer.top
            anchors.bottomMargin: 8
            text: Eitr.I18n.tr("AI Assistants…")
            foreground: menu.foreground
            onClicked: { menu.opened = false; Quickshell.execDetached([Eitr.Paths.code("walker/bin/walker"), "--provider", "menus:ai-tools"]); }
        }
        Text { id: footer; anchors.bottom: parent.bottom; width: parent.width; elide: Text.ElideRight; text: menu.status; color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
    }
}
