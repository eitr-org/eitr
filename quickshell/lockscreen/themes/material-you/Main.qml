import QtQuick
import LockscreenComponents

MaterialYouDesign {
    settings: config
    auth: typeof sddm !== "undefined" ? sddm : null
    users: typeof userModel !== "undefined" ? userModel : null
    sessions: typeof sessionModel !== "undefined" ? sessionModel : null
    keyboardState: typeof keyboard !== "undefined" ? keyboard : null
    background: Qt.resolvedUrl(config.background)
    fontSource: ""
}
