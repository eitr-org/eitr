"""Render the administrator password prompt offscreen with a fake polkit request."""
import tempfile
import unittest
from pathlib import Path

from layout_render import capture_path, copy_runtime, render, render_environment

FIXTURE = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
    QtObject {
        id: request
        property QtObject owner: QtObject { property string displayName: "alex" }
        property QtObject admin: QtObject { property string displayName: "root" }
        property string message: "Authentication is required to install software from the official repositories <b>now</b>"
        property string iconName: ""
        property string actionId: "org.freedesktop.packagekit.package-install"
        property string cookie: "fixture"
        property var identities: [owner]
        property var selectedIdentity: owner
        property bool isResponseRequired: true
        property string inputPrompt: "Password: "
        property bool responseVisible: false
        property string supplementaryMessage: ""
        property bool supplementaryIsError: false
        property bool isCompleted: false
        property bool failed: false
        property string answer: ""
        property int cancels: 0
        function submit(value) { answer = value; isResponseRequired = false; }
        function cancelAuthenticationRequest() { cancels += 1; }
    }
    FloatingWindow {
        visible: true
        implicitWidth: 480; implicitHeight: 480
        Rectangle {
            id: stage
            anchors.fill: parent
            color: "BACKGROUND"
            Rectangle { anchors.fill: parent; color: "#80000000" }
            Bar.PolkitDialog {
                id: dialog
                anchors.centerIn: parent
                flow: request
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "ACCENT"
            }
        }
    }
    TestCase { id: keyboard; name: "PolkitKeyboard"; when: false }
    function find(item, name) {
        if (item.objectName === name) return item;
        for (const child of item.children) {
            const found = find(child, name);
            if (found) return found;
        }
        return null;
    }
    function check(condition, message) { if (!condition) { console.log("POLKIT_FAIL " + message); Qt.exit(1); } return condition; }
    property var steps: [
        function() {
            dialog.focusPassword();
            check(find(dialog, "polkitPassword").activeFocus, "password field is not focused");
            check(find(dialog, "polkitMessage").textFormat === Text.PlainText, "message is not plain text");
            check(find(dialog, "polkitIdentity").text.indexOf("alex") >= 0, "identity is missing");
            check(!find(dialog, "polkitAuthenticate").available, "empty password can be submitted");
            return "prompt";
        },
        function() {
            for (const key of [Qt.Key_S, Qt.Key_E, Qt.Key_C, Qt.Key_R, Qt.Key_E, Qt.Key_T]) keyboard.keyClick(key);
            check(find(dialog, "polkitPassword").echoMode === TextInput.Password, "password is echoed");
            keyboard.keyClick(Qt.Key_Return);
            check(request.answer === "secret", "Enter did not submit the typed answer");
            check(find(dialog, "polkitPassword").text === "", "the field kept the password after submit");
            check(dialog.waiting, "no progress while polkit checks the answer");
            request.failed = true;
            request.isResponseRequired = true;
            return "wrong-password";
        },
        function() {
            check(find(dialog, "polkitError").visible, "no error after a wrong password");
            check(find(dialog, "polkitPassword").activeFocus, "the field is not focused for a retry");
            find(dialog, "polkitDetailsToggle").clicked();
            return "details";
        },
        function() {
            check(find(dialog, "polkitActionId").text === request.actionId, "details miss the action id");
            dialog.detailsShown = false;
            request.failed = false;
            request.identities = [request.owner, request.admin];
            return "identities";
        },
        function() {
            check(find(dialog, "polkitIdentityChoice").visible, "no identity choice for two identities");
            check(!find(dialog, "polkitIdentity").visible, "single identity line shown beside the choice");
            dialog.focusPassword();
            keyboard.keyClick(Qt.Key_X);
            keyboard.keyClick(Qt.Key_Escape);
            check(request.cancels === 1, "Escape did not cancel the request");
            check(find(dialog, "polkitPassword").text === "", "the field kept text after cancelling");
            return "";
        }
    ]
    property int step: 0
    Timer {
        interval: 300; running: true; repeat: true
        onTriggered: {
            if (dialog.height + 16 > stage.height) { check(false, "the card does not fit: " + dialog.height); return; }
            const name = steps[step]();
            step += 1;
            if (name === "") { console.log("POLKIT_DIALOG_OK"); Qt.quit(); return; }
            stop();
            Qt.callLater(function() {
                stage.grabToImage(function(result) {
                    result.saveToFile("CAPTURE/THEME-" + name + ".png");
                    start();
                });
            });
        }
    }
}
'''


class PolkitDialogTests(unittest.TestCase):
    def test_prompt_wrong_password_details_and_identities_in_both_themes(self):
        themes = {'dark': ('#1e1e2e', '#cdd6f4', '#89b4fa'), 'light': ('#eff1f5', '#4c4f69', '#1e66f5')}
        for theme, (background, foreground, accent) in themes.items():
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                captures = capture_path('POLKIT', directory, theme + '-prompt.png').parent
                fixture = (FIXTURE.replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                           .replace('ACCENT', accent).replace('CAPTURE', str(captures)).replace('THEME', theme))
                (folder / 'fixture.qml').write_text(fixture)
                returncode, output = render(folder / 'fixture.qml', render_environment(directory), timeout=30)
                self.assertEqual(returncode, 0, output)
                self.assertIn('POLKIT_DIALOG_OK', output)
                self.assertNotIn('secret', output)
                for state in ('prompt', 'wrong-password', 'details', 'identities'):
                    self.assertTrue((captures / f'{theme}-{state}.png').is_file(), state)


if __name__ == '__main__':
    unittest.main()
