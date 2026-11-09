import ".."
import QtQuick

// The zero-size anchor stays out of positioner geometry; its child paints the row.
// Neither item intercepts input.
Item {
    id: target
    Component.onCompleted: if (parent.settingTargetOwner) parent = parent.settingTargetOwner
    z: 20
    Rectangle {
        width: target.parent ? target.parent.width : 0
        height: target.parent ? target.parent.height : 0
        radius: DesktopStyle.radius(4)
        color: Qt.alpha(SettingsPalette.accent, 0.22)
    }
    opacity: 0
    function reveal() {
        let ancestor = parent;
        while (ancestor) {
            if (ancestor.contentItem && ancestor.contentY !== undefined) {
                const position = parent.mapToItem(ancestor.contentItem, 0, 0).y;
                ancestor.contentY = Math.max(0, Math.min(position - 18, ancestor.contentHeight - ancestor.height));
            }
            ancestor = ancestor.parent;
        }
        fade.stop(); hold.stop(); opacity = 1;
        if (DesktopStyle.reduceMotion) hold.start();
        else fade.start();
    }
    NumberAnimation { id: fade; target: target; property: "opacity"; from: 1; to: 0; duration: 1500 }
    Timer { id: hold; interval: 1500; onTriggered: target.opacity = 0 }
}
