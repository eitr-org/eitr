import ".."
import QtQuick
Rectangle {
    property color gold: foreground
    property color accent: foreground
    property color background: "#20242c"
    property color foreground: "#eeeeee"
    property color themeAccent: accent
    property color themeForeground: foreground
    property color themeBackground: background
    property color line: Qt.alpha(foreground, 0.15)
    id: picture
    property string value: "theme"
    color: value === "website" ? SiteStyle.bg : picture.themeBackground
    Row {
        anchors.centerIn: parent
        spacing: 6
        Repeater {
            model: picture.value === "website" ? [SiteStyle.bronze, SiteStyle.accent, SiteStyle.fg] : [picture.themeAccent, picture.themeForeground, picture.themeBackground]
            Rectangle { required property var modelData; width: 22; height: 28; radius: DesktopStyle.radius(3); color: modelData; border.color: picture.line }
        }
    }
}
