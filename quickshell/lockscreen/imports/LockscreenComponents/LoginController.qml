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
    property var keyboard: null

    signal loginFailed()
    signal loginSucceeded()
    signal loginSubmitted()

    // The Quickshell bridge marks itself; SDDM's object has no such property.
    readonly property bool isQuickshell: !sddm || sddm.quickshellLock === true
    property int userIndex: userModel && userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property int sessionIndex: sessionModel && sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    readonly property string userLogin: users.currentItem && users.currentItem.uLogin
        ? users.currentItem.uLogin : (userModel && userModel.lastUser ? userModel.lastUser : "")
    readonly property string userName: users.currentItem && users.currentItem.uName
        ? users.currentItem.uName : userLogin
    readonly property string userIcon: {
        const icon = users.currentItem ? users.currentItem.uIcon : "";
        if (!isQuickshell && /^(file:\/\/)?\/usr\/share\/sddm\/faces\//.test(icon)) return "";
        return icon && icon.indexOf(":") === -1 ? "file://" + icon : icon;
    }
    readonly property string sessionName: sessions.currentItem ? sessions.currentItem.sName : ""

    readonly property int userCount: users.count
    readonly property bool canPickUser: !isQuickshell && userCount > 1

    readonly property var layoutList: {
        if (!keyboard || !keyboard.layouts) return [];
        const raw = keyboard.layouts;
        const items = [];
        if (typeof raw.length === "number") {
            for (let index = 0; index < raw.length; index++) items.push(raw[index]);
        } else if (typeof raw.count === "number" && typeof raw.get === "function") {
            for (let index = 0; index < raw.count; index++) items.push(raw.get(index));
        }
        return items;
    }
    readonly property int layoutCount: layoutList.length
    readonly property bool canSwitchLayout: layoutCount > 1
    readonly property int currentLayoutIndex: {
        if (!keyboard || layoutCount === 0) return 0;
        const current = Number(keyboard.currentLayout);
        return (current >= 0 && current < layoutCount) ? current : 0;
    }
    function formatLayoutCode(entry, allEntries) {
        if (!entry) return "";
        if (entry.code) return String(entry.code).toUpperCase();
        const base = String(entry.shortName || entry.layout || entry.name || "").trim();
        const variant = String(entry.variant || "").trim();
        const sameBase = allEntries.filter(candidate =>
            String(candidate && (candidate.shortName || candidate.layout || candidate.name) || "").trim().toLowerCase() === base.toLowerCase()
        ).length > 1;
        if (sameBase) {
            if (variant) return variant.slice(0, 3).toUpperCase();
            const detail = String(entry.longName || entry.label || "");
            if (/intl|international/i.test(detail)) return "INT";
            const paren = detail.match(/\(([^)]+)\)/);
            if (paren) {
                const parts = paren[1].split(/[\s,;-]+/).filter(part => part && part.toLowerCase() !== base.toLowerCase());
                if (parts.length > 0) return parts[0].slice(0, 3).toUpperCase();
            }
        }
        return (base || String(entry.longName || entry.label || "").trim()).slice(0, 3).toUpperCase();
    }
    readonly property string layoutCode: layoutCount > 0 ? formatLayoutCode(layoutList[currentLayoutIndex], layoutList) : ""
    readonly property string layoutLabel: {
        if (layoutCount === 0) return "";
        const entry = layoutList[currentLayoutIndex];
        if (!entry) return "";
        return String(entry.label || entry.longName || entry.shortName || entry.code || "");
    }

    function nextLayout() {
        if (!keyboard || layoutCount <= 1) return;
        if (typeof keyboard.nextLayout === "function") {
            keyboard.nextLayout();
            return;
        }
        keyboard.currentLayout = (currentLayoutIndex + 1) % layoutCount;
    }

    // Empty passwords are ignored; the bridge itself refuses logins in previews.
    function login(password) {
        loginSubmitted();
        if (sddm && password !== "")
            sddm.login(userLogin, password, sessionIndex);
    }

    // Quickshell locks only the current user and session.
    function cycleUser(direction = 1) {
        if (!isQuickshell && userModel && userModel.rowCount() > 0)
            userIndex = (userIndex + direction + userCount) % userCount;
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
            property string uIcon: model.icon || ""
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
