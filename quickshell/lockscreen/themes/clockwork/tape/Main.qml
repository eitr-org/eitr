import QtQuick
import LockscreenComponents

EitrClockworkDesign {
    variant: "tape"
    settings: config
    auth: typeof sddm !== "undefined" ? sddm : null
    users: typeof userModel !== "undefined" ? userModel : null
    sessions: typeof sessionModel !== "undefined" ? sessionModel : null
}
