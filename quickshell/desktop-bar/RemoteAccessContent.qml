import QtQuick
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

// Tailscale and Streaming share this layout: the main state is a header switch
// (connected, sharing), details sit below, the everyday actions stay visible and
// setup or diagnostic actions live in the "…" menu. Every action is a row of
// Walker's remote-access menus, run through menu-action.py by the panel.
Column {
    id: content
    required property string kind
    required property var state
    required property color foreground
    required property color accent
    required property color background
    property bool busy: false
    readonly property var detail: state[kind] || ({})
    readonly property var actions: detail.actions || []
    readonly property bool tailscale: kind === "tailscale"
    readonly property bool installed: detail.installed !== false
    // The header's control: a switch for the main state, or the one step that comes first.
    readonly property string setupSource: tailscale ? "Set Up Away Access" : "Set Up Sharing"
    readonly property string firstStep: !installed ? setupSource : tailscale && detail.signedOut ? "Sign In" : ""
    readonly property var firstStepAction: firstStep === "" ? null : actions.find(entry => entry.source === firstStep) || null
    readonly property var switchSources: tailscale ? ["Connect", "Disconnect"] : ["Start Sharing", "Stop Sharing"]
    readonly property var visibleSources: tailscale ? [] : ["Pair a Device", "Connect to another PC"]
    readonly property var loginSources: tailscale ? [] : ["Start at Login", "Turn Off Start at Login"]
    readonly property var moreActions: actions.filter(entry => entry.source !== firstStep
        && switchSources.indexOf(entry.source) < 0 && visibleSources.indexOf(entry.source) < 0
        && loginSources.indexOf(entry.source) < 0 && entry.source !== "Sign In")
    signal actionRequested(string menu, string source)
    signal settingsRequested()
    spacing: 14

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
            text: content.tailscale ? "Tailscale" : Eitr.I18n.tr("Streaming")
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
                visible: content.moreActions.length > 0
                foreground: content.foreground; background: content.background
                actions: content.moreActions.map(entry => ({title: entry.title, glyph: entry.icon,
                    run: () => content.actionRequested(entry.menu, entry.source)}))
            }
            PanelButton {
                id: firstStepButton
                anchors.verticalCenter: parent.verticalCenter
                visible: content.firstStepAction !== null
                width: Math.max(68, firstStepLabel.width + 24); height: 30
                text: content.firstStepAction ? content.firstStepAction.title : ""
                foreground: content.foreground
                onClicked: content.run(content.firstStep)
                TextMetrics { id: firstStepLabel; text: firstStepButton.text; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize }
            }
            PanelSwitch {
                anchors.verticalCenter: parent.verticalCenter
                visible: content.firstStep === "" && content.installed
                checked: content.tailscale ? !!content.detail.connected : !!content.detail.running
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
    // Streaming: whether sharing starts when you sign in.
    Item {
        visible: !content.tailscale && content.installed && content.detail.startAtLogin !== undefined
        width: parent.width
        height: visible ? 32 : 0
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: Eitr.I18n.tr("Start at login")
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
    // Tailscale: the other devices on the network and how this PC reaches them.
    Column {
        visible: content.tailscale && (content.detail.peers || []).length > 0
        width: parent.width
        spacing: PanelStyle.selectionRowGap
        PanelDivider { width: parent.width; height: 8; foreground: content.foreground }
        Text {
            text: Eitr.I18n.tr("DEVICES")
            color: content.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
        Repeater {
            model: content.tailscale ? content.detail.peers || [] : []
            delegate: Rectangle {
                required property var modelData
                width: content.width
                height: PanelStyle.selectionRowHeight
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.alpha(content.foreground, PanelStyle.selectionAlpha(false, false))
                border.width: PanelStyle.selectionBorderWidth(false)
                border.color: Qt.alpha(content.foreground, PanelStyle.selectionBorderAlpha)
                Text {
                    width: PanelStyle.selectionTextInset
                    anchors.verticalCenter: parent.verticalCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: "\u{F0379}"
                    color: content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.selectionIconSize
                }
                Text {
                    x: PanelStyle.selectionTextInset
                    width: parent.width - x - connection.width - 2 * PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.name
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                Text {
                    id: connection
                    anchors.right: parent.right
                    anchors.rightMargin: PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.connection
                    color: content.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                }
            }
        }
    }
    // Streaming: the everyday actions stay one click away.
    Row {
        id: everyday
        visible: !content.tailscale && content.installed
        width: parent.width
        spacing: PanelStyle.selectionActionGap
        Repeater {
            model: content.visibleSources.map(source => content.action(source)).filter(entry => entry !== null)
            PanelButton {
                required property var modelData
                width: (everyday.width - everyday.spacing) / 2; height: 34
                text: modelData.title; leadingIcon: modelData.icon
                textSize: PanelStyle.bodySize; iconSize: 16; textAlignment: Text.AlignLeft
                foreground: content.foreground
                onClicked: content.actionRequested(modelData.menu, modelData.source)
                HoverHandler { id: buttonHover }
                BarTooltip { target: parent; hovered: buttonHover.hovered; text: modelData.description; foreground: content.foreground; background: content.background }
            }
        }
    }
    PanelFooterLink {
        text: Eitr.I18n.tr("Remote Access Settings…")
        foreground: content.foreground
        onClicked: content.settingsRequested()
    }
}
