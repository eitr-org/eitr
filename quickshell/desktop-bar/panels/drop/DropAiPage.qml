import "../.."
import QtQuick
import Eitr as Eitr
import "../../PanelStyle.js" as PanelStyle
import "../../AiSelectionModel.js" as Selection

// Drop's AI Usage page: one column per signed-in assistant, each limit as a large
// percentage over a thin bar with the time until it resets. The ai.usage domain is
// observed only while this page shows; the AI Usage panel keeps the full details.
Item {
    id: page
    required property var barHost
    required property color foreground
    required property color accent
    required property bool watching
    property string token: ""
    readonly property var snapshot: DesktopData.topics["ai.usage"]
    readonly property var providers: Selection.shownProviders(snapshot && snapshot.data ? snapshot.data.providers : []).slice(0, 3)
    onWatchingChanged: {
        if (watching) token = DesktopData.observe("ai.usage", page);
        else if (token) { DesktopData.release(token); token = ""; }
    }
    Component.onDestruction: DesktopData.releaseOwner(page)
    implicitHeight: Math.max(150, columns.implicitHeight + 16)

    function resetIn(timestamp) {
        const minutes = Math.max(0, Math.floor((timestamp - Date.now() / 1000) / 60));
        if (minutes >= 1440) return Eitr.I18n.tr("Resets in {days}d {hours}h", {days: Math.floor(minutes / 1440), hours: Math.floor(minutes % 1440 / 60)});
        return Eitr.I18n.tr("Resets in {hours}h {minutes}m", {hours: Math.floor(minutes / 60), minutes: minutes % 60});
    }

    Row {
        id: columns
        y: 8
        width: parent.width
        Repeater {
            model: page.providers
            Item {
                id: provider
                required property var modelData
                required property int index
                readonly property var account: modelData.accounts[0]
                readonly property string plan: Selection.sharedPlan(modelData.accounts) || account.plan || ""
                width: columns.width / Math.max(1, page.providers.length)
                implicitHeight: body.implicitHeight
                height: implicitHeight
                Rectangle {
                    visible: provider.index > 0
                    width: 1; height: parent.height; color: Qt.alpha(page.foreground, 0.14)
                }
                Column {
                    id: body
                    x: provider.index > 0 ? 20 : 6; width: parent.width - x - 14
                    spacing: 12
                    Column {
                        spacing: 2
                        Text {
                            text: provider.modelData.name === "Claude" ? Eitr.I18n.tr("Claude Code") : provider.modelData.name
                            color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.Bold
                            font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
                        }
                        Text {
                            visible: provider.plan !== ""
                            text: provider.plan
                            color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                        }
                    }
                    Repeater {
                        model: (provider.account.windows || []).slice(0, 2)
                        Column {
                            id: limit
                            required property var modelData
                            readonly property real used: Math.max(0, Math.min(100, Number(modelData.used) || 0))
                            width: body.width
                            spacing: 5
                            Row {
                                spacing: 8
                                Text {
                                    text: Math.round(limit.used) + "%"
                                    color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 24; font.weight: Font.Bold
                                    font.features: PanelStyle.tabularFigures
                                }
                                Text {
                                    anchors.baseline: parent.children[0].baseline
                                    text: limit.modelData.label === "5h window" ? Eitr.I18n.tr("Session") : limit.modelData.label
                                    color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                                }
                            }
                            Rectangle {
                                width: parent.width; height: 4; radius: 2
                                color: Qt.alpha(page.foreground, 0.12)
                                Rectangle {
                                    width: parent.width * limit.used / 100; height: 4; radius: 2; color: page.accent
                                    Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(500); easing.type: Easing.OutCubic } }
                                }
                            }
                            Text {
                                visible: !!limit.modelData.reset
                                width: parent.width; elide: Text.ElideRight
                                text: limit.modelData.reset ? page.resetIn(limit.modelData.reset) : ""
                                color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                                font.family: DesktopFonts.family; font.pixelSize: 11
                            }
                        }
                    }
                }
            }
        }
    }
    Text {
        anchors.centerIn: parent
        width: parent.width - 40; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
        visible: page.providers.length === 0
        text: page.snapshot && page.snapshot.inFlight || !page.snapshot ? Eitr.I18n.tr("Detecting configured AI clients…")
            : Eitr.I18n.tr("No readable AI usage available. Sign in to Claude Code, Codex, or Grok, or try refreshing later.")
        color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
    }
    MouseArea {
        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
        onClicked: page.barHost.togglePanel(page.barHost.aiMenu)
    }
}
