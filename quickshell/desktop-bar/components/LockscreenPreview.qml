import ".."
import QtQuick
import Eitr as Eitr
Rectangle {
    property color accent: foreground
    property color raised: Qt.alpha(foreground, 0.08)
    property color gold: foreground
    property color foreground: "#eeeeee"
    property color background: "#20242c"
    id: picture
    property string value: "eitr"
    color: picture.background
    Image {
        id: preview
        anchors.fill: parent
        source: picture.value === "hyprlock" ? "" : "file://" + Eitr.Paths.code("quickshell/lockscreen/themes/" + picture.value + "/preview.png")
        sourceSize.width: 320
        fillMode: Image.PreserveAspectFit
    }
    Column {
        anchors.centerIn: parent
        visible: preview.status !== Image.Ready
        spacing: 6
        Text { text: "12:34"; color: picture.foreground; font.pixelSize: 22; font.family: SiteStyle.carved }
        Rectangle { width: 68; height: 12; radius: DesktopStyle.radius(3); color: picture.raised; border.color: picture.gold }
    }
}
