import ".."
import QtQuick
import Eitr as Eitr

// Git & Cloud: a toolbar for the setup flows, then one card per provider.
Column {
    id: pageBody
    required property var context
    readonly property var view: context
    readonly property var helper: context.helper
    readonly property var cloudProviders: ["aws", "gcp", "azure"]
    width: parent ? parent.width : 0
    spacing: 12
    function addCloudAccount(provider) {
        if (cloudProviders.includes(provider)) view.terminal("walker/scripts/menus/cloud/accounts.py", ["add", provider]);
        else view.terminal("walker/scripts/menus/cloud/providers.py", [provider, "add"]);
    }
    Flow {
        objectName: "settings-git-cloud-toolbar"
        width: parent.width
        spacing: 8
        PanelButton { width: 100; foreground: pageBody.view.foreground; text: Eitr.I18n.tr("Refresh"); onClicked: if (pageBody.view.live) pageBody.helper.refresh() }
        PanelButton { width: 130; foreground: pageBody.view.foreground; text: Eitr.I18n.tr("Git Accounts"); onClicked: pageBody.view.terminal("walker/scripts/actions/development/git-accounts.py", ["add"]) }
        PanelButton { width: 190; foreground: pageBody.view.foreground; text: Eitr.I18n.tr("Import Existing Setup"); onClicked: pageBody.view.terminal("walker/scripts/actions/development/git-accounts.py", ["import"]) }
        ChoiceDropdown {
            id: cloudProvider
            width: 160
            foreground: pageBody.view.foreground; background: pageBody.view.background; gold: SettingsInk.gold
            accessibleName: Eitr.I18n.tr("Cloud provider")
            choices: pageBody.helper.summary.providers || []
            current: "aws"
            onChosen: value => current = value
        }
        PanelButton { width: 140; foreground: pageBody.view.foreground; text: Eitr.I18n.tr("Add Account…"); onClicked: pageBody.addCloudAccount(cloudProvider.current) }
    }
    SettingsSummaryCards { context: pageBody.context }
}
