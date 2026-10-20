import Eitr as Eitr
import QtQuick
import QtQuick.Window
import Qt5Compat.GraphicalEffects

// Material You lockscreen shared by the material-you and material-you-dark
// designs. Each design's Main.qml passes its context objects and assets; its
// theme.conf selects `themeMode=light|dark` and the `background` image.
Rectangle {
    id: root
    width: Screen.width
    height: Screen.height
    color: root.colors.background

    property var settings: ({})
    property var auth: null
    property var users: null
    property var sessions: null
    property var keyboardState: null
    // Theme-relative assets, resolved by the design's Main.qml.
    property url background
    property url fontSource

    readonly property bool dark: String(settings && settings.themeMode || "light") === "dark"
    readonly property var colors: dark ? darkColors : lightColors
    readonly property var lightColors: ({
        accentContainer: "#BEE8C7",
        background: "#ffffff",
        button: "#0F3C2C",
        buttonHover: "#1E4F3E",
        buttonPressed: "#0A281D",
        card: "#E9F3EB",
        chipButton: "#eef6f0",
        chipButtonHover: "#d2ebd4",
        chipButtonPressed: "#cbe8cc",
        chipButtonText: "#1d3c34",
        error: "#ea1821",
        field: "#D0EADB",
        fieldIcon: "#1d3c34",
        fieldText: "#1d3c34",
        focus: "#0F3C2C",
        mutedText: "#8ca090",
        onStrong: "#BEE8C7",
        primaryText: "#0F3C2C",
        secondaryText: "#1E4F3E",
        selection: "#c2ebd4",
        tile: "#E9F3EB",
        tileCaption: "#1E4F3E",
        tileCaptionHover: "#E9F3EB",
        tileHover: "#0F3C2C",
        tilePressed: "#0A281D",
        tileTitle: "#0F3C2C"
    })
    readonly property var darkColors: ({
        accentContainer: "#3A3247",
        background: "#131218",
        button: "#3A3247",
        buttonHover: "#4F4461",
        buttonPressed: "#2B2238",
        card: "#1C1B20",
        chipButton: "#2B2930",
        chipButtonHover: "#36343B",
        chipButtonPressed: "#201E25",
        chipButtonText: "#CBC2DB",
        error: "#FFB4AB",
        field: "#2B2930",
        fieldIcon: "#D0BCFF",
        fieldText: "#E6E1E5",
        focus: "#D0BCFF",
        mutedText: "#958DA5",
        onStrong: "#E6E1E5",
        primaryText: "#E6E1E5",
        secondaryText: "#CBC2DB",
        selection: "#4F4461",
        tile: "#25232A",
        tileCaption: "#958DA5",
        tileCaptionHover: "#CBC2DB",
        tileHover: "#322A3E",
        tilePressed: "#1C1924",
        tileTitle: "#CBC2DB"
    })

    // Background
    Image {
        anchors.fill: parent
        source: root.background
        fillMode: Image.PreserveAspectCrop
    }

    readonly property real s: Screen.height / 768

    LoginController {
        id: login
        sddm: root.auth
        userModel: root.users
        sessionModel: root.sessions
        onLoginFailed: {
            root.errorMessage = Eitr.I18n.tr("ACCESS DENIED");
            pwd.text = "";
            shakeAnim.start();
            errTimer.start();
        }
    }

    // UI States
    property real ui1: 0
    property real ui2: 0
    property string errorMessage: ""

    // Fonts
    QtObject { id: customFont; readonly property string name: "JetBrainsMono Nerd Font"; readonly property string source: "" }

    readonly property string sansFont: customFont.name !== "" ? customFont.name : "JetBrainsMono Nerd Font"

    Timer {
        id: focusTimer
        interval: 300
        running: true
        onTriggered: pwd.forceActiveFocus()
    }

    Timer {
        id: errTimer
        interval: 3000
        onTriggered: root.errorMessage = ""
    }

    Component.onCompleted: {
        fadeAnim.start();
        if (root.keyboardState) root.keyboardState.numLock = true;
    }

    SequentialAnimation {
        id: fadeAnim
        PauseAnimation { duration: 500 }
        ParallelAnimation {
            NumberAnimation { target: root; property: "ui1"; from: 0; to: 1; duration: 900; easing.type: Easing.OutCubic }
            NumberAnimation { target: root; property: "ui2"; from: 0; to: 1; duration: 900; easing.type: Easing.OutCubic }
        }
    }

    SequentialAnimation {
        id: shakeAnim
        NumberAnimation { target: shakeTranslate; property: "x"; to: 15*s; duration: 50 }
        NumberAnimation { target: shakeTranslate; property: "x"; to: -15*s; duration: 50 }
        NumberAnimation { target: shakeTranslate; property: "x"; to: 15*s; duration: 50 }
        NumberAnimation { target: shakeTranslate; property: "x"; to: -15*s; duration: 50 }
        NumberAnimation { target: shakeTranslate; property: "x"; to: 0; duration: 50 }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.ArrowCursor
        z: -1
        onClicked: pwd.forceActiveFocus()
    }

    // Layout Row
    Row {
        id: mainLayout
        anchors.centerIn: parent
        spacing: 96 * s
        opacity: root.ui1
        scale: 0.96 + (0.04 * root.ui1)
        transform: Translate { y: (1 - root.ui1) * 30 * s }

        // Left Section
        Column {
            spacing: 24 * s
            anchors.verticalCenter: parent.verticalCenter

            Timer {
                interval: 1000
                running: true
                repeat: true
                onTriggered: {
                    let d = new Date();
                    hText.text = Qt.formatTime(d, "hh");
                    mText.text = Qt.formatTime(d, "mm");
                    dateChipText.text = Qt.formatDate(d, "dddd, MMM d").toUpperCase();
                }
            }

            // Clock
            Column {
                spacing: -24 * s

                Text {
                    id: hText
                    text: Qt.formatTime(new Date(), "hh")
                    font.family: root.sansFont
                    font.pixelSize: 140 * s
                    font.weight: Font.Bold
                    color: root.colors.primaryText
                }

                Text {
                    id: mText
                    text: Qt.formatTime(new Date(), "mm")
                    font.family: root.sansFont
                    font.pixelSize: 140 * s
                    font.weight: Font.Bold
                    color: root.colors.secondaryText
                }
            }

            // Date Pill
            Rectangle {
                width: dateChipText.implicitWidth + 32 * s
                height: 44 * s
                radius: 22 * s
                color: root.colors.accentContainer

                Text {
                    id: dateChipText
                    anchors.centerIn: parent
                    text: Qt.formatDate(new Date(), "dddd, MMM d").toUpperCase()
                    font.family: root.sansFont
                    font.pixelSize: 11 * s
                    font.bold: true
                    font.letterSpacing: 1 * s
                    color: root.colors.primaryText
                }
            }
        }

        // Right Section
        Column {
            spacing: 24 * s
            anchors.verticalCenter: parent.verticalCenter

            // Settings Title
            Text {
                text: Eitr.I18n.tr("QUICK SETTINGS")
                font.family: root.sansFont
                font.pixelSize: 11 * s
                font.bold: true
                font.letterSpacing: 1.5 * s
                color: root.colors.mutedText
            }

            // Settings Grid
            Grid {
                columns: 2
                spacing: 16 * s

                // Power
                Rectangle {
                    id: powerTile
                    width: 180 * s; height: 76 * s; radius: 38 * s
                    color: powerMouse.pressed ? root.colors.tilePressed : (powerMouse.containsMouse ? root.colors.tileHover : root.colors.tile)
                    scale: powerMouse.pressed ? 0.95 : (powerMouse.containsMouse ? 1.03 : 1.0)
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 16 * s
                        anchors.rightMargin: 16 * s
                        spacing: 12 * s

                        Rectangle {
                            width: 48 * s; height: 48 * s; radius: 24 * s
                            color: root.colors.accentContainer
                            anchors.verticalCenter: parent.verticalCenter

                            Image {
                                id: powerIcon
                                source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M18.36 6.64a9 9 0 1 1-12.73 0'></path><line x1='12' y1='2' x2='12' y2='12'></line></svg>"
                                anchors.centerIn: parent
                                width: 20 * s
                                height: 20 * s
                                sourceSize.width: 40 * s
                                sourceSize.height: 40 * s
                                visible: false
                            }
                            ColorOverlay {
                                anchors.fill: powerIcon
                                source: powerIcon
                                color: root.colors.primaryText
                            }
                        }

                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2 * s

                            Text {
                                text: Eitr.I18n.tr("POWER")
                                font.family: root.sansFont
                                font.pixelSize: 12 * s
                                font.bold: true
                                color: powerMouse.containsMouse ? root.colors.onStrong : root.colors.tileTitle
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            Text {
                                text: Eitr.I18n.tr("SHUT DOWN")
                                font.family: root.sansFont
                                font.pixelSize: 9 * s
                                color: powerMouse.containsMouse ? root.colors.tileCaptionHover : root.colors.tileCaption
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                        }
                    }

                    MouseArea {
                        id: powerMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (!login.isQuickshell) root.auth.powerOff();
                    }
                }

                // Session
                Rectangle {
                    id: sessionTile
                    width: 180 * s; height: 76 * s; radius: 38 * s
                    color: sessionMouse.pressed ? root.colors.tilePressed : (sessionMouse.containsMouse ? root.colors.tileHover : root.colors.tile)
                    scale: sessionMouse.pressed ? 0.95 : (sessionMouse.containsMouse ? 1.03 : 1.0)
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 16 * s
                        anchors.rightMargin: 16 * s
                        spacing: 12 * s

                        Rectangle {
                            width: 48 * s; height: 48 * s; radius: 24 * s
                            color: root.colors.accentContainer
                            anchors.verticalCenter: parent.verticalCenter

                            Image {
                                id: sessionIcon
                                source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'></circle><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'></path></svg>"
                                anchors.centerIn: parent
                                width: 20 * s
                                height: 20 * s
                                sourceSize.width: 40 * s
                                sourceSize.height: 40 * s
                                visible: false
                            }
                            ColorOverlay {
                                anchors.fill: sessionIcon
                                source: sessionIcon
                                color: root.colors.primaryText
                            }
                        }

                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2 * s

                            Text {
                                text: Eitr.I18n.tr("SESSION")
                                font.family: root.sansFont
                                font.pixelSize: 12 * s
                                font.bold: true
                                color: sessionMouse.containsMouse ? root.colors.onStrong : root.colors.tileTitle
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            Text {
                                text: (login.sessionName || Eitr.I18n.tr("PLASMA")).toUpperCase()
                                font.family: root.sansFont
                                font.pixelSize: 9 * s
                                color: sessionMouse.containsMouse ? root.colors.tileCaptionHover : root.colors.tileCaption
                                Behavior on color { ColorAnimation { duration: 150 } }
                                elide: Text.ElideRight
                                width: 90 * s
                            }
                        }
                    }

                    MouseArea {
                        id: sessionMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            login.cycleSession();
                        }
                    }
                }

                // Reboot
                Rectangle {
                    id: rebootTile
                    width: 180 * s; height: 76 * s; radius: 38 * s
                    color: rebootMouse.pressed ? root.colors.tilePressed : (rebootMouse.containsMouse ? root.colors.tileHover : root.colors.tile)
                    scale: rebootMouse.pressed ? 0.95 : (rebootMouse.containsMouse ? 1.03 : 1.0)
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 16 * s
                        anchors.rightMargin: 16 * s
                        spacing: 12 * s

                        Rectangle {
                            width: 48 * s; height: 48 * s; radius: 24 * s
                            color: root.colors.accentContainer
                            anchors.verticalCenter: parent.verticalCenter

                            Image {
                                id: rebootIcon
                                source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='23 4 23 10 17 10'></polyline><path d='M20.49 15a9 9 0 1 1-2.12-9.36L23 10'></path></svg>"
                                anchors.centerIn: parent
                                width: 20 * s
                                height: 20 * s
                                sourceSize.width: 40 * s
                                sourceSize.height: 40 * s
                                visible: false
                            }
                            ColorOverlay {
                                anchors.fill: rebootIcon
                                source: rebootIcon
                                color: root.colors.primaryText
                            }
                        }

                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2 * s

                            Text {
                                text: Eitr.I18n.tr("REBOOT")
                                font.family: root.sansFont
                                font.pixelSize: 12 * s
                                font.bold: true
                                color: rebootMouse.containsMouse ? root.colors.onStrong : root.colors.tileTitle
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            Text {
                                text: Eitr.I18n.tr("RESTART")
                                font.family: root.sansFont
                                font.pixelSize: 9 * s
                                color: rebootMouse.containsMouse ? root.colors.tileCaptionHover : root.colors.tileCaption
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                        }
                    }

                    MouseArea {
                        id: rebootMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (!login.isQuickshell) root.auth.reboot();
                    }
                }

                // Sleep
                Rectangle {
                    id: suspendTile
                    width: 180 * s; height: 76 * s; radius: 38 * s
                    color: suspendMouse.pressed ? root.colors.tilePressed : (suspendMouse.containsMouse ? root.colors.tileHover : root.colors.tile)
                    scale: suspendMouse.pressed ? 0.95 : (suspendMouse.containsMouse ? 1.03 : 1.0)
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 16 * s
                        anchors.rightMargin: 16 * s
                        spacing: 12 * s

                        Rectangle {
                            width: 48 * s; height: 48 * s; radius: 24 * s
                            color: root.colors.accentContainer
                            anchors.verticalCenter: parent.verticalCenter

                            Image {
                                id: suspendIcon
                                source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'></path></svg>"
                                anchors.centerIn: parent
                                width: 20 * s
                                height: 20 * s
                                sourceSize.width: 40 * s
                                sourceSize.height: 40 * s
                                visible: false
                            }
                            ColorOverlay {
                                anchors.fill: suspendIcon
                                source: suspendIcon
                                color: root.colors.primaryText
                            }
                        }

                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2 * s

                            Text {
                                text: Eitr.I18n.tr("SLEEP")
                                font.family: root.sansFont
                                font.pixelSize: 12 * s
                                font.bold: true
                                color: suspendMouse.containsMouse ? root.colors.onStrong : root.colors.tileTitle
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            Text {
                                text: Eitr.I18n.tr("SUSPEND")
                                font.family: root.sansFont
                                font.pixelSize: 9 * s
                                color: suspendMouse.containsMouse ? root.colors.tileCaptionHover : root.colors.tileCaption
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                        }
                    }

                    MouseArea {
                        id: suspendMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: if (!login.isQuickshell) root.auth.suspend();
                    }
                }
            }

            // Login Card
            Rectangle {
                id: notificationCard
                width: 376 * s
                height: 180 * s
                radius: 32 * s
                color: root.colors.card
                transform: Translate { id: shakeTranslate }

                Column {
                    anchors.fill: parent
                    anchors.margins: 20 * s
                    spacing: 12 * s

                    // Header
                    Row {
                        width: parent.width
                        spacing: 8 * s

                        Item {
                            width: 12 * s
                            height: 12 * s
                            anchors.verticalCenter: parent.verticalCenter
                            Image {
                                id: lockIcon
                                source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='11' width='18' height='11' rx='2' ry='2'></rect><path d='M7 11V7a5 5 0 0 1 10 0v4'></path></svg>"
                                anchors.fill: parent
                                sourceSize.width: 24 * s
                                sourceSize.height: 24 * s
                                visible: false
                            }
                            ColorOverlay {
                                anchors.fill: lockIcon
                                source: lockIcon
                                color: root.colors.mutedText
                            }
                        }
                        Text {
                            text: Eitr.I18n.tr("SYSTEM UI")
                            font.family: root.sansFont
                            font.pixelSize: 10 * s
                            font.bold: true
                            font.letterSpacing: 1 * s
                            color: root.colors.mutedText
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: Eitr.I18n.tr("•  now")
                            font.family: root.sansFont
                            font.pixelSize: 10 * s
                            color: root.colors.mutedText
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    // Password Box
                    Rectangle {
                        width: parent.width
                        height: 52 * s
                        radius: 26 * s
                        color: root.colors.field
                        border.color: root.errorMessage !== "" ? root.colors.error : (pwd.activeFocus ? root.colors.focus : "transparent")
                        border.width: pwd.activeFocus ? 2 * s : 0
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        TextInput {
                            id: pwd
                            anchors.fill: parent
                            anchors.leftMargin: 20 * s
                            anchors.rightMargin: 20 * s
                            font.family: root.sansFont
                            font.pixelSize: 18 * s
                            font.letterSpacing: 6 * s
                            color: root.colors.fieldText
                            echoMode: TextInput.Password
                            passwordCharacter: "•"
                            horizontalAlignment: TextInput.AlignHCenter
                            verticalAlignment: TextInput.AlignVCenter
                            clip: true

                            cursorVisible: false
                            cursorDelegate: Item { width: 0; height: 0 }
                            selectionColor: root.colors.selection

                            property bool wasClicked: false
                            onActiveFocusChanged: if (!activeFocus && text.length === 0) wasClicked = false

                            Text {
                                anchors.centerIn: parent
                                text: root.errorMessage !== "" ? root.errorMessage : Eitr.I18n.tr("PASSWORD REQUIRED")
                                font.family: root.sansFont
                                font.pixelSize: 11 * s
                                font.bold: true
                                font.letterSpacing: 1.5 * s
                                color: root.errorMessage !== "" ? root.colors.error : root.colors.mutedText
                                opacity: pwd.text === "" && (!pwd.activeFocus || (!pwd.wasClicked && pwd.text.length === 0)) ? 1 : 0
                                Behavior on opacity { NumberAnimation { duration: 150 } }
                            }

                            // Cursor
                            Rectangle {
                                id: customCursor
                                width: 2 * s
                                height: 18 * s
                                color: root.colors.fieldIcon
                                anchors.verticalCenter: parent.verticalCenter
                                x: pwd.cursorRectangle.x
                                visible: pwd.activeFocus && (pwd.text.length > 0 || pwd.wasClicked) && root.errorMessage === ""

                                SequentialAnimation {
                                    loops: Animation.Infinite
                                    running: customCursor.visible
                                    NumberAnimation { target: customCursor; property: "opacity"; from: 1; to: 0; duration: 400; easing.type: Easing.InOutQuad }
                                    NumberAnimation { target: customCursor; property: "opacity"; from: 0; to: 1; duration: 400; easing.type: Easing.InOutQuad }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.IBeamCursor
                                onClicked: {
                                    pwd.wasClicked = true;
                                    pwd.forceActiveFocus();
                                }
                            }

                            onAccepted: {
                                login.login(pwd.text);
                            }
                        }
                    }

                    // Bottom Row
                    Row {
                        width: parent.width
                        spacing: 12 * s

                        // User Switch
                        Rectangle {
                            width: userText.implicitWidth + 32 * s
                            height: 38 * s
                            radius: 19 * s
                            color: userMouse.pressed ? root.colors.chipButtonPressed : (userMouse.containsMouse ? root.colors.chipButtonHover : root.colors.chipButton)
                            scale: userMouse.pressed ? 0.95 : (userMouse.containsMouse ? 1.02 : 1.0)
                            Behavior on color { ColorAnimation { duration: 150 } }
                            Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutBack } }

                            Text {
                                id: userText
                                anchors.centerIn: parent
                                text: (login.userName || Eitr.I18n.tr("USER")).toUpperCase()
                                font.family: root.sansFont
                                font.pixelSize: 10 * s
                                font.bold: true
                                font.letterSpacing: 1 * s
                                color: root.colors.chipButtonText
                            }

                            MouseArea {
                                id: userMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    login.cycleUser();
                                }
                            }
                        }

                        // Unlock Pill
                        Item {
                            width: parent.width - (userText.implicitWidth + 32 * s) - 12 * s
                            height: 38 * s

                            Rectangle {
                                anchors.right: parent.right
                                width: parent.width
                                height: 38 * s
                                radius: 19 * s
                                color: loginMouse.pressed ? root.colors.buttonPressed : (loginMouse.containsMouse ? root.colors.buttonHover : root.colors.button)
                                scale: loginMouse.pressed ? 0.95 : (loginMouse.containsMouse ? 1.02 : 1.0)
                                Behavior on color { ColorAnimation { duration: 150 } }
                                Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutBack } }

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 6 * s

                                    Text {
                                        text: Eitr.I18n.tr("UNLOCK")
                                        font.family: root.sansFont
                                        font.pixelSize: 10 * s
                                        font.bold: true
                                        font.letterSpacing: 1.5 * s
                                        color: root.colors.onStrong
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text: "➔"
                                        font.family: root.sansFont
                                        font.pixelSize: 11 * s
                                        color: root.colors.onStrong
                                        anchors.verticalCenter: parent.verticalCenter
                                        transform: Translate {
                                            x: loginMouse.containsMouse ? 3 * s : 0
                                            Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutQuad } }
                                        }
                                    }
                                }

                                MouseArea {
                                    id: loginMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: pwd.accepted()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
