import Eitr as Eitr
import QtQuick
import QtQuick.Window

Rectangle {
    id: root

    width: Screen.width
    height: Screen.height
    property var settings: ({})
    property var auth: null
    property var users: null
    property var sessions: null
    property string variant: "tape"
    property date now: new Date()
    readonly property bool light: settings.themeMode === "light"
    readonly property real unit: Math.max(0.65, Math.min(width / 1440, height / 900))
    readonly property string runes: "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
    readonly property string family: "JetBrainsMono Nerd Font"
    readonly property color ink: light ? "#292521" : "#e9e1d5"
    readonly property color muted: light ? "#887b6a" : "#887f74"
    readonly property color accent: settings.accent || (variant === "neo-orbital"
        ? (light ? "#3e776b" : "#91bdb0") : light ? "#956344" : "#d2a47c")
    readonly property color surface: light ? "#e6ded1" : "#171817"
    readonly property string hours: Qt.formatDateTime(now, "HH")
    readonly property string minutes: Qt.formatDateTime(now, "mm")
    readonly property string seconds: Qt.formatDateTime(now, "ss")
    color: light ? "#f1eade" : "#101211"

    Timer { interval: 1000; running: root.visible; repeat: true; onTriggered: root.now = new Date() }
    // The lock host focuses the design's root item; typing belongs in the password field.
    onActiveFocusChanged: if (activeFocus) password.forceActiveFocus()
    LoginController {
        id: login
        onUserIndexChanged: password.text = ""
        sddm: root.auth; userModel: root.users; sessionModel: root.sessions
        onLoginFailed: { error.text = "Unable to unlock. Try again."; password.forceActiveFocus(); }
        onLoginSucceeded: { password.text = ""; error.text = ""; }
    }

    // A static drafting grid gives the scene depth without a full-screen shader.
    Repeater {
        model: Math.ceil(root.width / (80 * root.unit))
        Rectangle { required property int index; x: index * 80 * root.unit; width: 1; height: root.height; color: root.ink; opacity: 0.022 }
    }
    Repeater {
        model: Math.ceil(root.height / (80 * root.unit))
        Rectangle { required property int index; y: index * 80 * root.unit; width: root.width; height: 1; color: root.ink; opacity: 0.022 }
    }
    Rectangle {
        x: root.width * 0.08; y: root.height * 0.12
        width: root.width * 0.84; height: 1; color: root.ink; opacity: 0.09
    }
    Text {
        x: root.width * 0.08; y: root.height * 0.12 - 34 * root.unit
        text: Eitr.I18n.tr("E I T R  /  CLOCKWORK"); color: root.ink
        font.family: root.family; font.pixelSize: 12 * root.unit; font.letterSpacing: 2 * root.unit
    }
    Text {
        anchors.right: parent.right; anchors.rightMargin: root.width * 0.08
        y: root.height * 0.12 - 34 * root.unit
        text: root.variant === "tape" ? Eitr.I18n.tr("01 / TAPE") : Eitr.I18n.tr("02 / NEO ORBITAL")
        color: root.muted; font.family: root.family; font.pixelSize: 11 * root.unit
    }

    Item {
        id: composition
        width: Math.min(root.width * 0.84, 1220 * root.unit)
        height: Math.min(root.height * 0.66, 550 * root.unit)
        anchors.centerIn: parent
        readonly property bool stacked: root.width < 900

        Item {
            id: instrument
            width: composition.stacked ? composition.width : composition.width * 0.60
            height: composition.stacked ? composition.height * 0.48 : composition.height
            anchors.left: parent.left
            anchors.top: parent.top

            Item {
                id: tapes
                visible: root.variant === "tape"
                width: parent.width * 0.93; height: parent.height * 0.68
                anchors.centerIn: parent
                Row {
                    anchors.centerIn: parent
                    spacing: 14 * root.unit
                    Repeater {
                        model: 3
                        Item {
                            id: reel
                            required property int index
                            width: (tapes.width - 28 * root.unit) / 3
                            height: tapes.height
                            readonly property int value: Number(index === 0 ? root.hours : index === 1 ? root.minutes : root.seconds)
                            readonly property int count: index === 0 ? 24 : 60
                            property real offset: 0
                            onValueChanged: settle.restart()
                            NumberAnimation { id: settle; target: reel; property: "offset"; from: 1; to: 0; duration: 540; easing.type: Easing.OutCubic }
                            Rectangle { anchors.fill: parent; color: root.surface; radius: 8 * root.unit; border.color: Qt.alpha(root.ink, 0.12) }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter; y: 18 * root.unit
                                text: ["HOURS", "MINUTES", "SECONDS"][reel.index]
                                font.family: root.family; font.pixelSize: 10 * root.unit; font.letterSpacing: 2 * root.unit; color: root.muted
                            }
                            Item {
                                anchors.centerIn: parent; width: parent.width; height: parent.height * 0.65; clip: true
                                Repeater {
                                    model: 7
                                    Text {
                                        required property int index
                                        readonly property int tick: reel.value + index - 3
                                        readonly property real distance: index - 3 + reel.offset
                                        text: String((tick % reel.count + reel.count) % reel.count).padStart(2, "0")
                                        width: parent.width; horizontalAlignment: Text.AlignHCenter
                                        height: 83 * root.unit
                                        y: parent.height / 2 - height / 2 + distance * height
                                        color: Math.abs(distance) < 0.5 ? root.ink : root.muted
                                        opacity: Math.max(0, 1 - Math.abs(distance) * 0.48)
                                        font.family: root.family; font.pixelSize: 67 * root.unit; font.weight: Font.Light
                                    }
                                }
                            }
                            Rectangle { x: 12 * root.unit; width: 4 * root.unit; height: 28 * root.unit; anchors.verticalCenter: parent.verticalCenter; radius: 2; color: root.accent }
                            Rectangle { anchors.bottom: parent.bottom; anchors.bottomMargin: 18 * root.unit; anchors.horizontalCenter: parent.horizontalCenter; width: parent.width * 0.6; height: 1; color: root.accent; opacity: 0.35 }
                        }
                    }
                }
            }

            Text {
                visible: root.variant === "tape"
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: tapes.bottom; anchors.topMargin: 14 * root.unit
                text: "ᚠ  ᚢ  ᚦ  ᚨ  ᚱ  ᚲ  ᚷ  ᚹ"
                font.family: "Noto Sans Runic"; font.pixelSize: 18 * root.unit
                color: root.accent; opacity: 0.65
            }

            Item {
                id: dial
                visible: root.variant !== "tape"
                width: Math.min(parent.width * 0.83, parent.height * 0.93)
                height: width
                anchors.centerIn: parent
                readonly property bool neo: root.variant === "neo-orbital"
                Rectangle {
                    visible: dial.neo; anchors.centerIn: parent
                    width: parent.width * 1.16; height: parent.height * 0.42
                    radius: height / 2; rotation: -32
                    color: "transparent"; border.color: Qt.alpha(root.accent, 0.20)
                }
                Rectangle { anchors.fill: parent; radius: width / 2; color: "transparent"; border.color: Qt.alpha(root.ink, 0.14) }
                Rectangle { anchors.centerIn: parent; width: parent.width * 0.90; height: width; radius: width / 2; color: "transparent"; border.color: Qt.alpha(root.ink, 0.04); border.width: 14 * root.unit }
                Repeater {
                    model: 24
                    Item {
                        required property int index
                        anchors.fill: parent; rotation: index * 15
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: 27 * root.unit
                            text: root.runes.charAt(parent.index)
                            font.family: "Noto Sans Runic"; font.pixelSize: 14 * root.unit
                            color: root.accent; opacity: 0.65
                        }
                    }
                }
                Repeater {
                    model: 60
                    Item {
                        required property int index
                        anchors.fill: parent; rotation: index * 6
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter; y: 15 * root.unit
                            width: index % 5 === 0 ? 2 * root.unit : 1
                            height: index % 5 === 0 ? 14 * root.unit : 5 * root.unit
                            color: index % 5 === 0 ? root.accent : Qt.alpha(root.ink, 0.22)
                        }
                    }
                }
                Item {
                    anchors.fill: parent
                    RotationAnimator on rotation { from: 0; to: 360; duration: 60000; loops: Animation.Infinite; running: dial.visible && root.visible }
                    Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: -4 * root.unit; width: 8 * root.unit; height: width; radius: width / 2; color: root.accent }
                }
                Item {
                    width: parent.width * 0.70; height: width
                    anchors.centerIn: parent; anchors.horizontalCenterOffset: dial.neo ? -parent.width * 0.10 : 0
                    Rectangle { anchors.fill: parent; radius: width / 2; color: "transparent"; border.color: Qt.alpha(root.accent, 0.3); border.width: 1 }
                    Item {
                        anchors.fill: parent
                        RotationAnimator on rotation { from: 360; to: 0; duration: 180000; loops: Animation.Infinite; running: dial.visible && root.visible }
                        Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: -3 * root.unit; width: 6 * root.unit; height: width; radius: width / 2; color: root.ink }
                    }
                }
                Column {
                    anchors.centerIn: parent; spacing: 10 * root.unit
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: dial.neo ? Eitr.I18n.tr("LOCAL / TIME") : Eitr.I18n.tr("SYSTEM / TIME"); color: root.muted; font.family: root.family; font.pixelSize: 10 * root.unit; font.letterSpacing: 3 * root.unit }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: root.hours + ":" + root.minutes; color: root.ink; font.family: root.family; font.pixelSize: (dial.neo ? 60 : 68) * root.unit; font.weight: Font.Light }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: root.seconds + " / 60"; color: root.accent; font.family: root.family; font.pixelSize: 13 * root.unit; font.letterSpacing: 2 * root.unit }
                }
                Text {
                    visible: dial.neo; x: parent.width * 0.82; y: parent.height * 0.78
                    text: "↗\n" + Qt.formatDateTime(root.now, "dd"); color: root.accent; font.family: root.family; font.pixelSize: 22 * root.unit
                }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 0
                text: Qt.formatDateTime(root.now, "dddd · MMMM dd, yyyy").toUpperCase()
                color: root.muted; font.family: root.family; font.pixelSize: 11 * root.unit; font.letterSpacing: root.unit
            }
        }

        Rectangle {
            visible: !composition.stacked
            x: composition.width * 0.65; y: composition.height * 0.15
            width: 1; height: composition.height * 0.70; color: Qt.alpha(root.ink, 0.10)
        }
        Column {
            id: unlock
            width: Math.min(340 * root.unit, composition.stacked ? composition.width : composition.width * 0.30)
            x: composition.stacked ? (composition.width - width) / 2 : composition.width - width
            y: composition.stacked ? composition.height * 0.58 : (composition.height - height) / 2
            spacing: 20 * root.unit
            Text { text: Eitr.I18n.tr("WELCOME BACK"); font.family: root.family; font.pixelSize: 10 * root.unit; font.letterSpacing: 3 * root.unit; color: root.accent }
            UserPicker {
                controller: login
                unit: root.unit
                width: parent.width
                ink: root.ink; surface: root.surface
            }
            Text { visible: !login.canPickUser; width: parent.width; elide: Text.ElideRight; text: login.userName || Eitr.I18n.tr("EITR"); font.family: root.family; font.pixelSize: 32 * root.unit; color: root.ink }
            Text { text: Eitr.I18n.tr("Your workspace awaits."); font.family: root.family; font.pixelSize: 12 * root.unit; color: root.muted }
            Rectangle {
                width: parent.width; height: 50 * root.unit; radius: 5 * root.unit
                color: root.surface; border.color: password.activeFocus ? Qt.alpha(root.accent, 0.65) : Qt.alpha(root.ink, 0.18)
                Text { visible: password.text.length === 0; x: 17 * root.unit; anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Password"); color: root.muted; font.family: root.family; font.pixelSize: 13 * root.unit }
                TextInput {
                    id: password
                    anchors.fill: parent; anchors.margins: 16 * root.unit
                    verticalAlignment: TextInput.AlignVCenter; color: root.ink
                    font.family: root.family; font.pixelSize: 14 * root.unit
                    echoMode: TextInput.Password; selectByMouse: true; focus: true
                    onAccepted: { error.text = ""; login.login(text); text = ""; }
                }
            }
            Rectangle {
                width: parent.width; height: 44 * root.unit; radius: 5 * root.unit
                color: buttonMouse.containsMouse ? Qt.lighter(root.accent, 1.1) : root.accent
                Text { anchors.centerIn: parent; text: Eitr.I18n.tr("UNLOCK  →"); font.family: root.family; font.pixelSize: 12 * root.unit; font.letterSpacing: 2 * root.unit; color: root.color }
                MouseArea { id: buttonMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { error.text = ""; login.login(password.text); password.text = ""; } }
            }
            Text { id: error; width: parent.width; wrapMode: Text.Wrap; color: root.accent; font.family: root.family; font.pixelSize: 11 * root.unit }
            Row {
                visible: !login.isQuickshell; spacing: 16 * root.unit
                Text { text: Eitr.I18n.tr("USER"); color: root.muted; font.family: root.family; font.pixelSize: 11 * root.unit; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: login.cycleUser() } }
                Text { text: login.sessionName || Eitr.I18n.tr("SESSION"); color: root.muted; font.family: root.family; font.pixelSize: 11 * root.unit; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: login.cycleSession() } }
            }
        }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter; y: root.height * 0.89
        text: Eitr.I18n.tr("EITR  /  A MOMENT BETWEEN THINGS"); color: root.muted
        font.family: root.family; font.pixelSize: 10 * root.unit; font.letterSpacing: 2 * root.unit
    }
}
