import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    required property var context
    readonly property var view: context
    readonly property var chooser: context.chooser
    width: parent ? parent.width : 0
    spacing: 12
    property alias pictureSheet: pictureSheet
    property alias profileEditor: profileEditor
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("User")
        foreground: view.foreground
        visible: view.page === "user"
        width: parent.width
        spacing: 12
        Row {
            spacing: 18
            Eitr.Avatar {
                objectName: "settings-user-avatar"
                size: 80
                source: view.accountPicture.path ? "file://" + view.accountPicture.path + "?v=" + (view.accountPicture.version || 0) : ""
                initial: view.accountPicture.initial || ""
                accent: view.accent
                background: view.background
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 10
                SettingsText {
                    text: view.accountPicture.name || Eitr.I18n.tr("Unavailable")
                    font.pixelSize: PanelStyle.headingSize
                }
                Row {
                    spacing: 8
                    PanelButton {
                        objectName: "settings-change-picture"
                        width: 150
                        foreground: view.foreground
                        text: Eitr.I18n.tr("Change picture")
                        loading: chooser.running
                        available: !profileEditor.busy
                        onClicked: view.choosePicture()
                    }
                    PanelButton {
                        objectName: "settings-remove-picture"
                        width: 110
                        visible: !!view.accountPicture.path
                        foreground: view.foreground
                        text: Eitr.I18n.tr("Remove")
                        available: !profileEditor.busy && !chooser.running
                        onClicked: profileEditor.remove()
                    }
                }
                SettingsText {
                    visible: !pictureSheet.opened && profileEditor.error !== ""
                    text: profileEditor.error
                }
            }
        }
    }
    Popup {
        id: pictureSheet
        objectName: "settings-picture-sheet"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300
        padding: 24
        modal: true
        dim: true
        focus: true
        closePolicy: Popup.NoAutoClose
        onOpened: profileEditor.forceActiveFocus()
        Overlay.modal: Rectangle { color: Qt.alpha("black", 0.45) }
        background: Rectangle {
            radius: DesktopStyle.radius(12)
            color: Qt.rgba(view.background.r, view.background.g, view.background.b, 1)
            border.width: 1
            border.color: Qt.alpha(SettingsInk.gold, 0.4)
        }
        contentItem: Column {
            spacing: 16
            Text {
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: Eitr.I18n.tr("Profile picture")
                color: view.foreground
                font.family: SiteStyle.carved
                font.pixelSize: PanelStyle.headingSize
            }
            ProfilePicture {
                id: profileEditor
                objectName: "settings-profile-picture"
                width: parent.width
                account: view.accountPicture
                foreground: view.foreground
                background: view.background
                accent: view.accent
                onFinished: pictureSheet.close()
            }
        }
    }
}
