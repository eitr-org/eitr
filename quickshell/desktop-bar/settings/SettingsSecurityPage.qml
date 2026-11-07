import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: pageBody
    required property var context
    width: parent ? parent.width : 0
    spacing: 12
    SettingsSummaryCards { context: pageBody.context }
}
