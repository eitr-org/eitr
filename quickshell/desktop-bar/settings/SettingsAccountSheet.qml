import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Popup {
    id: sheet
    required property var view
    property string action: ""
    property var account: ({})
    property bool deleteHome: false
    readonly property string heading: action === "set-type" ? Eitr.I18n.tr("Change type")
        : action === "set-password" ? Eitr.I18n.tr("Set password") : Eitr.I18n.tr("Remove")
    signal confirmed(var arguments)
    objectName: "settings-account-sheet"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 420
    padding: 24
    modal: true
    dim: true
    focus: true
    closePolicy: Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: Qt.alpha("black", 0.45) }
    onOpened: confirm.forceActiveFocus()
    function review(kind, target) {
        action = kind;
        account = target;
        deleteHome = false;
        open();
    }
    function submit() {
        let arguments = [action, account.login];
        if (action === "set-type") arguments = arguments.concat(["--account-type", account.administrator ? "standard" : "administrator"]);
        if (action === "remove" && deleteHome) arguments.push("--delete-home");
        close();
        confirmed(arguments);
    }
    background: Rectangle {
        radius: DesktopStyle.radius(12)
        color: Qt.rgba(sheet.view.background.r, sheet.view.background.g, sheet.view.background.b, 1)
        border.width: 1
        border.color: Qt.alpha(SettingsInk.gold, 0.4)
    }
    contentItem: Column {
        spacing: 14
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: sheet.heading
            color: sheet.view.foreground
            font.family: SiteStyle.carved
            font.pixelSize: PanelStyle.headingSize
        }
        SettingsText {
            width: parent.width
            wrapMode: Text.WordWrap
            text: sheet.account.login || ""
        }
        SettingsText {
            width: parent.width
            wrapMode: Text.WordWrap
            text: sheet.action === "set-type"
                ? (sheet.account.administrator ? Eitr.I18n.tr("Change to Standard") : Eitr.I18n.tr("Change to Administrator"))
                : sheet.action === "set-password"
                ? Eitr.I18n.tr("Their login keyring cannot be updated and will keep its old password. Enter the new password in the terminal.")
                : Eitr.I18n.tr("Remove this account? Keeping the home folder preserves its files.")
        }
        ChoiceSegmented {
            width: parent.width
            visible: sheet.action === "remove"
            foreground: sheet.view.foreground
            choices: [{id: "keep", label: Eitr.I18n.tr("Keep home folder")}, {id: "delete", label: Eitr.I18n.tr("Delete home folder")}]
            current: sheet.deleteHome ? "delete" : "keep"
            onChosen: value => sheet.deleteHome = value === "delete"
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8
            PanelButton { width: 110; foreground: sheet.view.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: sheet.close() }
            PanelButton {
                id: confirm
                objectName: "settings-confirm-account"
                width: 150
                foreground: sheet.view.foreground
                text: Eitr.I18n.tr("Continue")
                onClicked: sheet.submit()
            }
        }
    }
}
