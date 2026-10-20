import QtQuick

// Shared login state for lockscreen designs, working with SDDM and with the
// Quickshell bridge in AuthAdapter.qml. Pass the context objects explicitly:
// Quickshell exposes `sddm`, `userModel`, and `sessionModel` only to a design's
// Main.qml, not to components imported from this module.
Item {
    id: controller

    property var sddm: null
    property var userModel: null
    property var sessionModel: null

    signal loginFailed()
    signal loginSucceeded()

    // The Quickshell bridge marks itself; SDDM's object has no such property.
    readonly property bool isQuickshell: !sddm || sddm.quickshellLock === true
    property int userIndex: userModel && userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property int sessionIndex: sessionModel && sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    readonly property string userLogin: users.currentItem && users.currentItem.uLogin
        ? users.currentItem.uLogin : (userModel && userModel.lastUser ? userModel.lastUser : "")
    readonly property string userName: users.currentItem && users.currentItem.uName
        ? users.currentItem.uName : userLogin
    readonly property string sessionName: sessions.currentItem ? sessions.currentItem.sName : ""

    // Empty passwords are ignored; the bridge itself refuses logins in previews.
    function login(password) {
        if (sddm && password !== "")
            sddm.login(userLogin, password, sessionIndex);
    }

    // Quickshell locks only the current user and session.
    function cycleUser() {
        if (!isQuickshell && userModel && userModel.rowCount() > 0)
            userIndex = (userIndex + 1) % userModel.rowCount();
    }

    function cycleSession() {
        if (!isQuickshell && sessionModel && sessionModel.rowCount() > 0)
            sessionIndex = (sessionIndex + 1) % sessionModel.rowCount();
    }

    Connections {
        target: controller.sddm
        function onLoginFailed() { controller.loginFailed(); }
        function onLoginSucceeded() { controller.loginSucceeded(); }
    }

    // Model roles are read through delegates because SDDM's models are not
    // ListModels. The views are invisible and never take input.
    ListView {
        id: users
        model: controller.userModel
        currentIndex: controller.userIndex
        width: 100
        height: 100
        opacity: 0
        enabled: false
        delegate: Item {
            property string uName: model.realName || model.name || ""
            property string uLogin: model.name || ""
        }
    }

    ListView {
        id: sessions
        model: controller.sessionModel
        currentIndex: controller.sessionIndex
        width: 100
        height: 100
        opacity: 0
        enabled: false
        delegate: Item {
            property string sName: model.name || ""
        }
    }
}
