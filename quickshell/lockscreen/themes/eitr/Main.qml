import Eitr as Eitr
import QtQuick
import LockscreenComponents
import "Spectrum.js" as Spectrum

Item {
    id: root
    readonly property var auth: typeof sddm !== "undefined" ? sddm : null
    readonly property var users: typeof userModel !== "undefined" ? userModel : null
    readonly property var sessions: typeof sessionModel !== "undefined" ? sessionModel : null
    readonly property var settings: config
    readonly property real unit: Math.min(width / 1080, height / 1080, 1.5)
    readonly property bool light: settings.themeMode === "light"
    // Pure black on dark themes: the aurora and runes glow over it, and OLED pixels stay off.
    readonly property color ground: light ? (settings.backgroundColor || "#f2ecdf") : "#000000"
    readonly property color ink: settings.foreground || (light ? "#292521" : "#f2ecdf")
    readonly property color accent: settings.accent || "#a3bd79"
    readonly property color muted: settings.muted || (light ? "#625b53" : "#a99b90")
    readonly property bool motion: visible && settings.reduceMotion !== true && sweepProgress < 0
    readonly property var spectrum: Spectrum.colors(light)
    // The wordmark is filled with the current theme's accent, still.
    readonly property var wordmarkFill: [accent, accent, accent, accent, accent, accent, accent]
    // A green northern-lights sky on every theme: the wallpaper's lime and green at
    // the foot, rising through teal to a little violet instead of magenta.
    readonly property var sky: ["#c2ee5a", "#3fe39a", "#2fd6b0", "#6f7fe0"]
    property date now: new Date()
    property real elapsed: 0
    property real ringAngle: 0
    Component.onCompleted: ringAngle = now.getSeconds() * 6
    property real sweepProgress: -1
    signal captureRequested()
    signal previewFinished()
    function dismissPreview() {
        if (settings.reduceMotion === true) { previewFinished(); return; }
        sweepProgress = 0;
        previewSweep.start();
    }
    function submit() {
        if (typeof isLockPreview !== "undefined" && isLockPreview) { dismissPreview(); return; }
        const value = password.text;
        password.text = "";
        feedback.text = "";
        try { captureRequested(); } finally { login.login(value); }
    }
    NumberAnimation { id: previewSweep; target: root; property: "sweepProgress"; to: 1; duration: 820; onFinished: root.previewFinished() }
    // The live wallpaper's pace: smooth curtains and twinkling.
    Timer { interval: 50; running: root.motion; repeat: true; onTriggered: root.elapsed += interval / 1000 }
    Timer {
        interval: 1000; running: root.visible; repeat: true
        onTriggered: {
            root.now = new Date();
            const advance = (root.now.getSeconds() - Math.round(root.ringAngle / 6) % 60 + 60) % 60;
            root.ringAngle += advance * 6;
        }
    }
    onActiveFocusChanged: if (activeFocus) password.forceActiveFocus()
    LoginController {
        id: login
        sddm: root.auth; userModel: root.users; sessionModel: root.sessions
        onLoginFailed: { feedback.text = Eitr.I18n.tr("Unable to unlock. Try again."); password.text = ""; password.forceActiveFocus(); }
        onLoginSucceeded: { password.text = ""; feedback.text = ""; }
    }
    // The lockscreen itself; while the Bifröst opens, the two halves below show it.
    Item {
        id: scene
        width: root.width; height: root.height
        Item {
            width: root.width; height: root.height
            Rectangle { anchors.fill: parent; color: root.ground }
            Stars {
                anchors.fill: parent
                visible: !root.light
                time: root.elapsed
                twinkle: root.settings.reduceMotion !== true
            }
            Aurora {
                objectName: "eitrAurora"
                anchors.fill: parent
                // Twice the wallpaper's drift: the lockscreen's sky is the whole picture.
                time: root.elapsed * 2
                light: root.light
                palette: root.sky
            }
            Column {
                anchors.centerIn: parent
                width: Math.min(root.width * 0.82, 480 * root.unit)
                spacing: 30 * root.unit
                Item {
                    width: 410 * root.unit; height: width
                    anchors.horizontalCenter: parent.horizontalCenter
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width * 0.97; height: width; radius: width / 2
                        color: Qt.alpha(root.ground, root.light ? 0.55 : 0.42)
                    }
                    // The boot splash's ring (distro/plymouth/eitr/export.py): the 24 Elder
                    // Futhark runes in Noto Sans Runic and runestone gold with a soft glow,
                    // drawn as text so they stay sharp at every angle. It ticks once a second.
                    RuneRing {
                        anchors.fill: parent
                        gold: root.light ? "#8a6431" : "#c4914f"
                        glow: !root.light
                        rotation: root.ringAngle
                        Behavior on rotation { NumberAnimation { duration: root.settings.reduceMotion === true ? 0 : 160; easing.type: Easing.OutCubic } }
                    }
                    Brand {
                        anchors.centerIn: parent
                        width: parent.width * 0.65; height: width * 310.36 / 710.41
                        artwork: Qt.resolvedUrl("wordmark.svg")
                        spectrum: root.wordmarkFill
                    }
                }
        NorseClock {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDateTime(root.now, root.settings.clock === "12h" ? "h:mm AP" : "HH:mm")
            color: root.ink
            glyphHeight: 62 * root.unit
        }
        Rectangle {
            id: field
            width: parent.width; height: 60 * root.unit; radius: 5 * root.unit
            color: Qt.alpha(root.ink, 0.045); border.color: password.activeFocus ? root.accent : root.muted
            // Each carved rune jolts the field and flares its border.
            property real jolt: 0
            transform: Translate { x: field.jolt * 5 * root.unit; y: Math.abs(field.jolt) * 2 * root.unit }
            Rectangle {
                id: flare
                anchors.fill: parent; radius: parent.radius
                color: "transparent"; border.width: 2 * root.unit
                border.color: root.light ? "#8a6431" : "#ffcf7a"; opacity: 0
            }
            SequentialAnimation {
                id: joltAnimation
                ParallelAnimation {
                    NumberAnimation { target: flare; property: "opacity"; from: 0.9; to: 0; duration: 320; easing.type: Easing.OutQuad }
                    SequentialAnimation {
                        NumberAnimation { target: field; property: "jolt"; to: 1; duration: 35 }
                        NumberAnimation { target: field; property: "jolt"; to: -0.7; duration: 45 }
                        NumberAnimation { target: field; property: "jolt"; to: 0.35; duration: 45 }
                        NumberAnimation { target: field; property: "jolt"; to: 0; duration: 60; easing.type: Easing.OutQuad }
                    }
                }
            }
            TextInput {
                id: password
                objectName: "eitrPassword"
                anchors.fill: parent; anchors.leftMargin: 18 * root.unit; anchors.rightMargin: 55 * root.unit
                verticalAlignment: TextInput.AlignVCenter; echoMode: TextInput.Password
                // The typed characters stay hidden; CarvedRunes shows one rune per character instead.
                font.pixelSize: 18 * root.unit; color: "transparent"; selectionColor: "transparent"
                selectedTextColor: "transparent"; cursorDelegate: Item {}
                focus: true; selectByMouse: false
                // No selection: every edit is a plain insert or delete at the caret.
                onSelectedTextChanged: if (selectedText.length) deselect()
                onAccepted: root.submit()
            }
            CarvedRunes {
                anchors.fill: password
                input: password
                gold: root.light ? "#8a6431" : "#c4914f"
                caret: password.activeFocus ? root.accent : "transparent"
                size: 23 * root.unit
                animated: root.settings.reduceMotion !== true
                onStruck: joltAnimation.restart()
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 18 * root.unit; anchors.verticalCenter: parent.verticalCenter
                text: "→"; font.pixelSize: 25 * root.unit; color: root.accent
                MouseArea { anchors.fill: parent; anchors.margins: -10 * root.unit; cursorShape: Qt.PointingHandCursor; onClicked: root.submit() }
            }
        }
        Text {
            id: feedback
            objectName: "eitrFeedback"
            width: parent.width; height: 36 * root.unit; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
            color: root.settings.alert || root.accent; font.pixelSize: 14 * root.unit
        }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter; spacing: 20 * root.unit
            visible: !login.isQuickshell
            Text { text: login.userName; color: root.muted; MouseArea { anchors.fill: parent; onClicked: login.cycleUser() } }
            Text { text: login.sessionName; color: root.muted; MouseArea { anchors.fill: parent; onClicked: login.cycleSession() } }
        }
            }
        }
    }
    ShaderEffectSource {
        visible: root.sweepProgress >= 0
        width: sweep.leftEdge; height: root.height
        sourceItem: scene; hideSource: root.sweepProgress >= 0
        sourceRect: Qt.rect(0, 0, width, height)
    }
    ShaderEffectSource {
        visible: root.sweepProgress >= 0
        x: sweep.rightEdge; width: root.width - x; height: root.height
        sourceItem: scene; hideSource: root.sweepProgress >= 0
        sourceRect: Qt.rect(x, 0, width, height)
    }
    ShaderEffectSource {
        id: sceneTexture
        visible: false
        sourceItem: scene; hideSource: root.sweepProgress >= 0
    }
    Sweep {
        id: sweep; anchors.fill: parent; progress: Math.max(0, root.sweepProgress)
        spectrum: root.spectrum; style: root.settings.unlockEffect || "bifrost"; source: sceneTexture
        visible: root.sweepProgress >= 0
    }
}
