import ".."
import QtQuick
import Quickshell
import Quickshell.Io

Scope {
    id: owner
    required property color foreground
    required property color background
    required property color accent
    Loader {
        id: content
        active: false
        sourceComponent: BeautifyContent {
            foreground: owner.foreground
            background: owner.background
            accent: owner.accent
        }
    }
    IpcHandler {
        target: "beautify"
        function open(path: string): void {
            content.active = true;
            content.item.open(path);
        }
    }
}
