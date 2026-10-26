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
    property var openedProviders: []
    property bool selectionReady: false
    property bool selectionWritable: false
    readonly property var shownProviders: Selection.shownProviders(usage.providers)
    readonly property var availableProviders: shownProviders.map(providerData => providerData.name)
    function toggleProvider(name) {
        openedProviders = Selection.toggle(availableProviders, openedProviders, name);
        if (selectionWritable)
            selectionSettings.setText(JSON.stringify({version: 1, openedProviders: openedProviders}) + "\n");
    }
    FileView {
        id: selectionSettings
        path: Quickshell.env("XDG_RUNTIME_DIR") ? Quickshell.env("XDG_RUNTIME_DIR") + "/eitr-ai-usage-open.json" : ""
        atomicWrites: true
        printErrors: false
        onLoaded: {
            try {
                menu.openedProviders = Selection.restore(Eitr.Paths.settings(text()));
                menu.selectionWritable = true;
            } catch (error) {
                console.warn("Invalid AI usage session settings:", error);
            }
            menu.selectionReady = true;
        }
        onLoadFailed: function(error) {
            menu.selectionWritable = !!path && error === FileViewError.FileNotFound;
            menu.selectionReady = true;
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
                    text: menu.loading || cached.running ? Eitr.I18n.tr("Detecting configured AI clients…") : Eitr.I18n.tr("No readable AI usage available. Sign in to Claude Code, Codex, or Grok, or try refreshing later.")
                    color: menu.foreground; opacity: 0.7
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                }
                Repeater {
                    model: menu.shownProviders
                    Column {
                        id: section
                        required property var modelData
                        width: content.width
                        spacing: 14
                        required property int index
                        readonly property string plan: Selection.sharedPlan(modelData.accounts)
                        readonly property bool folded: menu.openedProviders.indexOf(modelData.name) === -1
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
                                textFormat: Text.StyledText
                                text: {
                                    const name = section.modelData.name === "Claude" ? Eitr.I18n.tr("Claude Code") : section.modelData.name;
                                    const escape = value => String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
                                    const secondary = Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, PanelStyle.secondaryTextOpacity);
                                    return escape(name) + (section.plan ? ' <font color="' + secondary + '">· ' + escape(section.plan) + '</font>' : "");
                                }
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
                                    visible: section.modelData.accounts.length > 1
                                    text: accountSection.modelData.label + (!section.plan && accountSection.modelData.plan ? " · " + accountSection.modelData.plan : "")
                                    elide: Text.ElideRight
                                    color: menu.foreground
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.secondarySize
                                }
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
