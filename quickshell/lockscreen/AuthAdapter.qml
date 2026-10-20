import QtQuick
import Quickshell
import Quickshell.Services.Pam

Item {
    id: auth
    required property bool preview
    signal authenticated()
    property string password: ""
    property bool supplied: false
    readonly property var sddm: bridge
    readonly property var userModel: users
    readonly property var sessionModel: sessions

    ListModel {
        id: users
        property string lastUser: Quickshell.env("USER")
        property int lastIndex: 0
        function rowCount() { return count; }
        Component.onCompleted: append({name: lastUser, realName: lastUser, icon: ""})
    }
    ListModel {
        id: sessions
        property int lastIndex: 0
        function rowCount() { return count; }
        Component.onCompleted: append({name: "Current session", file: ""})
    }
    QtObject {
        id: bridge
        // Lets designs tell this bridge from SDDM (see LoginController.qml).
        readonly property bool quickshellLock: true
        signal loginFailed()
        signal loginSucceeded()
        function login(user, value, sessionIndex) {
            // Previews never authenticate; a second submit during an attempt is
            // ignored so its pending result is not reported as a failure.
            if (auth.preview || pam.active) return;
            if (user !== users.lastUser) {
                loginFailed();
                return;
            }
            auth.password = value;
            auth.supplied = false;
            pam.start();
        }
        function reboot() { if (!auth.preview) Quickshell.execDetached(["systemctl", "reboot"]); }
        function powerOff() { if (!auth.preview) Quickshell.execDetached(["systemctl", "poweroff"]); }
        function suspend() { if (!auth.preview) Quickshell.execDetached(["systemctl", "suspend"]); }
    }
    PamContext {
        id: pam
        config: "hyprlock"
        user: users.lastUser
        onResponseRequiredChanged: {
            if (!responseRequired) return;
            // A single password prompt is supported; never reuse it for another challenge.
            if (!responseVisible && !auth.supplied) {
                auth.supplied = true;
                respond(auth.password);
                auth.password = "";
            } else {
                auth.password = "";
                abort();
                bridge.loginFailed();
            }
        }
        onCompleted: function(result) {
            auth.password = "";
            if (result === PamResult.Success) {
                bridge.loginSucceeded();
                auth.authenticated();
            } else bridge.loginFailed();
        }
    }
}
