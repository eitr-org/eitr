import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "general"; width: parent.width; spacing: 12
    ControlCenterSection { centerRef: section.centerRef; text: Eitr.I18n.tr("Power"); width: parent.width }
    PowerControls { visible: section.centerRef.battery.available; width: parent.width; battery: section.centerRef.battery; displayControl: section.centerRef.displayControl; foreground: section.centerRef.foreground }
    // Lock is the everyday action; the session-ending ones sit behind one labelled button.
    GridLayout {
        width: parent.width; columns: 2; columnSpacing: PanelStyle.selectionActionGap; rowSpacing: PanelStyle.selectionRowGap
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Lock"); glyph: ""; onClicked: section.centerRef.runAfterClose(["bash", Eitr.Paths.code("hypr/scripts/manual-lock.sh")]) }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Power…"); glyph: ""; selected: section.centerRef.powerOpen; onClicked: section.centerRef.powerOpen = !section.centerRef.powerOpen }
        Repeater {
            model: section.centerRef.powerOpen ? [
                {title: Eitr.I18n.tr("Logout"), icon: "", command: ["uwsm", "stop"]},
                {title: Eitr.I18n.tr("Suspend"), icon: "", command: ["sh", "-c", "loginctl lock-session && sleep 1 && systemctl suspend"]},
                {title: Eitr.I18n.tr("Reboot"), icon: "", command: ["systemctl", "reboot", "--no-wall"]},
                {title: Eitr.I18n.tr("Shutdown"), icon: "", command: ["systemctl", "poweroff", "--no-wall"]}
            ] : []
            ControlCenterGridAction { centerRef: section.centerRef;
                required property var modelData
                title: modelData.title; glyph: modelData.icon
                onClicked: section.centerRef.runAfterClose(modelData.command)
            }
        }
    }
}
