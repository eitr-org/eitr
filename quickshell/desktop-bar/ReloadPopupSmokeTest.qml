// Run with: quickshell -p quickshell/desktop-bar/ReloadPopupSmokeTest.qml
// Uses a separate instance; never breaks or restarts the live desktop config.
import QtQuick
import Quickshell
import "."

ShellRoot {
    id: test
    property int step: 0
    property color testBackground: "#111c18"
    property color testForeground: "#C1C497"
    function check(condition, message) {
        if (!condition) throw new Error(message);
    }
    ReloadErrorPopup {
        id: popup
        foreground: test.testForeground
        background: test.testBackground
        targetScreen: Quickshell.screens[0] || null
    }
    Timer {
        interval: 500; running: true; repeat: true
        onTriggered: {
            if (test.step === 0) {
                Quickshell.reloadFailed("Test error: a long readable line with <plain text> only.\n".repeat(20));
            } else if (test.step === 1) {
                test.check(popup.showing && popup.popupWindow, "Error popup did not open");
                test.check(popup.errorMessage.indexOf("<plain text>") !== -1, "Error details were lost");
                test.check(popup.popupWindow.height <= 500, "Long errors must not exceed the screen");
                test.testBackground = Qt.rgba(17 / 255, 28 / 255, 24 / 255, 0.38);
            } else if (test.step === 2) {
                test.check(popup.background.a < 0.4, "Blur appearance must update live");
                test.testBackground = "#f1eee8";
                test.testForeground = "#242424";
                Quickshell.reloadFailed("Second test error");
            } else if (test.step === 3) {
                test.check(popup.errorMessage === "Second test error", "New error must replace the previous one");
                test.check(popup.background.a === 1, "Theme Color must remain opaque");
                Quickshell.reloadCompleted();
            } else {
                test.check(!popup.showing, "Successful reload must dismiss the error and stay quiet");
                console.log("Reload popup: error signals, replacement, live colors, blur, size cap and dismissal passed");
                Qt.quit();
            }
            test.step++;
        }
    }
}
