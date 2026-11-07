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
        id: method
        visible: form.enterprise
        width: Math.min(320, parent.width)
        foreground: form.foreground; background: form.background; gold: SettingsInk.gold
        choices: [{value: "peap", label: "PEAP / MSCHAPv2"}, {value: "ttls", label: "TTLS / PAP"}]
        current: "peap"
        onChosen: value => current = value
    }
    TextField { id: identity; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Username"); color: form.foreground }
    TextField { id: anonymous; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Anonymous identity (optional)"); color: form.foreground }
    TextField { id: domain; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Server domain"); color: form.foreground }
    TextField { id: certificate; visible: form.enterprise; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("CA certificate path"); color: form.foreground }
    TextField { id: password; width: Math.min(320, parent.width); placeholderText: Eitr.I18n.tr("Password"); color: form.foreground; echoMode: TextInput.Password; Accessible.name: placeholderText }
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
