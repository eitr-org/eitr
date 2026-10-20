import QtQuick
import Eitr as Eitr
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    Component.onCompleted: Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1"
    id: picker
    property var emojis: []
    property var results: []
    property string query: ""
    property int selected: 0
    property color background: "#181824"
    property color foreground: "#cdd6f4"
    property color accent: "#cdd6f4"

    function filter() {
        var words = query.trim().toLowerCase().split(/\s+/);
        results = emojis.filter(function(item) {
            return words.every(function(word) { return item.k.toLowerCase().indexOf(word) !== -1 || item.e === word; });
        }).slice(0, 1000);
        selected = 0;
        grid.positionViewAtBeginning();
    }
    function navigate(delta) {
        if (!results.length) return;
        selected = (selected + delta + results.length) % results.length;
        grid.positionViewAtIndex(selected, GridView.Contain);
    }
    function insert(index) {
        if (!results[index]) return;
        Quickshell.execDetached([Eitr.Paths.code("quickshell/emoji-picker/insert.sh"), results[index].e]);
        Qt.quit();
    }

    Process {
        running: true
        command: ["python3", Eitr.Paths.code("quickshell/emoji-picker/data.py")]
        stdout: StdioCollector { id: data }
        onExited: function(code) {
            if (code === 0) {
                var value = JSON.parse(data.text);
                picker.emojis = value.emojis;
                picker.background = value.background;
                picker.foreground = value.foreground;
                picker.accent = value.accent;
                picker.filter();
            }
        }
    }

    PanelWindow {
        id: panel
        visible: true
        screen: Quickshell.screens[0]
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        color: "transparent"
        WlrLayershell.namespace: "desktop-emoji-picker"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        MouseArea { anchors.fill: parent; onClicked: Qt.quit() }

        Rectangle {
            id: card
            anchors.centerIn: parent
            width: Math.min(400, panel.width - 32)
            height: Math.min(500, panel.height - 64)
            radius: 4
            color: Qt.rgba(picker.background.r, picker.background.g, picker.background.b, 0.96)
            border.width: 2
            border.color: picker.accent
            MouseArea { anchors.fill: parent; onClicked: search.forceActiveFocus() }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                TextField {
                    id: search
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    placeholderText: Eitr.I18n.tr("Search emojis")
                    color: picker.foreground
                    placeholderTextColor: Qt.rgba(picker.foreground.r, picker.foreground.g, picker.foreground.b, 0.55)
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 14
                    selectByMouse: true
                    background: Rectangle { radius: 4; color: Qt.rgba(picker.foreground.r, picker.foreground.g, picker.foreground.b, 0.06) }
                    Component.onCompleted: forceActiveFocus()
                    onTextChanged: { picker.query = text; picker.filter(); }
                    Keys.priority: Keys.BeforeItem
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Escape) {
                            if (text) clear(); else Qt.quit();
                        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) picker.insert(picker.selected);
                        else if (event.key === Qt.Key_Left) picker.navigate(-1);
                        else if (event.key === Qt.Key_Right) picker.navigate(1);
                        else if (event.key === Qt.Key_Up) picker.navigate(-grid.columns);
                        else if (event.key === Qt.Key_Down) picker.navigate(grid.columns);
                        else if (event.key === Qt.Key_Tab) picker.navigate(event.modifiers & Qt.ShiftModifier ? -1 : 1);
                        else return;
                        event.accepted = true;
                    }
                }

                GridView {
                    id: grid
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    readonly property int columns: Math.max(1, Math.floor(width / 46))
                    cellWidth: width / columns
                    cellHeight: 46
                    model: picker.results
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: Rectangle {
                        required property int index
                        required property var modelData
                        width: grid.cellWidth
                        height: grid.cellHeight
                        radius: 4
                        color: index === picker.selected ? Qt.rgba(picker.accent.r, picker.accent.g, picker.accent.b, 0.24) : "transparent"
                        Text {
                            anchors.centerIn: parent
                            text: parent.modelData.e
                            font.family: "Noto Color Emoji"
                            font.pixelSize: 28
                        }
                        MouseArea {
                            id: mouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onPositionChanged: picker.selected = index
                            onClicked: picker.insert(index)
                        }
                        ToolTip.visible: mouse.containsMouse
                        ToolTip.delay: 600
                        ToolTip.text: modelData.k
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: !picker.results.length
                        text: Eitr.I18n.tr("No matches")
                        color: picker.foreground
                        font.pixelSize: 14
                    }
                }
            }
        }
    }
}
