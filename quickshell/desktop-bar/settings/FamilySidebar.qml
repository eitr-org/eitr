import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The sidebar shared by Settings, the Handbook and Eitr Store: a header box
// with the Eitr logo, a search field, rune group captions and rows with a sliding
// gold marker. Entries are {id, title, rune, group, groupRune}, already translated.
ColumnLayout {
    id: sidebar
    required property color foreground
    required property color background
    required property color accent
    property string subtitle: ""
    property string closeName: Eitr.I18n.tr("Close")
    property string placeholder: ""
    property string query: ""
    property bool searchVisible: true
    property var entries: []
    property string currentId: ""
    // A row picked from the search field with Up/Down, or -1.
    property int highlighted: -1
    property string emptyText: ""
    property bool interactive: true
    property alias searchField: search
    property real markerY: 0
    readonly property color gold: SettingsInk.gold
    signal chosen(var entry)
    signal closeRequested()
    signal searchEdited(string text)
    signal searchAccepted()
    signal searchKey(var event)
    spacing: 12
    Rectangle {
        Layout.fillWidth: true; implicitHeight: 76
        color: Qt.alpha(sidebar.foreground, 0.025); radius: DesktopStyle.radius(6)
        border.width: 1; border.color: Qt.alpha(sidebar.gold, 0.3)
        // The logo file leaves a margin around the glyph; at 66 px the glyph itself is as
        // tall as the title and subtitle beside it.
        EitrLogo { x: 2; anchors.verticalCenter: titleBlock.verticalCenter; anchors.verticalCenterOffset: 3; width: 66; height: 66; iconSize: 66; foreground: sidebar.gold; background: sidebar.background; enabled: false }
        Column { id: titleBlock; x: 72; width: parent.width - x - 36; anchors.verticalCenter: parent.verticalCenter; spacing: 3
            Text { text: "EITR"; color: sidebar.foreground; font.family: SiteStyle.carved; font.pixelSize: 23; font.letterSpacing: 3 }
            Text { width: parent.width; text: sidebar.subtitle.toLocaleUpperCase(); color: sidebar.gold; font.family: SiteStyle.carved; font.pixelSize: 11; font.letterSpacing: 2; fontSizeMode: Text.HorizontalFit; minimumPixelSize: 8; elide: Text.ElideRight }
        }
        PanelButton { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 5; width: 28; height: 28; icon: true; compactIconBackground: true; text: "\u{F00D}"; foreground: sidebar.foreground; onClicked: sidebar.closeRequested(); Accessible.name: sidebar.closeName }
    }
    TextField {
        id: search
        visible: sidebar.searchVisible
        Layout.fillWidth: true
        enabled: sidebar.interactive
        text: sidebar.query
        placeholderText: sidebar.placeholder
        color: sidebar.foreground; placeholderTextColor: Qt.alpha(sidebar.foreground, PanelStyle.secondaryTextOpacity)
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        selectByMouse: true; selectionColor: sidebar.accent
        selectedTextColor: PanelStyle.readableInk(sidebar.accent, sidebar.foreground, sidebar.background)
        Accessible.name: placeholderText
        background: Rectangle { color: Qt.alpha(sidebar.foreground, 0.04); radius: DesktopStyle.radius(PanelStyle.controlRadius); border.width: 1; border.color: Qt.alpha(sidebar.foreground, 0.15) }
        onTextEdited: sidebar.searchEdited(text)
        onAccepted: sidebar.searchAccepted()
        Keys.onPressed: event => sidebar.searchKey(event)
    }
    Flickable {
        id: navigationScroll
        ScrollBar.vertical: ScrollBar {
            width: 4; policy: ScrollBar.AsNeeded
            contentItem: Rectangle { radius: 2; color: Qt.alpha(sidebar.foreground, 0.25) }
        }
        Layout.fillWidth: true; Layout.fillHeight: true
        contentHeight: navigation.height; clip: true; boundsBehavior: Flickable.StopAtBounds
        enabled: sidebar.interactive
        Rectangle {
            x: 0; y: sidebar.markerY; z: 2; width: 3; height: 28
            visible: sidebar.entries.some(entry => entry.id === sidebar.currentId)
            radius: 1; color: sidebar.gold
            Behavior on y { NumberAnimation { duration: DesktopStyle.motionDuration(220); easing.type: Easing.OutCubic } }
        }
        Column {
            id: navigation
            width: parent.width; spacing: PanelStyle.selectionRowGap
            Repeater {
                model: sidebar.entries
                Column {
                    id: entry
                    required property var modelData
                    required property int index
                    width: navigation.width; spacing: 2
                    onYChanged: if (row.selected) Qt.callLater(row.revealRow)
                    Text {
                        visible: entry.index === 0 || sidebar.entries[entry.index - 1].group !== entry.modelData.group
                        height: visible ? 24 : 0
                        text: entry.modelData.groupRune + "  " + entry.modelData.group.toLocaleUpperCase()
                        color: sidebar.gold
                        font.family: SettingsInk.runes; font.pixelSize: 11; font.capitalization: Font.SmallCaps; font.letterSpacing: 1
                        verticalAlignment: Text.AlignBottom
                        Rectangle { x: parent.implicitWidth + 8; y: parent.height - 6; width: Math.max(0, navigation.width - x); height: 1; color: Qt.alpha(sidebar.gold, 0.25) }
                    }
                    Rectangle {
                        id: row
                        readonly property bool selected: sidebar.currentId === entry.modelData.id
                        readonly property bool picked: sidebar.highlighted === entry.index
                        width: parent.width; height: entry.modelData.caption ? 52 : PanelStyle.selectionRowHeight
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: Qt.alpha(sidebar.foreground, !selected && (pointer.containsMouse || picked) ? 0.07 : 0)
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            visible: row.selected
                            gradient: selectedGlow
                        }
                        Gradient {
                            id: selectedGlow
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: Qt.alpha(sidebar.accent, 0.18) }
                            GradientStop { position: 0.7; color: Qt.alpha(sidebar.accent, 0.06) }
                            GradientStop { position: 1; color: Qt.alpha(sidebar.accent, 0.02) }
                        }
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button; Accessible.name: entry.modelData.title
                        Keys.onReturnPressed: sidebar.chosen(entry.modelData)
                        Keys.onSpacePressed: sidebar.chosen(entry.modelData)
                        Component.onCompleted: if (selected) Qt.callLater(revealRow)
                        onYChanged: if (selected) Qt.callLater(revealRow)
                        onSelectedChanged: if (selected) Qt.callLater(revealRow)
                        onPickedChanged: if (picked) Qt.callLater(revealRow)
                        onActiveFocusChanged: if (activeFocus) revealRow()
                        function revealRow() {
                            // A deferred call can arrive after the entries were rebuilt.
                            if (!sidebar || !navigation || !navigationScroll || !row.parent) return;
                            const position = mapToItem(navigation, 0, 0).y;
                            if (selected) sidebar.markerY = position + 4;
                            if (position < navigationScroll.contentY) navigationScroll.contentY = position;
                            else if (position + height > navigationScroll.contentY + navigationScroll.height)
                                navigationScroll.contentY = position + height - navigationScroll.height;
                        }
                        Text { x: PanelStyle.selectionInset + 2; width: parent.width - x - 32; y: entry.modelData.caption ? 6 : (parent.height - height) / 2; text: entry.modelData.title; color: sidebar.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; elide: Text.ElideRight }
                        Text { x: PanelStyle.selectionInset + 2; y: 28; width: parent.width - x - 10; visible: !!entry.modelData.caption; text: entry.modelData.caption || ""; color: Qt.alpha(sidebar.foreground, PanelStyle.secondaryTextOpacity); font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; elide: Text.ElideRight }
                        Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: entry.modelData.rune; color: row.selected ? sidebar.gold : Qt.alpha(sidebar.foreground, 0.28); font.family: SettingsInk.runes; font.pixelSize: 15 }
                        MouseArea { id: pointer; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sidebar.chosen(entry.modelData) }
                    }
                }
            }
        }
    }
    Text { visible: sidebar.entries.length === 0 && sidebar.emptyText !== ""; Layout.fillWidth: true; wrapMode: Text.WordWrap; text: sidebar.emptyText; color: sidebar.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
}
