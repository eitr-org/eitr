import QtQuick
import Eitr as Eitr
import "PanelStyle.js" as PanelStyle

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
    signal refreshRequested()
    signal actionRequested(string menu, string source)
    spacing: 14
    Item {
        width: parent.width
        height: 42
        PanelHeading {
            width: parent.width - 54
            anchors.verticalCenter: parent.verticalCenter
            text: content.kind === "tailscale" ? "Tailscale" : Eitr.I18n.tr("Streaming")
            subtitle: content.detail.status || (content.busy ? Eitr.I18n.tr("Checking status…") : Eitr.I18n.tr("Status unavailable"))
            rune: "connectivity"
            foreground: content.foreground
            accent: content.accent
        }
        PanelButton {
            id: refreshButton
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            compactIconBackground: true
            width: 34; height: 32
            icon: true; text: "\uF021"
            loading: content.busy
            foreground: content.foreground
            onClicked: content.refreshRequested()
            HoverHandler { id: refreshHover }
            BarTooltip { target: refreshButton; hovered: refreshHover.hovered; text: Eitr.I18n.tr("Refresh"); foreground: content.foreground; background: content.background }
        }
    }
    Text {
        width: parent.width
        visible: text !== ""
        text: content.kind === "tailscale" ? ""
            : content.detail.startAtLogin !== undefined ? Eitr.I18n.tr("Start at Login: {state}", {state: content.detail.startAtLogin ? Eitr.I18n.tr("On") : Eitr.I18n.tr("Off")}) : ""
        textFormat: Text.PlainText
        color: content.foreground
        opacity: 0.6
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
        wrapMode: Text.Wrap
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
                width: (parent.width - 12) * 0.45
                text: modelData.label
                color: content.foreground
                opacity: 0.6
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
                wrapMode: Text.Wrap
            }
            Text {
                width: (parent.width - 12) * 0.55
                text: modelData.value
                textFormat: Text.PlainText
                color: content.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
                wrapMode: Text.WrapAnywhere
            }
        }
    }
    }
    Repeater {
        model: content.kind === "tailscale" ? content.detail.peers || [] : []
        delegate: Row {
            required property var modelData
            width: content.width
            spacing: 8
            Text {
                width: parent.width - connection.width - 8
                text: modelData.name
                textFormat: Text.PlainText
                color: content.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
                elide: Text.ElideRight
            }
            Text {
                id: connection
                text: modelData.connection
                color: content.foreground
                opacity: 0.6
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
        }
    }
    PanelDivider { width: parent.width; height: 8; foreground: content.foreground }
    Grid {
        id: actionGrid
        width: parent.width
        columns: 2
        spacing: PanelStyle.selectionRowGap
        Repeater {
            model: content.actions
            Rectangle {
                id: actionRow
                required property var modelData
                width: (actionGrid.width - actionGrid.spacing) / actionGrid.columns
                height: PanelStyle.selectionRowHeight
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.alpha(content.foreground, PanelStyle.selectionAlpha(false, actionMouse.containsMouse))
                border.width: PanelStyle.selectionBorderWidth(false)
                border.color: Qt.alpha(content.foreground, PanelStyle.selectionBorderAlpha)
                activeFocusOnTab: true
                Keys.onReturnPressed: content.actionRequested(modelData.menu, modelData.source)
                Keys.onSpacePressed: content.actionRequested(modelData.menu, modelData.source)
                Text {
                    x: PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: actionRow.modelData.icon
                    color: content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.headingSize
                }
                Text {
                    x: PanelStyle.selectionTextInset
                    width: parent.width - x - PanelStyle.selectionInset
                    anchors.verticalCenter: parent.verticalCenter
                    text: actionRow.modelData.title
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                MouseArea {
                    id: actionMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: content.actionRequested(actionRow.modelData.menu, actionRow.modelData.source)
                }
                BarTooltip {
                    target: actionRow
                    hovered: actionMouse.containsMouse
                    text: actionRow.modelData.title + "\n" + actionRow.modelData.description
                    foreground: content.foreground
                    background: content.background
                }
            }
        }
    }
}
