import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../AiSelectionModel.js" as Selection

// Drop's AI Usage page: one column per signed-in assistant, each limit as a large
// percentage over a thin bar with the time until it resets. Clicking an assistant opens
// all its accounts and limits in place, with a back button. The ai.usage domain is
// observed only while this page shows.
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
        if (!watching) chosen = "";
        if (watching) token = DesktopData.observe("ai.usage", page);
        else if (token) { DesktopData.release(token); token = ""; }
    }
    Component.onDestruction: DesktopData.releaseOwner(page)
    // The assistant opened in place, by name, or "" for the overview.
    property string chosen: ""
    readonly property var chosenProvider: providers.find(provider => provider.name === chosen) || null
    implicitHeight: chosenProvider ? Math.max(150, details.implicitHeight + 16) : Math.max(150, columns.implicitHeight + 16)
    function title(name) { return name === "Claude" ? Eitr.I18n.tr("Claude Code") : name; }

    function resetIn(timestamp) {
        const minutes = Math.max(0, Math.floor((timestamp - Date.now() / 1000) / 60));
        if (minutes >= 1440) return Eitr.I18n.tr("Resets in {days}d {hours}h", {days: Math.floor(minutes / 1440), hours: Math.floor(minutes % 1440 / 60)});
        return Eitr.I18n.tr("Resets in {hours}h {minutes}m", {hours: Math.floor(minutes / 60), minutes: minutes % 60});
    }

    // One limit: a large percentage and its name, a thin bar, and when it resets.
    component Limit: Column {
        id: limit
        required property var window
        readonly property real used: Math.max(0, Math.min(100, Number(window.used) || 0))
        spacing: 5
        Row {
            spacing: 8
            Text {
                id: percent
                text: Math.round(limit.used) + "%"
                color: page.foreground; font.family: DesktopFonts.family; font.pixelSize: 24; font.weight: Font.Bold
                font.features: PanelStyle.tabularFigures
            }
            Text {
                anchors.baseline: percent.baseline
                text: limit.window.label === "5h window" ? Eitr.I18n.tr("Session") : limit.window.label
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
            visible: !!limit.window.reset
            width: parent.width; elide: Text.ElideRight
            text: limit.window.reset ? page.resetIn(limit.window.reset) : ""
            color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family; font.pixelSize: 11
        }
    }

    Row {
        id: columns
        y: 8
        width: parent.width
        visible: !page.chosenProvider
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
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: page.chosen = provider.modelData.name
                }
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
                            text: page.title(provider.modelData.name)
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
                        Limit {
                            required property var modelData
                            window: modelData
                            width: body.width
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
    // One assistant opened in place: every account, each limit in a two-column grid.
    Column {
        id: details
        y: 8; x: 6; width: parent.width - 12
        visible: !!page.chosenProvider
        spacing: 14
        Row {
            spacing: 8
            PanelButton {
                width: 24; height: 24; icon: true; anchors.verticalCenter: parent.verticalCenter
                text: "󰅁"; foreground: page.foreground
                Accessible.name: Eitr.I18n.tr("Back")
                onClicked: page.chosen = ""
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: page.chosenProvider ? page.title(page.chosenProvider.name) : ""
                color: page.accent; font.family: DesktopFonts.family; font.pixelSize: 11; font.weight: Font.Bold
                font.capitalization: Font.AllUppercase; font.letterSpacing: 1.2
            }
        }
        Repeater {
            model: page.chosenProvider ? page.chosenProvider.accounts : []
            Column {
                id: account
                required property var modelData
                width: details.width
                spacing: 10
                Text {
                    text: [account.modelData.label, account.modelData.plan].filter(Boolean).join(" · ")
                    color: page.foreground; opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                }
                Grid {
                    columns: 2; columnSpacing: 28; rowSpacing: 14
                    Repeater {
                        model: account.modelData.windows || []
                        Limit {
                            required property var modelData
                            window: modelData
                            width: (details.width - 28) / 2
                        }
                    }
                }
            }
        }
    }
}
