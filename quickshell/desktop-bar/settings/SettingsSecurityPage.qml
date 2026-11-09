import ".."
import QtQuick
import Eitr as Eitr

Column {
    id: pageBody
    required property var context
    width: parent ? parent.width : 0
    spacing: 12
    // Sign-in and Protection: the helper tags each row with its tab.
    TabStrip { foreground: SettingsPalette.foreground; gold: SettingsPalette.gold; carved: true
        objectName: "settings-security-tabs"
        width: parent.width
        height: 42
        choices: [{id: "sign-in", label: Eitr.I18n.tr("Sign-in")}, {id: "protection", label: Eitr.I18n.tr("Protection")}]
        current: pageBody.context.tab
        onChosen: value => { pageBody.context.tabRequested(value); pageBody.context.contentY = 0; }
    }
    SettingsSummaryCards { context: pageBody.context }
}
