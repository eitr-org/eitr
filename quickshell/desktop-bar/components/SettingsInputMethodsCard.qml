import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

// Settings > Input's optional CJK input methods (fcitx5): status, one-click install
// via the standard software task terminal, and fcitx5-configtool launch when installed.
ControlCard {
    id: card
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var methods: [
        {id: "japanese", label: Eitr.I18n.tr("Japanese (Mozc)"), installed: false, recommended: false},
        {id: "korean", label: Eitr.I18n.tr("Korean (Hangul)"), installed: false, recommended: false},
        {id: "chinese", label: Eitr.I18n.tr("Chinese (Pinyin)"), installed: false, recommended: false}
    ]
    property bool configtoolAvailable: false
    property string error: ""
    readonly property string helper: Eitr.Paths.library("eitr_input_methods.py")
    title: Eitr.I18n.tr("Input Methods")
    surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
    SettingsTarget { objectName: "setting-input-methods" }
    onActiveChanged: if (active && live && !query.running) query.running = true
    function runHelper(arguments) {
        if (!live) return;
        Quickshell.execDetached(["python3", helper].concat(arguments));
    }
    Process {
        id: query
        command: ["python3", card.helper, "summary"]
        stdout: StdioCollector { id: summaryOutput }
        onExited: function(code) {
            const result = JsonState.parse(summaryOutput.text, code, {methods: "array", configtoolAvailable: "boolean"});
            card.error = result.ok ? "" : result.error;
            if (result.ok) {
                card.methods = result.data.methods;
                card.configtoolAvailable = !!result.data.configtoolAvailable;
            }
        }
    }
    Repeater {
        model: card.methods
        ControlRow {
            required property var modelData
            width: parent.width
            text: modelData.label
            description: modelData.installed
                ? Eitr.I18n.tr("Installed · Ctrl + Space switches input method")
                : (modelData.recommended
                    ? Eitr.I18n.tr("Recommended for your desktop language (fcitx5)")
                    : Eitr.I18n.tr("Optional CJK input method (fcitx5)"))
            foreground: card.foreground
            controlWidth: 120
            PanelButton {
                anchors.right: parent.right
                width: 112; height: 34
                foreground: card.foreground
                text: modelData.installed ? Eitr.I18n.tr("Installed") : Eitr.I18n.tr("Install")
                available: !modelData.installed
                onClicked: card.runHelper(["install", modelData.id])
            }
        }
    }
    PanelButton {
        visible: card.configtoolAvailable
        width: 220
        foreground: card.foreground
        text: Eitr.I18n.tr("Configure fcitx5…")
        onClicked: card.runHelper(["configtool"])
    }
    Text {
        width: parent.width; visible: card.error !== ""
        text: card.error; wrapMode: Text.WordWrap
        color: card.foreground; font.pixelSize: PanelStyle.captionSize
    }
}
