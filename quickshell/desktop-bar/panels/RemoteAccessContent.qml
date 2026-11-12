import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../settings/SettingsCatalog.js" as Catalog

// Streaming: whether sharing runs is a header switch, details sit below, the everyday
// actions stay visible and setup or diagnostic actions live in the "…" menu. Every action
// is a row of Walker's remote-access menus, run through menu-action.py by the panel.
// (Tailscale is a plugin with its own panel.)
Column {
    id: content
    required property string kind
    required property var state
    required property color foreground
    required property color accent
    required property color background
    property bool busy: false
    property bool settingsMode: false
    readonly property var detail: state[kind] || ({})
    readonly property var actions: detail.actions || []
    readonly property bool installed: detail.installed !== false
    // The header's control: a switch for the main state, or the one step that comes first.
    readonly property string setupSource: "Set Up Sharing"
    readonly property string firstStep: !installed ? setupSource : ""
    readonly property var firstStepAction: firstStep === "" ? null : actions.find(entry => entry.source === firstStep) || null
    readonly property var switchSources: ["Start Sharing", "Stop Sharing"]
    readonly property var visibleSources: ["Pair a Device", "Connect to another PC"]
    readonly property var loginSources: ["Start at Login", "Turn Off Start at Login"]
    readonly property var moreActions: actions.filter(entry => entry.source !== firstStep
        && switchSources.indexOf(entry.source) < 0 && visibleSources.indexOf(entry.source) < 0
        && loginSources.indexOf(entry.source) < 0)
    signal actionRequested(string menu, string source)
    signal settingsRequested()
    spacing: 14

    function settingTarget(source) {
        const setting = Catalog.settings.find(candidate => candidate.page === "streaming" && candidate.label === source);
        return settingsMode && setting ? "setting-" + setting.id : "";
    }
    function action(source) { return actions.find(entry => entry.source === source) || null; }
    function run(source) {
        const entry = action(source);
        if (entry) actionRequested(entry.menu, entry.source);
    }

    Item {
        width: parent.width
        height: 42
        PanelHeading {
            width: parent.width - controls.width - 8
            anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Streaming")
            subtitle: content.detail.status || (content.busy ? Eitr.I18n.tr("Checking status…") : Eitr.I18n.tr("Status unavailable"))
            rune: "connectivity"
            foreground: content.foreground
            accent: content.accent
        }
        Row {
            id: controls
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            PanelLoadingIndicator {
                anchors.verticalCenter: parent.verticalCenter
                busy: content.busy
                foreground: content.foreground; background: content.background
            }
            PanelMoreButton {
                anchors.verticalCenter: parent.verticalCenter
                visible: !content.settingsMode && content.moreActions.length > 0
                foreground: content.foreground; background: content.background
                actions: content.moreActions.map(entry => ({title: entry.title, glyph: entry.icon,
                    run: () => content.actionRequested(entry.menu, entry.source)}))
            }
            PanelButton {
                id: firstStepButton
                SettingsTarget { objectName: content.settingTarget(content.setupSource) }
                anchors.verticalCenter: parent.verticalCenter
                visible: content.firstStepAction !== null
                width: Math.max(68, firstStepLabel.width + 24); height: 30
                text: content.firstStepAction ? content.firstStepAction.title : ""
                foreground: content.foreground
                onClicked: content.run(content.firstStep)
                TextMetrics { id: firstStepLabel; text: firstStepButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            }
            PanelSwitch {
                SettingsTarget { objectName: "setting-streaming-streaming" }
                anchors.verticalCenter: parent.verticalCenter
                visible: content.firstStep === "" && content.installed
                checked: !!content.detail.running
                enabled: !content.busy
                foreground: content.foreground; accent: content.accent
                onClicked: content.run(content.switchSources[checked ? 0 : 1])
            }
        }
    }
    Column {
        width: parent.width
        spacing: PanelStyle.selectionRowGap
        Repeater {
            model: content.detail.facts || []
            delegate: Row {
                required property var modelData
                width: content.width
                spacing: 12
                Text {
                    width: (parent.width - 12) * 0.4
                    text: modelData.label
                    color: content.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    wrapMode: Text.Wrap
                }
                Text {
                    width: (parent.width - 12) * 0.6
                    horizontalAlignment: Text.AlignRight
                    text: modelData.value
                    textFormat: Text.PlainText
                    color: content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    font.features: PanelStyle.tabularFigures
                    wrapMode: Text.WrapAnywhere
                }
            }
        }
    }
    // Whether sharing starts when you sign in.
    Item {
        visible: content.installed && content.detail.startAtLogin !== undefined
        width: parent.width
        height: visible ? 32 : 0
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Start at login")
            SettingsTarget { objectName: "setting-streaming-start-at-login" }
            color: content.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            checked: !!content.detail.startAtLogin
            enabled: !content.busy
            foreground: content.foreground; accent: content.accent
            onClicked: content.run(content.loginSources[checked ? 0 : 1])
        }
    }
    // The everyday actions stay one click away.
    Row {
        id: everyday
        visible: content.installed
        width: parent.width
        spacing: PanelStyle.selectionActionGap
        Repeater {
            model: content.visibleSources.map(source => content.action(source)).filter(entry => entry !== null)
            PanelButton {
                required property var modelData
                SettingsTarget { objectName: content.settingTarget(modelData.source) }
                width: content.settingsMode ? everyday.width : (everyday.width - everyday.spacing) / 2; height: 34
                text: modelData.title; leadingIcon: modelData.icon || ""
                textSize: PanelStyle.bodySize; iconSize: 16; textAlignment: Text.AlignLeft
                foreground: content.foreground
                onClicked: content.actionRequested(modelData.menu, modelData.source)
                HoverHandler { id: buttonHover }
                BarTooltip { target: parent; hovered: buttonHover.hovered; text: modelData.description || ""; foreground: content.foreground; background: content.background }
            }
        }
    }
    Repeater {
        model: content.settingsMode ? content.moreActions : []
        ControlRow {
            SettingsTarget { objectName: content.settingTarget(modelData.source) }
            required property var modelData
            text: modelData.title
            description: modelData.description
            foreground: content.foreground
            PanelButton {
                width: parent.width
                text: Eitr.I18n.tr("Open")
                foreground: content.foreground
                available: !content.busy
                onClicked: content.actionRequested(modelData.menu, modelData.source)
            }
        }
    }
    PanelFooterLink {
        visible: !content.settingsMode
        text: Eitr.I18n.tr("Remote Access Settings…")
        foreground: content.foreground
        onClicked: content.settingsRequested()
    }
}
