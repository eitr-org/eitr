import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle
import "../HandbookModel.js" as Model

// A small live drawing of one tour step in the current theme's colours. The bar and
// themes reuse BarPreview, PalettePreview and WallpaperArt; the rest are simple shapes.
Rectangle {
    id: art
    required property string step
    required property color foreground
    required property color background
    required property color accent
    property color gold: SettingsInk.gold
    property url artSource: ""
    property bool animate: true
    readonly property color line: Qt.alpha(foreground, 0.14)
    readonly property color panel: Qt.tint(background, Qt.alpha(foreground, 0.06))
    readonly property color selectedInk: PanelStyle.readableInk(accent, foreground, background)
    radius: DesktopStyle.radius(12)
    color: Qt.tint(background, Qt.alpha(accent, 0.1))
    border.width: 1; border.color: line
    clip: true
    Loader {
        anchors.fill: parent
        anchors.margins: 1
        sourceComponent: ({bar: barArt, launcher: launcherArt, settings: settingsArt, "control-center": centerArt, themes: themesArt})[art.step] || null
    }
    // A pill standing for a line of text.
    component Bar: Rectangle { height: 6; radius: 3; color: Qt.alpha(art.foreground, 0.3) }
    component Glyph: Text { color: art.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: 15 }
    Component {
        id: barArt
        WallpaperArt {
            id: desktopPicture
            radius: art.radius; surround: art.color
            color: Qt.tint(art.background, Qt.alpha(art.accent, 0.18))
            source: art.artSource
            BarPreview {
                id: desktopBar
                readonly property var layouts: ["unified", "islands", "dynamic", "centered"]
                property int shown: 0
                anchors.fill: parent
                zoom: Math.max(1, Math.min(width / 150, height / 90))
                scenery: !desktopPicture.loaded
                layout: layouts[shown]; expanded: true
                foreground: art.foreground; background: art.background; accent: art.accent; gold: art.gold
                Timer { interval: 1800; repeat: true; running: art.animate && !DesktopStyle.reduceMotion; onTriggered: desktopBar.shown = (desktopBar.shown + 1) % desktopBar.layouts.length }
            }
        }
    }
    Component {
        id: launcherArt
        Item {
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(parent.width * 0.72, 300); height: Math.min(parent.height * 0.78, 168)
                radius: DesktopStyle.radius(10); color: art.panel; border.width: 1; border.color: art.line
                Column {
                    anchors.fill: parent; anchors.margins: 12; spacing: 8
                    Rectangle {
                        width: parent.width; height: 28; radius: DesktopStyle.radius(6)
                        color: Qt.alpha(art.foreground, 0.06); border.width: 1; border.color: Qt.alpha(art.gold, 0.6)
                        Glyph { x: 9; anchors.verticalCenter: parent.verticalCenter; text: "󰍉"; color: art.gold }
                        Text { id: hint; x: 32; anchors.verticalCenter: parent.verticalCenter; text: "SUPER + Space"; color: art.foreground; opacity: 0.7; font.family: DesktopFonts.family; font.pixelSize: 11 }
                        Rectangle {
                            x: hint.x + hint.width + 3; anchors.verticalCenter: parent.verticalCenter; width: 1.5; height: 13; color: art.foreground
                            SequentialAnimation on opacity { running: art.animate && !DesktopStyle.reduceMotion; loops: Animation.Infinite; NumberAnimation { to: 0; duration: 500 } NumberAnimation { to: 1; duration: 500 } }
                        }
                    }
                    Repeater {
                        model: [{icon: "󰈹", size: 0.62}, {icon: "󰆍", size: 0.48}, {icon: "󰉋", size: 0.55}]
                        Rectangle {
                            required property var modelData
                            required property int index
                            width: parent.width; height: 26; radius: DesktopStyle.radius(5)
                            color: index === 0 ? Qt.alpha(art.accent, 0.28) : "transparent"
                            Glyph { x: 8; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.icon }
                            Bar { x: 32; anchors.verticalCenter: parent.verticalCenter; width: (parent.width - 44) * parent.modelData.size }
                        }
                    }
                }
            }
        }
    }
    Component {
        id: settingsArt
        Item {
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(parent.width * 0.84, 340); height: Math.min(parent.height * 0.8, 176)
                radius: DesktopStyle.radius(10); color: art.panel; border.width: 1; border.color: art.line
                Column {
                    id: sidebar
                    x: 10; y: 12; width: parent.width * 0.32; spacing: 6
                    Repeater {
                        model: 5
                        Rectangle {
                            required property int index
                            width: sidebar.width; height: 20; radius: DesktopStyle.radius(4)
                            color: index === 1 ? Qt.alpha(art.foreground, 0.12) : "transparent"
                            Text { x: 6; anchors.verticalCenter: parent.verticalCenter; text: Model.runes[parent.index * 3]; color: art.gold; font.family: SettingsInk.runes; font.pixelSize: 10 }
                            Bar { x: 22; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 32 - parent.index * 4 }
                        }
                    }
                }
                Rectangle { x: sidebar.x + sidebar.width + 8; y: 10; width: 1; height: parent.height - 20; color: art.line }
                Column {
                    x: sidebar.x + sidebar.width + 18; y: 14; width: parent.width - x - 12; spacing: 9
                    Text { text: "ᚱ  ·"; color: art.gold; font.family: SettingsInk.runes; font.pixelSize: 9 }
                    Rectangle { width: parent.width * 0.55; height: 9; radius: 4; color: Qt.alpha(art.foreground, 0.55) }
                    Repeater {
                        model: [true, false]
                        Rectangle {
                            required property bool modelData
                            width: parent.width; height: 34; radius: DesktopStyle.radius(6)
                            color: Qt.alpha(art.foreground, 0.04); border.width: 1; border.color: art.line
                            Bar { x: 10; anchors.verticalCenter: parent.verticalCenter; width: parent.width * 0.42 }
                            Rectangle {
                                anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
                                width: 26; height: 14; radius: 7
                                color: parent.modelData ? art.accent : Qt.alpha(art.foreground, 0.2)
                                Rectangle { x: parent.parent.modelData ? 14 : 2; y: 2; width: 10; height: 10; radius: 5; color: parent.parent.modelData ? art.selectedInk : art.foreground }
                            }
                        }
                    }
                }
            }
        }
    }
    Component {
        id: centerArt
        Item {
            Column {
                anchors.centerIn: parent
                spacing: 10
                Grid {
                    columns: 3; spacing: 8
                    Repeater {
                        model: [{icon: "󰖩", on: true}, {icon: "󰂯", on: true}, {icon: "󰖔", on: false},
                                {icon: "󰍬", on: false}, {icon: "󰄀", on: false}, {icon: "󰂚", on: true}]
                        Rectangle {
                            required property var modelData
                            width: 56; height: 40; radius: DesktopStyle.radius(8)
                            color: modelData.on ? art.accent : Qt.alpha(art.foreground, 0.07)
                            border.width: modelData.on ? 0 : 1; border.color: art.line
                            Glyph { anchors.centerIn: parent; text: parent.modelData.icon; color: parent.modelData.on ? art.selectedInk : art.foreground; font.pixelSize: 17 }
                        }
                    }
                }
                Rectangle {
                    width: 184; height: 6; radius: 3; color: Qt.alpha(art.foreground, 0.15)
                    Rectangle {
                        id: level
                        height: parent.height; radius: 3; color: art.gold
                        width: parent.width * 0.6
                        SequentialAnimation on width {
                            running: art.animate && !DesktopStyle.reduceMotion; loops: Animation.Infinite
                            NumberAnimation { to: 184 * 0.35; duration: 1600; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 184 * 0.75; duration: 1600; easing.type: Easing.InOutSine }
                        }
                    }
                    Rectangle { x: level.width - 6; anchors.verticalCenter: parent.verticalCenter; width: 12; height: 12; radius: 6; color: art.foreground }
                }
            }
        }
    }
    Component {
        id: themesArt
        Item {
            readonly property real cardWidth: Math.min(width * 0.36, 150)
            PalettePreview {
                x: parent.width / 2 - parent.cardWidth * 1.15; anchors.verticalCenter: parent.verticalCenter
                width: parent.cardWidth * 0.8; height: width * 0.66; rotation: -9
                radius: DesktopStyle.radius(8); border.width: 1; border.color: art.line
                value: "website"; foreground: art.foreground; background: art.background; accent: art.accent
            }
            PalettePreview {
                x: parent.width / 2 + parent.cardWidth * 0.35; anchors.verticalCenter: parent.verticalCenter
                width: parent.cardWidth * 0.8; height: width * 0.66; rotation: 9
                radius: DesktopStyle.radius(8); border.width: 1; border.color: art.line
                themeBackground: art.foreground; themeForeground: art.background; themeAccent: art.accent
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.cardWidth; height: width * 0.62 + 26
                radius: DesktopStyle.radius(9); color: art.panel; border.width: 1; border.color: Qt.alpha(art.gold, 0.7)
                WallpaperArt {
                    x: 5; y: 5; width: parent.width - 10; height: parent.height - 31
                    radius: DesktopStyle.radius(6); color: Qt.tint(art.background, Qt.alpha(art.accent, 0.3))
                    source: art.artSource; surround: art.panel
                }
                Row {
                    x: 8; y: parent.height - 18; spacing: 5
                    Repeater {
                        model: [art.accent, art.gold, art.foreground, art.background]
                        Rectangle { required property color modelData; width: 11; height: 11; radius: 6; color: modelData; border.width: 1; border.color: art.line }
                    }
                }
            }
        }
    }
}
