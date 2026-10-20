import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "." as Eitr

// A private-data-free reader fixture for documentation screenshots.
ShellRoot {
    Eitr.Handbook {
        id: book
        opened: true
        mask: Region {}
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        foreground: "#ddd9bd"
        background: "#20202b"
        accent: "#85a1dc"
    }
    IpcHandler {
        target: "preview"
        function stop(): void { book.opened = false; exitDelay.restart(); }
    }
    Timer { id: exitDelay; interval: 700; onTriggered: Qt.quit() }
    Timer { interval: 120000; running: true; onTriggered: { book.opened = false; exitDelay.restart(); } }
}
