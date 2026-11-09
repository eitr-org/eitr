import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Change the signed-in user's password from Settings > User. The helper runs passwd
// (the system's rules decide) and re-keys the login keyring; the passwords go to it on
// stdin and the fields are cleared whenever the sheet closes.
Popup {
    id: sheet
    required property var view
    property bool live: true
    property string error: ""
    property string notice: ""
    readonly property bool busy: helper.running
    readonly property bool ready: current.text !== "" && fresh.text !== "" && fresh.text === repeat.text && !busy
    objectName: "settings-password-sheet"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 340
    padding: 24
    modal: true
    dim: true
    focus: true
    closePolicy: busy ? Popup.NoAutoClose : Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: Qt.alpha("black", 0.45) }
    onOpened: { error = ""; notice = ""; current.forceActiveFocus(); }
    // Shown on the User page after the sheet closes.
    onClosed: { current.clear(); fresh.clear(); repeat.clear(); }

    function submit() {
        if (!ready) {
            if (fresh.text !== repeat.text) error = Eitr.I18n.tr("The new passwords do not match.");
            return;
        }
        error = "";
        if (live) helper.running = true;
    }
    function finish(result) {
        if (result.status === "changed") {
            notice = result.keyring === "kept"
                ? Eitr.I18n.tr("Password changed. The login keyring kept its old password; change it in Passwords and Keys.")
                : Eitr.I18n.tr("Password changed.");
            current.clear(); fresh.clear(); repeat.clear();
            close();
        } else if (result.status === "wrong-current") {
            error = Eitr.I18n.tr("The current password is not correct.");
            current.clear();
            current.forceActiveFocus();
        } else if (result.status === "rejected") {
            error = Eitr.I18n.tr("The new password was not accepted: {reason}", {reason: result.detail || Eitr.I18n.tr("choose a stronger one")});
            fresh.clear(); repeat.clear();
            fresh.forceActiveFocus();
        } else {
            error = Eitr.I18n.tr("The password could not be changed.");
        }
    }

    Process {
        id: helper
        command: ["python3", Eitr.Paths.code("walker/scripts/actions/system/account_password.py")]
        stdinEnabled: true
        onStarted: {
            write(JSON.stringify({current: current.text, new: fresh.text}) + "\n");
            stdinEnabled = false;
        }
        onExited: stdinEnabled = true
        stdout: StdioCollector {
            onStreamFinished: {
                let result = {status: "failed"};
                try { result = JSON.parse(text); } catch (problem) {}
                sheet.finish(result);
            }
        }
    }

    background: Rectangle {
        radius: DesktopStyle.radius(12)
        color: Qt.rgba(sheet.view.background.r, sheet.view.background.g, sheet.view.background.b, 1)
        border.width: 1
        border.color: Qt.alpha(SettingsInk.gold, 0.4)
    }
    contentItem: Column {
        spacing: 12
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: Eitr.I18n.tr("Change password")
            color: sheet.view.foreground
            font.family: SiteStyle.carved
            font.pixelSize: PanelStyle.headingSize
        }
        SettingsText {
            width: parent.width
            wrapMode: Text.WordWrap
            text: Eitr.I18n.tr("Used to sign in, unlock the screen and approve system changes. A disk encryption passphrase is separate and stays the same.")
        }
        PanelTextField {
            id: current
            objectName: "settings-password-current"
            width: parent.width
            foreground: sheet.view.foreground
            accent: sheet.view.accent
            enabled: !sheet.busy
            echoMode: TextInput.Password
            placeholderText: Eitr.I18n.tr("Current password")
            onAccepted: fresh.forceActiveFocus()
        }
        PanelTextField {
            id: fresh
            objectName: "settings-password-new"
            width: parent.width
            foreground: sheet.view.foreground
            accent: sheet.view.accent
            enabled: !sheet.busy
            echoMode: TextInput.Password
            placeholderText: Eitr.I18n.tr("New password")
            onAccepted: repeat.forceActiveFocus()
        }
        PanelTextField {
            id: repeat
            objectName: "settings-password-repeat"
            width: parent.width
            foreground: sheet.view.foreground
            accent: sheet.view.accent
            enabled: !sheet.busy
            echoMode: TextInput.Password
            placeholderText: Eitr.I18n.tr("Repeat new password")
            onAccepted: sheet.submit()
        }
        SettingsText {
            objectName: "settings-password-error"
            width: parent.width
            wrapMode: Text.WordWrap
            visible: sheet.error !== "" || (repeat.text !== "" && fresh.text !== repeat.text)
            text: sheet.error !== "" ? sheet.error : Eitr.I18n.tr("The new passwords do not match.")
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8
            PanelButton {
                width: 110
                foreground: sheet.view.foreground
                text: Eitr.I18n.tr("Cancel")
                available: !sheet.busy
                onClicked: sheet.close()
            }
            PanelButton {
                objectName: "settings-password-save"
                width: 150
                foreground: sheet.view.foreground
                text: Eitr.I18n.tr("Change password")
                loading: sheet.busy
                available: sheet.ready
                onClicked: sheet.submit()
            }
        }
    }
}
