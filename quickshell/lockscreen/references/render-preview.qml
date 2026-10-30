import QtQuick
import QtQuick.Window
import Quickshell

ShellRoot {
    id: preview
    readonly property bool isLockPreview: true
    readonly property var config: JSON.parse(Quickshell.env("EITR_RENDER_CONFIG"))
    readonly property var sddm: mockAuth
    readonly property var userModel: users
    readonly property var sessionModel: sessions
    readonly property var keyboard: keyboardState
    QtObject { id: keyboardState; property bool numLock: false }
    QtObject {
        id: mockAuth
        property bool quickshellLock: false
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, session) {}
        function reboot() {}
        function powerOff() {}
        function suspend() {}
    }
    Component.onCompleted: { if (Quickshell.env("EITR_RENDER_USERS") === "1") users.remove(1, 2); }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "EITR"; function rowCount() { return count; } ListElement { name: "astrid"; realName: "Astrid Solberg" } ListElement { name: "bjorn"; realName: "Bjørn Lund" } ListElement { name: "freya"; realName: "Freya Lind" } }
    ListModel { id: sessions; property int lastIndex: 0; function rowCount() { return count; } ListElement { name: "Current session" } }
    Window {
        id: renderWindow
        Rectangle { anchors.fill: parent; color: "#293b49" }
        Text { anchors.centerIn: parent; text: "Mock desktop"; color: "#c1d4dd"; font.pixelSize: 36 }
        width: Number(Quickshell.env("EITR_RENDER_WIDTH")) || 3840; height: Number(Quickshell.env("EITR_RENDER_HEIGHT")) || 2160; visible: true
        Loader {
            id: design
            anchors.fill: parent
            source: Quickshell.env("EITR_RENDER_DESIGN")
            onLoaded: {
                item.forceActiveFocus();
                const auroraFrame = Quickshell.env("EITR_RENDER_AURORA");
                if (auroraFrame) {
                    const aurora = findChild(item, "eitrAurora");
                    if (!aurora) { console.error("Aurora component missing"); Qt.exit(1); return; }
                    for (const child of aurora.children) child.visible = false;
                    aurora.opacity = 1;
                    aurora.layer.enabled = false;
                    Qt.createQmlObject('import QtQuick; Image { anchors.fill: parent; source: '
                        + JSON.stringify(auroraFrame) + '; smooth: false }', aurora, "CanonicalAuroraReference");
                }
                if (!!Quickshell.env("EITR_RENDER_SWEEP")) item.sweepProgress = Number(Quickshell.env("EITR_RENDER_SWEEP"));
                if (Quickshell.env("EITR_RENDER_STATE") === "wrong") failureDelay.start();
                if (Quickshell.env("EITR_RENDER_STATE") === "typed") {
                    const field = findChild(item, "eitrPassword");
                    if (!field) { console.error("Password field missing"); Qt.exit(1); }
                    field.text = "preview-only";
                }
            }
            function findChild(parentItem, name) {
                if (parentItem.objectName === name) return parentItem;
                for (const child of parentItem.children) {
                    const found = findChild(child, name);
                    if (found) return found;
                }
                return null;
            }
        }
        Timer { id: failureDelay; interval: 600; onTriggered: mockAuth.loginFailed() }
        Timer {
            interval: Number(Quickshell.env("EITR_RENDER_DELAY")) || 3200; running: true
            onTriggered: {
                if (design.status !== Loader.Ready) { console.error("Design did not load"); Qt.exit(1); return; }
                const picker = design.findChild(design.item, "userPicker");
                if (!picker || picker.visible !== (users.count > 1)) { console.error("Incorrect picker visibility"); Qt.exit(1); return; }
                const controller = picker.controller;
                const original = controller.userIndex;
                if (controller.userName !== "Astrid Solberg") { console.error("Real name missing"); Qt.exit(1); return; }
                for (let index = 0; index < users.count; index++) controller.cycleUser();
                if (controller.userIndex !== original) { console.error("User wrap failed"); Qt.exit(1); return; }
                mockAuth.quickshellLock = true;
                controller.cycleUser();
                if (controller.userIndex !== original) { console.error("Lock changed account"); Qt.exit(1); return; }
                mockAuth.quickshellLock = false;
                controller.cycleUser();
                if (controller.userIndex !== (original + 1) % users.count) { console.error("User cycle failed"); Qt.exit(1); return; }
                controller.cycleUser(-1);
                if (controller.userIndex !== original) { console.error("Reverse cycle failed"); Qt.exit(1); return; }
                const target = !!Quickshell.env("EITR_RENDER_SWEEP") ? renderWindow.contentItem : design;
                target.grabToImage(function(result) {
                    if (!result.saveToFile(Quickshell.env("EITR_RENDER_OUTPUT"))) Qt.exit(1);
                    else Qt.quit();
                }, Qt.size(design.width, design.height));
            }
        }
    }
}
