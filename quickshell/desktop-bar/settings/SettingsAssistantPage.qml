import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// AI Assistant, in three tabs: General (the default assistant, Assistant Access and
// collaboration from Walker's AI menus), Assistants (each assistant's own actions) and Usage
// (the accounts the AI Usage panel tracks).
Column {
    id: pageBody
    required property var context
    readonly property var view: context
    readonly property var helper: context.helper
    readonly property string tab: view.tab || "general"
    readonly property var usage: (DesktopData.topics["ai.usage"] || {}).data || ({providers: []})
    readonly property var usageAccounts: (usage.providers || []).reduce((rows, provider) =>
        rows.concat((provider.accounts || []).map(account => Object.assign({provider: provider.name}, account))), [])
    width: parent ? parent.width : 0
    spacing: 12
    function demand() {
        DesktopData.releaseOwner(pageBody);
        if (view.active && view.live) DesktopData.observe("ai.usage", pageBody);
    }
    function limits(account) {
        return (account.windows || []).map(limit => (limit.label === "5h window" ? Eitr.I18n.tr("Session") : limit.label)
            + " " + Math.round(Math.max(0, Math.min(100, Number(limit.used)))) + "%").join("  ·  ");
    }
    Component.onCompleted: demand()
    Component.onDestruction: DesktopData.releaseOwner(pageBody)
    Connections { target: pageBody.view; function onActiveChanged() { pageBody.demand(); } }
    PreferenceWatch { path: pageBody.view.live && pageBody.view.active ? Eitr.Paths.config("eitr/ai.json") : ""; onChanged: pageBody.helper.refresh() }
    TabStrip { foreground: SettingsPalette.foreground; gold: SettingsPalette.gold; carved: true;
        width: parent.width
        height: 42
        choices: [{id: "general", label: Eitr.I18n.tr("General")}, {id: "assistants", label: Eitr.I18n.tr("Assistants")}, {id: "usage", label: Eitr.I18n.tr("Usage")}]
        current: pageBody.tab
        onChosen: value => { pageBody.view.tabRequested(value); pageBody.view.contentY = 0; }
    }
    Flow {
        visible: pageBody.tab === "usage"
        width: parent.width
        spacing: 8
        PanelButton {
            width: 100; text: Eitr.I18n.tr("Refresh"); foreground: pageBody.view.foreground
            onClicked: if (pageBody.view.live) { pageBody.helper.refresh(); DesktopData.refresh("ai.usage"); }
        }
        PanelButton {
            SettingsTarget { objectName: "setting-assistant-open-ai-usage" }
            width: 150; text: Eitr.I18n.tr("Open AI Usage"); foreground: pageBody.view.foreground
            onClicked: if (pageBody.view.live) Quickshell.execDetached(["eitr-shell", "desktop-bar", "ipc", "call", "--", "panels", "show", "ai"])
        }
    }
    ControlCard {
        title: Eitr.I18n.tr("Preferences")
        visible: pageBody.tab === "general"
        foreground: pageBody.view.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-assistant-default-assistant" }
            floatingLabel: Eitr.I18n.tr("Default Assistant")
            helperText: Eitr.I18n.tr("Open with the assistant shortcut")
            width: Math.min(parent.width, 460)
            objectName: "settings-default-assistant"
            foreground: pageBody.view.foreground; background: pageBody.view.background; gold: SettingsInk.gold
            accessibleName: Eitr.I18n.tr("Default Assistant")
            placeholder: (pageBody.helper.summary.choices || []).length ? Eitr.I18n.tr("Choose an installed assistant.") : Eitr.I18n.tr("Install an AI Assistant")
            choices: pageBody.helper.summary.choices || []
            current: pageBody.helper.summary.current || ""
            available: !pageBody.helper.busy && (pageBody.helper.summary.choices || []).length > 0
            onChosen: value => pageBody.helper.change(["default-assistant", "assistants", value])
        }
        ChoiceDropdown {
            SettingsTarget { objectName: "setting-assistant-assistant-access" }
            floatingLabel: Eitr.I18n.tr("Assistant Access")
            helperText: Eitr.I18n.tr("Full access skips the assistant's permission prompts; Ask keeps them.")
            width: Math.min(parent.width, 460)
            objectName: "settings-assistant-access"
            foreground: pageBody.view.foreground; background: pageBody.view.background; gold: SettingsInk.gold
            accessibleName: Eitr.I18n.tr("Assistant Access")
            choices: [{value: "full", label: Eitr.I18n.tr("Full access (default)")}, {value: "ask", label: Eitr.I18n.tr("Ask before changes")}]
            current: pageBody.helper.summary.access || "full"
            available: !pageBody.helper.busy
            onChosen: value => pageBody.helper.change(["access", "assistants", value])
        }
        ToggleRow {
            SettingsTarget { objectName: "setting-assistant-let-assistants-work-together" }
            text: Eitr.I18n.tr("Let assistants work together")
            description: Eitr.I18n.tr("Read-only help from your connected assistants. Turning it on explains what is shared and asks first.")
            foreground: pageBody.view.foreground; accent: pageBody.view.accent
            checked: !!pageBody.helper.summary.collaboration
            available: !pageBody.helper.busy
            onToggled: checked => { if (checked !== !!pageBody.helper.summary.collaboration) pageBody.helper.change(["collaboration", "assistants"]); }
        }
    }
    ControlCard {
        title: Eitr.I18n.tr("AI Usage")
        visible: pageBody.tab === "usage"
        foreground: pageBody.view.foreground
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        Repeater {
            model: pageBody.usageAccounts
            ControlRow {
                required property var modelData
                text: modelData.provider + (modelData.id && modelData.id !== "default" ? " · " + modelData.label : "")
                description: modelData.plan || ""
                foreground: pageBody.view.foreground
                controlWidth: Math.min(360, width * 0.5)
                SettingsText {
                    anchors.right: parent.right
                    width: parent.width
                    horizontalAlignment: Text.AlignRight
                    text: pageBody.limits(modelData) || Eitr.I18n.tr("Unavailable")
                    font.pixelSize: PanelStyle.captionSize
                    font.features: PanelStyle.tabularFigures
                }
            }
        }
        SettingsText {
            visible: !pageBody.usageAccounts.length
            text: Eitr.I18n.tr("No readable AI usage available. Sign in to Claude Code, Codex, or Grok, or try refreshing later.")
            opacity: PanelStyle.secondaryTextOpacity
        }
    }
    SettingsSummaryCards { context: pageBody.context; visible: pageBody.tab === "assistants" }
}
