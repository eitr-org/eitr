import QtQuick
import Eitr as Eitr
import Quickshell
import Quickshell.Io

// Eitr's calculator: a small floating window in the current theme's colors and
// desktop font. CalculatorView draws it; CalculatorModel.js does the arithmetic,
// parsing the expression instead of running it as code.
ShellRoot {
    id: root
    Component.onCompleted: Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1"

    Process {
        running: true
        command: ["python3", Eitr.Paths.code("quickshell/calculator/theme.py")]
        stdout: StdioCollector { id: theme }
        onExited: function(code) {
            if (code !== 0) return;
            const value = JSON.parse(theme.text);
            view.background = value.background;
            view.foreground = value.foreground;
            view.accent = value.accent;
            view.font = value.font;
        }
    }

    FloatingWindow {
        id: window
        title: Eitr.I18n.tr("Eitr Calculator")
        visible: true
        implicitWidth: 340
        implicitHeight: 540
        color: view.background
        onVisibleChanged: if (!visible) Qt.quit()

        CalculatorView {
            id: view
            anchors.fill: parent
            onCopyRequested: text => Quickshell.execDetached(["wl-copy", text])
            onCloseRequested: Qt.quit()
        }
    }
}
