import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

// Pure view: native Hyprland groups remain usable if the view disappears.
Rectangle {
    id: strip
    required property var tabs
    required property color foreground
    required property color background
    required property color accent
    property string fontFamily: DesktopFonts.family
    property string clockText: ""
    property string networkText: ""
    property string batteryText: ""
    signal selected(string address)
    implicitHeight: 28
    color: background
    clip: true
    readonly property int paneCount: tabs.filter(tab => tab.pane).length
    readonly property int firstPane: tabs.findIndex(tab => tab.pane)
    readonly property int lastPane: tabs.reduce((last, tab, index) => tab.pane ? index : last, -1)
    function revealFocused() {
        const index = tabs.findIndex(tab => tab.active);
        if (index < 0) return;
        const start = index * tabWidth;
        const end = start + tabWidth;
        if (start < scroll.contentX) scroll.contentX = start;
        else if (end > scroll.contentX + scroll.width) scroll.contentX = Math.min(Math.max(0, scroll.contentWidth - scroll.width), end - scroll.width);
    }
    onTabsChanged: Qt.callLater(revealFocused)
    onWidthChanged: Qt.callLater(revealFocused)
    readonly property real tabWidth: Math.max(48, Math.min(220, (width - status.width - 16) / Math.max(1, tabs.length)))
    Flickable {
        id: scroll
        anchors { left: parent.left; right: status.left; top: parent.top; bottom: parent.bottom; rightMargin: 8 }
        contentWidth: row.width
        contentHeight: height
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        Row {
            id: row
            height: parent.height
            Repeater {
                model: strip.tabs
                Rectangle {
                    required property var modelData
                    required property int index
                    width: strip.tabWidth; height: strip.height
                    color: modelData.active ? Qt.alpha(strip.accent, 0.22) : "transparent"
                    Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: modelData.active ? 2 : 1; color: modelData.active ? strip.accent : Qt.alpha(strip.foreground, PanelStyle.dividerAlpha) }
                    Rectangle { visible: strip.paneCount > 1 && index >= strip.firstPane && index <= strip.lastPane; anchors { left: parent.left; right: parent.right; top: parent.top } height: 2; color: modelData.pane ? strip.accent : Qt.alpha(strip.accent, 0.35) }
                    Text {
                        anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                        verticalAlignment: Text.AlignVCenter
                        text: (index < 9 ? (index + 1) + "  " : "") + modelData.title
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: strip.foreground; font.family: strip.fontFamily; font.pixelSize: PanelStyle.captionSize
                        font.bold: modelData.active
                    }
                    MouseArea { anchors.fill: parent; onClicked: strip.selected(modelData.address) }
                }
            }
        }
    }
    Row {
        id: status
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        spacing: 12
        Repeater {
            model: [strip.networkText, strip.batteryText, strip.clockText].filter(label => label !== "")
            Text { required property string modelData; text: modelData; color: strip.foreground; font.family: strip.fontFamily; font.pixelSize: PanelStyle.captionSize; font.features: PanelStyle.tabularFigures }
        }
    }
}
