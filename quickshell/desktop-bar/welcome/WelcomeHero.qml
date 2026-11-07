import ".."
import QtQuick

// The welcome's opening picture: the theme's art under a carved title and one line.
// `artSource` is the current wallpaper today; a theme's own welcome art can take its place.
WallpaperArt {
    id: hero
    required property string title
    // The chapter's rune and group, as page headers show them.
    property string caption: ""
    property string lead: ""
    property url artSource: ""
    required property color foreground
    required property color accent
    required property color background
    readonly property bool narrow: width < 560
    width: parent ? parent.width : 0
    height: narrow ? 250 : Math.max(260, Math.min(330, width * 0.36))
    radius: DesktopStyle.radius(16)
    color: Qt.tint(background, Qt.alpha(accent, 0.14))
    source: artSource
    surround: background
    EitrLogo {
        visible: !hero.loaded
        readonly property int extent: Math.round(hero.height * 0.62)
        anchors.right: parent.right; anchors.rightMargin: hero.narrow ? 16 : 48
        anchors.verticalCenter: parent.verticalCenter
        width: extent; height: extent; iconSize: extent
        foreground: Qt.alpha(SettingsInk.gold, 0.2); background: hero.background
        enabled: false
    }
    // Keeps the words readable over any wallpaper, light or dark.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: Qt.alpha(hero.background, 0.9) }
            GradientStop { position: hero.narrow ? 0.75 : 0.5; color: Qt.alpha(hero.background, 0.62) }
            GradientStop { position: 1; color: Qt.alpha(hero.background, hero.narrow ? 0.4 : 0.05) }
        }
    }
    Rectangle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        height: parent.height * 0.5
        gradient: Gradient {
            GradientStop { position: 0; color: "transparent" }
            GradientStop { position: 1; color: Qt.alpha(hero.background, 0.55) }
        }
    }
    Column {
        anchors.left: parent.left; anchors.leftMargin: hero.narrow ? 22 : 34
        anchors.bottom: parent.bottom; anchors.bottomMargin: hero.narrow ? 24 : 34
        width: Math.min(hero.width - 2 * anchors.leftMargin, 540)
        spacing: 10
        Text {
            visible: text !== ""
            text: hero.caption
            color: SettingsInk.gold
            font.family: SettingsInk.runes
            font.pixelSize: 12
            font.letterSpacing: 1.8
        }
        Text {
            width: parent.width
            text: hero.title
            color: hero.foreground
            font.family: SiteStyle.carved
            font.pixelSize: hero.narrow ? 32 : 42
            wrapMode: Text.WordWrap
            lineHeight: 1.05
        }
        Rectangle { width: 56; height: 2; radius: 1; color: SettingsInk.gold }
        Text {
            width: parent.width
            visible: text !== ""
            text: hero.lead
            textFormat: Text.StyledText
            color: hero.foreground
            opacity: 0.88
            font.family: DesktopFonts.family
            font.pixelSize: 15
            lineHeight: 1.2
            wrapMode: Text.WordWrap
        }
    }
}
