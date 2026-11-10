import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The card of the administrator password prompt (PolkitPrompt owns the agent and window).
// `flow` is Quickshell's AuthFlow: the typed answer goes straight to flow.submit() and the
// field is cleared at once; nothing from the request is shown as markup or run.
FocusScope {
    id: dialog
    required property var flow
    required property color foreground
    required property color background
    required property color accent
    property bool detailsShown: false
    readonly property bool waiting: !!flow && !flow.isResponseRequired && !flow.isCompleted
    // AuthFlow lists the identities polkit accepts; with several, the user picks one.
    readonly property var identities: {
        const listed = flow && flow.identities ? flow.identities : [];
        const result = [];
        for (let index = 0; index < listed.length; index++) result.push(listed[index]);
        return result;
    }
    readonly property var selectedIdentity: flow ? flow.selectedIdentity : null
    readonly property bool lightSurface: PanelStyle.luminance(background) > 0.5
    readonly property color errorInk: lightSurface ? "#b3261e" : "#ff8a80"
    readonly property string errorText: !flow ? ""
        : flow.supplementaryIsError && flow.supplementaryMessage !== "" ? flow.supplementaryMessage
        : flow.failed ? Eitr.I18n.tr("That password was not accepted. Try again.") : ""
    readonly property string infoText: flow && !flow.supplementaryIsError ? flow.supplementaryMessage : ""
    implicitWidth: 400
    implicitHeight: layout.implicitHeight + 2 * PanelStyle.padding
    width: implicitWidth
    height: implicitHeight

    function identityName(identity) {
        if (!identity) return "";
        return identity.displayName || "";
    }
    // PAM asks "Password: " in English; that prompt reads as the translated "Password".
    function promptText() {
        const prompt = flow ? String(flow.inputPrompt || "").trim().replace(/:$/, "") : "";
        return prompt === "" || /^password$/i.test(prompt) ? Eitr.I18n.tr("Password") : prompt;
    }
    function submit() {
        if (!flow || !flow.isResponseRequired || password.text.length === 0) return;
        const answer = password.text;
        password.clear();
        flow.submit(answer);
    }
    function cancel() {
        password.clear();
        if (flow && !flow.isCompleted) flow.cancelAuthenticationRequest();
    }
    function reset() {
        password.clear();
        detailsShown = false;
    }
    function focusPassword() { password.forceActiveFocus(); }

    onFlowChanged: reset()
    onWaitingChanged: if (!waiting) focusPassword()
    Component.onDestruction: password.clear()
    Keys.onEscapePressed: cancel()

    Rectangle {
        anchors.fill: parent
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        color: dialog.background
        border.width: 1
        border.color: Qt.alpha(dialog.foreground, 0.15)
    }
    Column {
        id: layout
        x: PanelStyle.padding; y: PanelStyle.padding
        width: parent.width - 2 * PanelStyle.padding
        spacing: 14
        Row {
            width: parent.width
            spacing: 14
            Rectangle {
                id: badge
                width: 40; height: 40
                radius: DesktopStyle.radius(PanelStyle.controlRadius * 2)
                color: Qt.alpha(dialog.accent, 0.18)
                Text {
                    anchors.centerIn: parent
                    text: "󰌾"
                    color: dialog.accent
                    font.family: PanelStyle.fontFamily
                    font.pixelSize: 20
                }
            }
            Column {
                width: parent.width - badge.width - parent.spacing
                spacing: 4
                Text {
                    objectName: "polkitTitle"
                    width: parent.width
                    text: Eitr.I18n.tr("Authentication required")
                    textFormat: Text.PlainText
                    wrapMode: Text.Wrap
                    color: dialog.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.headingSize
                }
                Text {
                    objectName: "polkitMessage"
                    width: parent.width
                    text: dialog.flow ? dialog.flow.message : ""
                    textFormat: Text.PlainText
                    wrapMode: Text.Wrap
                    color: dialog.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
            }
        }
        Text {
            objectName: "polkitIdentity"
            visible: dialog.identities.length <= 1
            width: parent.width
            text: Eitr.I18n.tr("Authenticating as {user}", {user: dialog.identityName(dialog.selectedIdentity)})
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: dialog.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
        ChoiceDropdown {
            objectName: "polkitIdentityChoice"
            visible: dialog.identities.length > 1
            width: parent.width
            foreground: dialog.foreground
            background: dialog.background
            gold: dialog.accent
            label: Eitr.I18n.tr("Authenticate as")
            accessibleName: Eitr.I18n.tr("Authenticate as")
            available: !dialog.waiting
            choices: dialog.identities.map((identity, index) => ({value: String(index), label: dialog.identityName(identity)}))
            current: String(dialog.identities.indexOf(dialog.selectedIdentity))
            onChosen: value => {
                dialog.reset();
                dialog.flow.selectedIdentity = dialog.identities[Number(value)];
                dialog.focusPassword();
            }
        }
        PanelTextField {
            id: password
            objectName: "polkitPassword"
            width: parent.width
            height: 36
            foreground: dialog.foreground
            accent: dialog.accent
            enabled: !dialog.waiting
            echoMode: dialog.flow && dialog.flow.responseVisible ? TextInput.Normal : TextInput.Password
            inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText | Qt.ImhNoAutoUppercase
            placeholderText: dialog.promptText()
            focus: true
            onAccepted: dialog.submit()
        }
        Text {
            objectName: "polkitError"
            visible: text !== ""
            width: parent.width
            text: dialog.errorText !== "" ? dialog.errorText : dialog.infoText
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: dialog.errorText !== "" ? dialog.errorInk : dialog.foreground
            font.family: DesktopFonts.family
            font.pixelSize: PanelStyle.captionSize
        }
        Column {
            width: parent.width
            spacing: 6
            visible: dialog.flow && dialog.flow.actionId !== ""
            PanelButton {
                objectName: "polkitDetailsToggle"
                width: 210; height: 28
                flat: true
                textAlignment: Text.AlignLeft
                textSize: PanelStyle.captionSize
                leadingIcon: dialog.detailsShown ? "󰅀" : "󰅂"
                text: Eitr.I18n.tr("Request details")
                foreground: dialog.foreground
                onClicked: dialog.detailsShown = !dialog.detailsShown
            }
            Rectangle {
                visible: dialog.detailsShown
                width: parent.width
                height: details.implicitHeight + 16
                radius: DesktopStyle.radius(PanelStyle.controlRadius)
                color: Qt.alpha(dialog.foreground, 0.06)
                Column {
                    id: details
                    x: 10; y: 8
                    width: parent.width - 20
                    spacing: 2
                    Text {
                        text: Eitr.I18n.tr("Action")
                        textFormat: Text.PlainText
                        color: dialog.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                    TextEdit {
                        objectName: "polkitActionId"
                        width: parent.width
                        text: dialog.flow ? dialog.flow.actionId : ""
                        textFormat: TextEdit.PlainText
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.WrapAnywhere
                        color: dialog.foreground
                        selectionColor: Qt.alpha(dialog.accent, 0.35)
                        selectedTextColor: dialog.foreground
                        font.family: PanelStyle.fontFamily
                        font.pixelSize: PanelStyle.captionSize
                        activeFocusOnTab: false
                    }
                }
            }
        }
        Row {
            anchors.right: parent.right
            spacing: 8
            PanelButton {
                objectName: "polkitCancel"
                width: 100
                outlined: true
                text: Eitr.I18n.tr("Cancel")
                foreground: dialog.foreground
                onClicked: dialog.cancel()
            }
            PanelButton {
                objectName: "polkitAuthenticate"
                width: 130
                text: Eitr.I18n.tr("Authenticate")
                foreground: dialog.foreground
                loading: dialog.waiting
                available: !!dialog.flow && dialog.flow.isResponseRequired && password.text.length > 0
                onClicked: dialog.submit()
            }
        }
    }
}
