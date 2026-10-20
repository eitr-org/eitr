import Eitr as Eitr
import QtQuick
import "PanelStyle.js" as PanelStyle

ThemedPopup {
    id: menu
    required property bool idleEnabled
    required property bool busy
    signal toggleRequested()
    signal lockRequested()
    property bool pendingLock: false
    implicitWidth: 340
    // The shared surface reserves PanelStyle.surfaceInset above and below its content frame.
    implicitHeight: controls.implicitHeight + verticalContentInset
    onVisibleChanged: {
        if (!visible && pendingLock) {
            pendingLock = false;
            lockRequested();
        }
    }
    IdleLockControls {
        id: controls
        x: 0; y: 0
        width: parent.width
        idleEnabled: menu.idleEnabled
        busy: menu.busy
        foreground: menu.foreground
        accent: menu.accent
        onToggleRequested: menu.toggleRequested()
        onLockRequested: {
            menu.pendingLock = true;
            menu.opened = false;
        }
    }
    BarTooltip {
        target: controls.lockTarget
        hovered: controls.lockHovered
        text: Eitr.I18n.tr("Lock now")
        foreground: menu.foreground
        background: menu.background
    }
}
