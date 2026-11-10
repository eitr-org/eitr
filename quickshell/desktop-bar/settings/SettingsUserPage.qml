import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Users keeps personal profile controls separate from administrator account management.
Column {
    id: userPage
    required property var context
    readonly property var view: context
    readonly property var chooser: context.chooser
    // The helper lists every account; until it answers, your own row comes from the
    // live picture topic so the page never starts empty.
    readonly property var accounts: (view.helper.summary.items || []).length
        ? view.helper.summary.items
        : [{current: true, title: view.accountPicture.name || "", detail: ""}]
    width: parent ? parent.width : 0
    spacing: 12
    property alias pictureSheet: pictureSheet
    property alias profileEditor: profileEditor
    property alias passwordSheet: passwordSheet
    property alias removeSheet: removeSheet
    readonly property bool administrator: view.helper.summary.administrator === true
    readonly property bool managing: administrator && view.tab === "manage"
    TabStrip {
        objectName: "settings-user-tabs"
        width: parent.width
        height: visible ? 42 : 0
        visible: userPage.administrator
        foreground: SettingsPalette.foreground
        gold: SettingsPalette.gold
        carved: true
        choices: [{id: "users", label: Eitr.I18n.tr("Users")}, {id: "manage", label: Eitr.I18n.tr("Manage")}]
        current: userPage.managing ? "manage" : "users"
        onChosen: value => { userPage.view.tabRequested(value); userPage.view.contentY = 0; }
    }
    SettingsManageUsers {
        id: management
        visible: userPage.managing
        width: parent.width
        context: userPage.view
        accounts: userPage.accounts
    }
    property alias managementSheet: management.sheet
    ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
        title: Eitr.I18n.tr("Users")
        foreground: view.foreground
        visible: view.page === "user" && !userPage.managing
        width: parent.width
        spacing: 16
        Repeater {
            model: userPage.accounts
            Row {
                id: accountRow
                required property var modelData
                required property int index
                readonly property bool own: !!modelData.current
                spacing: 18
                Column {
                    spacing: 6
                    Item {
                        width: 80
                        height: 80
                        Eitr.Avatar {
                            objectName: accountRow.own ? "settings-user-avatar" : ""
                            anchors.fill: parent
                            size: 80
                            source: accountRow.own
                                ? (userPage.view.accountPicture.path ? "file://" + userPage.view.accountPicture.path + "?v=" + (userPage.view.accountPicture.version || 0) : "")
                                : (accountRow.modelData.picture ? "file://" + accountRow.modelData.picture : "")
                            initial: accountRow.own ? (userPage.view.accountPicture.initial || "") : (accountRow.modelData.initial || "")
                            accent: userPage.view.accent
                            background: userPage.view.background
                        }
                        MouseArea {
                            id: pictureMouse
                            SettingsTarget { objectName: "setting-user-change-picture" }

                            objectName: accountRow.own ? "settings-change-picture" : ""
                            anchors.fill: parent
                            visible: accountRow.own
                            hoverEnabled: true
                            enabled: !userPage.chooser.running && !profileEditor.busy
                            cursorShape: Qt.PointingHandCursor
                            onClicked: userPage.view.choosePicture()
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: width / 2
                            visible: pictureMouse.containsMouse || userPage.chooser.running
                            color: Qt.alpha("black", 0.35)
                            Text {
                                anchors.centerIn: parent
                                text: "󰄀"
                                color: "white"
                                font.pixelSize: 24
                            }
                        }
                        BarTooltip { target: pictureMouse; hovered: pictureMouse.containsMouse; text: Eitr.I18n.tr("Change picture"); foreground: userPage.view.foreground; background: userPage.view.background }
                    }
                    PanelButton {
                        objectName: accountRow.own ? "settings-remove-picture" : ""
                        anchors.horizontalCenter: parent.horizontalCenter
                        visible: accountRow.own && !!userPage.view.accountPicture.path
                        icon: true
                        text: "󰆴"
                        foreground: userPage.view.foreground
                        available: !profileEditor.busy && !userPage.chooser.running
                        Accessible.name: Eitr.I18n.tr("Remove picture")
                        SettingsTarget { objectName: "setting-user-remove-picture" }
                        onClicked: removeSheet.open()
                        HoverHandler { id: trashHover }
                        BarTooltip { target: parent; hovered: trashHover.hovered; text: Eitr.I18n.tr("Remove picture"); foreground: userPage.view.foreground; background: userPage.view.background }
                    }
                }
                Column {
                    y: 12
                    // Beside the 80 px picture column and the row's 18 px gap.
                    width: Math.max(160, userPage.width - 140)
                    spacing: 8
                    SettingsText {
                        text: (accountRow.own ? userPage.view.accountPicture.name : accountRow.modelData.title) || accountRow.modelData.title || Eitr.I18n.tr("Unavailable")
                        font.pixelSize: PanelStyle.headingSize
                    }
                    SettingsText {
                        visible: text !== ""
                        text: [accountRow.modelData.login && accountRow.modelData.login !== accountRow.modelData.title ? accountRow.modelData.login : "",
                               accountRow.modelData.detail || "", accountRow.own ? Eitr.I18n.tr("You") : ""].filter(part => part).join(" · ")
                        color: Qt.alpha(userPage.view.foreground, PanelStyle.secondaryTextOpacity)
                        font.pixelSize: PanelStyle.captionSize
                    }
                    Row {
                        visible: accountRow.own
                        spacing: 12
                        PanelButton {
                            SettingsTarget { objectName: "setting-user-change-password" }
                            objectName: "settings-change-password"
                            width: 170
                            foreground: userPage.view.foreground
                            text: Eitr.I18n.tr("Change password")
                            onClicked: passwordSheet.open()
                        }
                        SettingsText {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: !passwordSheet.opened && passwordSheet.notice !== ""
                            text: passwordSheet.notice
                        }
                    }
                    SettingsText {
                        visible: accountRow.own && !pictureSheet.opened && profileEditor.error !== ""
                        text: profileEditor.error
                    }
                }
            }
        }
    }
    SettingsPasswordSheet {
        id: passwordSheet
        view: userPage.view
        live: userPage.view.live !== false
    }
    // Removing the picture asks first: it also leaves the lockscreen and login screen.
    SettingsConfirmSheet {
        id: removeSheet
        objectName: "settings-remove-picture-sheet"
        confirmName: "settings-confirm-remove-picture"
        foreground: view.foreground; surfaceColor: view.background
        title: Eitr.I18n.tr("Remove picture?")
        message: Eitr.I18n.tr("Your initial shows instead, and the lockscreen and login screen show no picture.")
        onConfirmed: profileEditor.remove()
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
