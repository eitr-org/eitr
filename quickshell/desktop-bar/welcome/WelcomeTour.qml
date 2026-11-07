import ".."
import QtQuick
import Eitr as Eitr
import "../HandbookModel.js" as Model

// A short tour of the desktop: one step at a time with its live drawing, moving on
// by itself every six seconds unless the pointer rests on it. Dots and the arrows
// pick a step; the reader sends Left/Right here too. Reduce motion makes changes instant.
Rectangle {
    id: tour
    required property var section
    required property color foreground
    required property color background
    required property color accent
    property url artSource: ""
    property bool active: false
    property int current: 0
    property int shown: 0
    readonly property var items: section ? section.items || [] : []
    readonly property var item: items[shown] || ({})
    readonly property bool narrow: width < 620
    function step(delta) {
        if (items.length < 2) return;
        current = (current + delta + items.length) % items.length;
        advance.restart();
    }
    onCurrentChanged: swap.restart()
    onItemsChanged: if (current >= items.length) { current = 0; shown = 0; }
    width: parent ? parent.width : 0
    height: frame.height + 36
    radius: DesktopStyle.radius(12)
    color: SettingsPalette.surface
    border.width: 1; border.color: SettingsPalette.line
    HoverHandler { id: hover }
    Timer {
        id: advance
        interval: 6000; repeat: true
        running: tour.active && tour.visible && !hover.hovered && tour.items.length > 1
        onTriggered: tour.current = (tour.current + 1) % tour.items.length
    }
    SequentialAnimation {
        id: swap
        ParallelAnimation {
            NumberAnimation { target: stage; property: "opacity"; to: 0; duration: DesktopStyle.motionDuration(140) }
            NumberAnimation { target: slide; property: "x"; to: -10; duration: DesktopStyle.motionDuration(140) }
        }
        ScriptAction { script: { tour.shown = tour.current; slide.x = 14; } }
        ParallelAnimation {
            NumberAnimation { target: stage; property: "opacity"; to: 1; duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutCubic }
            NumberAnimation { target: slide; property: "x"; to: 0; duration: DesktopStyle.motionDuration(260); easing.type: Easing.OutCubic }
        }
    }
    Column {
        id: frame
        x: 18; y: 18; width: parent.width - 36
        spacing: 16
        Item {
            width: parent.width; height: heading.height
            Text {
                id: heading
                width: parent.width - counter.width - 12
                text: tour.section ? tour.section.title : ""
                textFormat: Text.StyledText
                color: tour.foreground
                font.family: SiteStyle.carved; font.pixelSize: 19
                elide: Text.ElideRight
            }
            Text {
                id: counter
                anchors.right: parent.right; anchors.baseline: heading.baseline
                text: (tour.shown + 1) + " / " + tour.items.length
                color: SettingsInk.gold
                font.family: SiteStyle.carved; font.pixelSize: 13; font.letterSpacing: 1.5
            }
        }
        Item {
            id: stage
            width: parent.width
            height: tour.narrow ? picture.height + words.height + 16 : Math.max(picture.height, words.height)
            transform: Translate { id: slide }
            WelcomeTourArt {
                id: picture
                width: tour.narrow ? parent.width : Math.round(parent.width * 0.46)
                height: tour.narrow ? 180 : 210
                step: tour.item.id || ""
                artSource: tour.artSource
                animate: tour.active && tour.visible
                foreground: tour.foreground; background: tour.background; accent: tour.accent
            }
            Column {
                id: words
                x: tour.narrow ? 0 : picture.width + 26
                y: tour.narrow ? picture.height + 16 : Math.max(0, (picture.height - height) / 2)
                width: parent.width - x
                spacing: 10
                Text {
                    text: Model.runes[(tour.shown * 5) % Model.runes.length] + "  " + Eitr.I18n.tr("Step %1").arg(tour.shown + 1).toLocaleUpperCase()
                    color: SettingsInk.gold
                    font.family: SettingsInk.runes; font.pixelSize: 11; font.letterSpacing: 1.6
                }
                Text {
                    width: parent.width
                    text: tour.item.title || ""
                    textFormat: Text.StyledText
                    color: tour.foreground
                    font.family: SiteStyle.carved; font.pixelSize: tour.narrow ? 22 : 26
                    wrapMode: Text.WordWrap
                }
                Text {
                    width: parent.width
                    text: tour.item.text || ""
                    textFormat: Text.StyledText
                    color: tour.foreground
                    opacity: 0.84
                    font.family: DesktopFonts.family; font.pixelSize: 14
                    lineHeight: 1.25
                    wrapMode: Text.WordWrap
                }
            }
        }
        Item {
            width: parent.width; height: 32
            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                Repeater {
                    model: tour.items.length
                    Rectangle {
                        required property int index
                        readonly property bool selected: index === tour.current
                        anchors.verticalCenter: parent.verticalCenter
                        width: selected ? 26 : 8; height: 8; radius: 4
                        color: selected ? SettingsInk.gold : Qt.alpha(tour.foreground, dotMouse.containsMouse ? 0.45 : 0.22)
                        Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(220); easing.type: Easing.OutCubic } }
                        Accessible.role: Accessible.Button
                        Accessible.name: Eitr.I18n.tr("Step %1").arg(index + 1)
                        MouseArea {
                            id: dotMouse
                            anchors.fill: parent; anchors.margins: -8
                            hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { tour.current = parent.index; advance.restart(); }
                        }
                    }
                }
            }
            Row {
                anchors.right: parent.right
                spacing: 8
                PanelButton {
                    width: 32; icon: true; outlined: true; iconSize: 18
                    text: "󰅁"; foreground: tour.foreground
                    available: tour.items.length > 1
                    Accessible.name: Eitr.I18n.tr("Previous step")
                    onClicked: tour.step(-1)
                }
                PanelButton {
                    width: 32; icon: true; outlined: true; iconSize: 18
                    text: "󰅂"; foreground: tour.foreground
                    available: tour.items.length > 1
                    Accessible.name: Eitr.I18n.tr("Next step")
                    onClicked: tour.step(1)
                }
            }
        }
    }
}
