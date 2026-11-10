import ".."
import QtQuick
import QtQuick.Controls.Basic
import Eitr as Eitr

ControlCard {
    id: form
    required property color background
    required property color accent
    property var network: null
    property bool busy: false
    readonly property bool enterprise: network && network.type === "8021x"
    signal submitted(var input)
    signal cancelled()
    title: network ? network.name : ""
    surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
    onNetworkChanged: { password.text = ""; identity.text = ""; anonymous.text = ""; domain.text = ""; certificate.text = ""; }
    SettingsText { visible: form.network && form.network.type === "unsupported"; text: Eitr.I18n.tr("This network needs advanced security configuration.") }
    ChoiceDropdown {
        floatingLabel: Eitr.I18n.tr("Authentication")
        helperText: Eitr.I18n.tr("Use the method required by your network.")
        width: Math.min(parent.width, 460)
        id: method
        visible: form.enterprise
        foreground: form.foreground; background: form.background; gold: SettingsInk.gold
        choices: [{value: "peap", label: "PEAP / MSCHAPv2"}, {value: "ttls", label: "TTLS / PAP"}]
        current: "peap"
        onChosen: value => current = value
    }
    PanelTextField { id: identity; foreground: form.foreground; accent: form.accent; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Username") }
    PanelTextField { id: anonymous; foreground: form.foreground; accent: form.accent; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Anonymous identity (optional)") }
    PanelTextField { id: domain; foreground: form.foreground; accent: form.accent; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Server domain") }
    PanelTextField { id: certificate; foreground: form.foreground; accent: form.accent; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("CA certificate path") }
    PanelTextField { id: password; foreground: form.foreground; accent: form.accent; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Password"); echoMode: TextInput.Password; Accessible.name: placeholderText }
    Row {
        spacing: 8
        PanelButton { width: 100; text: Eitr.I18n.tr("Cancel"); foreground: form.foreground; onClicked: form.cancelled() }
        PanelButton {
            width: 100; text: Eitr.I18n.tr("Connect"); foreground: form.foreground
            available: !form.busy && password.text !== "" && (!form.enterprise || identity.text !== "" && domain.text !== "" && certificate.text !== "") && (!form.network || form.network.type !== "unsupported")
            onClicked: form.submitted({password: password.text, identity: identity.text, name: form.network ? form.network.name : "", anonymous: anonymous.text, domain: domain.text, ca: certificate.text, eap: method.current})
        }
    }
}
