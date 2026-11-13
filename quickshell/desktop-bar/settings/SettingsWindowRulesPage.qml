import ".."
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    id: pageBody
    objectName: "editor-windowrules"
    property alias editorHelper: editor
    required property var context
    readonly property var view: context
    property int editing: -1
    property int removing: -1
    property bool formOpen: false
    property string appClass: ""
    property string appTitle: ""
    property bool otherApp: false
    property string sizeUnit: "px"
    readonly property int sizeLimit: sizeUnit === "%" ? 100 : 32768
    readonly property string sizeError: !sizing.checked ? "" : !(/^[1-9][0-9]*$/.test(ruleWidth.text) && /^[1-9][0-9]*$/.test(ruleHeight.text)) ? Eitr.I18n.tr("Enter a positive width and height.") : Number(ruleWidth.text) > sizeLimit || Number(ruleHeight.text) > sizeLimit ? Eitr.I18n.tr("Size must be between 1 and %1.").arg(sizeLimit) : ""
    readonly property var appChoices: editor.summary.apps.slice().sort((first, second) => Number(Boolean(second.title)) - Number(Boolean(first.title))).map(app => ({value: app.class, label: app.name + " · " + app.class})).concat([{value: "__other__", label: Eitr.I18n.tr("Other app…")}])
    width: parent ? parent.width : 0
    spacing: 12
    function edit(index) {
        const rule = index < 0 ? {} : editor.summary.rules[index];
        editing = index; appClass = rule.class || ""; appTitle = rule.title || "";
        floating.checked = rule.float === true;
        otherApp = appClass !== "" && !editor.summary.apps.some(app => app.class === appClass);
        titleMatch.checked = Boolean(appTitle);
        workspace.current = /^(10|[1-9])$/.test(rule.workspace || "") ? rule.workspace : "";
        const dimensions = (rule.size || "").split(" ");
        sizing.checked = Boolean(rule.size); sizeUnit = (rule.size || "").includes("%") ? "%" : "px";
        ruleWidth.text = (dimensions[0] || "").replace("%", ""); ruleHeight.text = (dimensions[1] || "").replace("%", "");
        opacity.value = Math.round((rule.opacity === undefined ? 1 : rule.opacity) * 100);
        formOpen = true;
    }
    function ruleDescription(rule) {
        const details = [];
        if (rule.float) details.push(Eitr.I18n.tr("Floating"));
        if (rule.size) details.push(rule.size.replace(" ", "×"));
        if (rule.workspace) details.push(Eitr.I18n.tr("Workspace %1").arg(rule.workspace));
        if (rule.opacity !== undefined && rule.opacity < 1) details.push(Eitr.I18n.tr("Opacity %1").arg(Math.round(rule.opacity * 100) + " %"));
        return details.join(" · ");
    }
    SettingsHelper {
        id: editor
        active: view.active && view.page === "window-rules"
        live: view.live
        script: Eitr.Paths.code("quickshell/desktop-bar/scripts/window-rules.py")
        schema: ({rules: "array", apps: "array"})
        summary: ({rules: [], apps: []})
    }
    PanelButton {
        SettingsTarget { objectName: "setting-window-rules-add" }
        width: 160; foreground: view.foreground; text: Eitr.I18n.tr("Add rule")
        onClicked: pageBody.edit(-1)
    }
    SettingsText { visible: editor.error !== ""; text: editor.error }
    Column {
        width: parent.width; spacing: PanelStyle.selectionRowGap
        Repeater {
            model: editor.summary.rules
            Rectangle {
                id: ruleCard
                required property var modelData
                required property int index
                readonly property var app: editor.summary.apps.find(candidate => candidate.class === modelData.class) || ({})
                width: parent.width; height: pageBody.ruleDescription(modelData) ? 44 : 36; radius: DesktopStyle.radius(4)
                color: Qt.alpha(view.foreground, PanelStyle.selectionAlpha(false, false))
                border.color: Qt.alpha(view.foreground, PanelStyle.selectionBorderAlpha)
                Image { x: 10; anchors.verticalCenter: parent.verticalCenter; width: 18; height: 18; source: ruleCard.app.icon ? Quickshell.iconPath(ruleCard.app.icon, true) : "" }
                Column {
                    x: 36; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 104; spacing: 2
                    Text { width: parent.width; text: ruleCard.app.name || ruleCard.modelData.class; color: view.foreground; font.family: DesktopFonts.family; font.pixelSize: 13; elide: Text.ElideRight }
                    Text { width: parent.width; text: pageBody.ruleDescription(ruleCard.modelData); color: Qt.alpha(view.foreground, PanelStyle.secondaryTextOpacity); font.family: DesktopFonts.family; font.pixelSize: 11; elide: Text.ElideRight }
                }
                Row {
                    anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter; spacing: 6
                    PanelButton { id: editButton; width: 24; height: 24; icon: true; iconSize: 14; foreground: view.foreground; text: "\uf040"; Accessible.name: Eitr.I18n.tr("Edit"); onClicked: pageBody.edit(ruleCard.index)
                        HoverHandler { id: editHover }
                        BarTooltip { target: editButton; hovered: editHover.hovered; text: Eitr.I18n.tr("Edit"); foreground: view.foreground; background: view.background }
                    }
                    PanelButton { id: deleteButton; width: 24; height: 24; icon: true; iconSize: 14; foreground: view.foreground; text: "\uf1f8"; Accessible.name: Eitr.I18n.tr("Remove"); onClicked: { pageBody.removing = ruleCard.index; removeSheet.open(); }
                        HoverHandler { id: deleteHover }
                        BarTooltip { target: deleteButton; hovered: deleteHover.hovered; text: Eitr.I18n.tr("Remove"); foreground: view.foreground; background: view.background }
                    }
                }
            }
        }
    }
    ControlCard {
        visible: pageBody.formOpen
        title: pageBody.editing < 0 ? Eitr.I18n.tr("Add rule") : Eitr.I18n.tr("Edit rule")
        foreground: view.foreground
        ControlRow {
            text: Eitr.I18n.tr("App"); description: Eitr.I18n.tr("The app this rule applies to.")
            foreground: view.foreground
            ChoiceDropdown {
                width: parent.width; foreground: view.foreground; background: view.background; gold: view.accent
                choices: pageBody.appChoices
                current: pageBody.otherApp ? "__other__" : pageBody.appClass
                placeholder: Eitr.I18n.tr("Choose an app")
                onChosen: value => { pageBody.otherApp = value === "__other__"; pageBody.appClass = pageBody.otherApp ? "" : value; }
            }
        }
        PanelTextField { visible: pageBody.otherApp; width: Math.min(320, parent.width); foreground: view.foreground; accent: view.accent; placeholderText: Eitr.I18n.tr("App class"); text: pageBody.appClass; onTextEdited: pageBody.appClass = text }
        ToggleRow { id: titleMatch; description: Eitr.I18n.tr("Window title (optional, exact match)"); text: Eitr.I18n.tr("Match a window title"); foreground: view.foreground; accent: view.accent; onToggled: value => titleMatch.checked = value }
        PanelTextField { visible: titleMatch.checked; width: parent.width; foreground: view.foreground; accent: view.accent; placeholderText: Eitr.I18n.tr("Window title (optional, exact match)"); text: pageBody.appTitle; onTextEdited: pageBody.appTitle = text }
        ToggleRow {
            id: floating; text: Eitr.I18n.tr("Always float"); description: Eitr.I18n.tr("Open this app's windows floating.")
            foreground: view.foreground; accent: view.accent; onToggled: value => floating.checked = value
        }
        ControlRow {
            text: Eitr.I18n.tr("Workspace"); description: Eitr.I18n.tr("Where this app's windows open.")
            foreground: view.foreground
            ChoiceDropdown {
                id: workspace; width: parent.width; foreground: view.foreground; background: view.background; gold: view.accent
                current: ""
                choices: [{value: "", label: Eitr.I18n.tr("Any workspace")}].concat(Array.from({length: 10}, (unused, index) => ({value: String(index + 1), label: String(index + 1)})))
                onChosen: value => current = value
            }
        }
        ToggleRow { id: sizing; description: Eitr.I18n.tr("Width") + " × " + Eitr.I18n.tr("Height"); text: Eitr.I18n.tr("Set a size"); foreground: view.foreground; accent: view.accent; onToggled: value => sizing.checked = value }
        Row {
            visible: sizing.checked; width: parent.width; spacing: 12
            Column { width: Math.min(150, (parent.width - 124) / 2); spacing: 4
                SettingsText { text: Eitr.I18n.tr("Width") }
                PanelTextField { id: ruleWidth; width: parent.width; foreground: view.foreground; accent: view.accent; validator: IntValidator { bottom: 1 } inputMethodHints: Qt.ImhDigitsOnly }
            }
            Column { width: Math.min(150, (parent.width - 124) / 2); spacing: 4
                SettingsText { text: Eitr.I18n.tr("Height") }
                PanelTextField { id: ruleHeight; width: parent.width; foreground: view.foreground; accent: view.accent; validator: IntValidator { bottom: 1 } inputMethodHints: Qt.ImhDigitsOnly }
            }
            ChoiceSegmented { width: 100; anchors.bottom: parent.bottom; foreground: view.foreground; gold: view.accent; choices: ["px", "%"]; current: pageBody.sizeUnit; onChosen: value => pageBody.sizeUnit = value }
        }
        SettingsText { visible: pageBody.sizeError !== ""; text: pageBody.sizeError }
        ControlRow {
            text: Eitr.I18n.tr("Opacity"); description: Eitr.I18n.tr("At 100 % the windows stay as they are.")
            foreground: view.foreground
            Row {
                width: parent.width; spacing: 8
                PanelSlider { id: opacity; width: parent.width - 56; from: 20; to: 100; stepSize: 1; value: 100; foreground: view.foreground; accent: view.accent }
                SettingsText { width: 48; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: Math.round(opacity.value) + " %" }
            }
        }
        Row {
            anchors.right: parent.right; spacing: 8
            PanelButton { width: 110; foreground: view.foreground; text: Eitr.I18n.tr("Cancel"); onClicked: pageBody.formOpen = false }
            PanelButton {
                width: 110; foreground: view.foreground; selected: true; text: Eitr.I18n.tr("Save")
                enabled: !editor.busy && pageBody.appClass.trim() !== "" && pageBody.sizeError === ""
                onClicked: {
                    const suffix = pageBody.sizeUnit === "%" ? "%" : "";
                    const rule = {class: pageBody.appClass, float: floating.checked, workspace: workspace.current, size: sizing.checked ? ruleWidth.text + suffix + " " + ruleHeight.text + suffix : ""};
                    if (opacity.value < 100) rule.opacity = opacity.value / 100;
                    if (titleMatch.checked && pageBody.appTitle) rule.title = pageBody.appTitle;
                    editor.change(pageBody.editing < 0 ? ["add", JSON.stringify(rule)] : ["update", String(pageBody.editing), JSON.stringify(rule)]);
                }
            }
        }
    }
    Connections { target: editor; function onSaved() { pageBody.formOpen = false; } }
    SettingsConfirmSheet {
        id: removeSheet
        foreground: view.foreground; surfaceColor: view.background
        title: Eitr.I18n.tr("Remove rule")
        onConfirmed: editor.change(["remove", String(pageBody.removing)])
    }
}
