import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: pageBody
    required property var context
    readonly property var view: context
    width: parent ? parent.width : 0
    spacing: 12
    TextField {
        onTextChanged: view.shortcutQuery = text
        visible: view.page === "keybinds"
        width: parent.width
        placeholderText: Eitr.I18n.tr("Search shortcuts")
        placeholderTextColor: Qt.alpha(view.foreground, PanelStyle.secondaryTextOpacity)
        color: view.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        background: Rectangle {
            radius: DesktopStyle.radius(6)
            color: Qt.alpha(view.foreground, 0.05)
        }
    }
    SettingsSummaryCards { context: pageBody.context }
    SettingsText {
        visible: view.page === "keybinds" && view.matches.length === 0
        text: Eitr.I18n.tr("No matching shortcuts")
    }
}
