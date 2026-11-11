import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../JsonState.js" as JsonState

// Settings > Input's mouse and touchpad settings: pointer speed, acceleration, natural
// scrolling and left-handed buttons, plus tap to click and typing protection when a touchpad
// is connected. scripts/pointer-settings.py saves what differs from the defaults (Reset goes
// back to them) and reloads Hyprland.
ControlCard {
    id: card
    required property color background
    required property color accent
    property bool active: false
    property bool live: true
    property var settings: ({})
    property string error: ""
    readonly property bool ready: settings.sensitivity !== undefined
    readonly property string helper: Eitr.Paths.code("quickshell/desktop-bar/scripts/pointer-settings.py")
    title: Eitr.I18n.tr("Mouse & Touchpad")
    surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
    onActiveChanged: if (active && live && !query.running) query.running = true
    function change(arguments) {
        if (!live || operation.running) return;
        operation.command = ["python3", helper].concat(arguments);
        operation.running = true;
    }
    function set(key, value) {
        if (settings[key] === value) return;
        settings = Object.assign({}, settings, {[key]: value});
        change(["set", key, String(value)]);
    }
    Process {
        id: query
        command: ["python3", card.helper, "summary"]
        stdout: StdioCollector { id: summary }
        onExited: function(code) {
            const result = JsonState.parse(summary.text, code, {sensitivity: "number", touchpad: "boolean"});
            card.error = result.ok ? "" : result.error;
            if (result.ok) card.settings = result.data;
        }
    }
    Process {
        id: operation
        stderr: StdioCollector { id: errors }
        onExited: function(code) {
            card.error = code ? errors.text.trim() : "";
            query.running = true;
        }
    }
    ControlRow {
        SettingsTarget { objectName: "setting-input-pointer-speed" }
        width: parent.width
        text: Eitr.I18n.tr("Pointer speed")
        description: Eitr.I18n.tr("How far the pointer moves for the same hand movement.")
        foreground: card.foreground
        PanelSlider {
            id: speed
            width: parent.width
            accent: card.accent; foreground: card.foreground
            from: -1; to: 1; stepSize: 0.05
            enabled: card.ready
            valueText: (value > 0 ? "+" : "") + Math.round(value * 100) + "%"
            Accessible.name: Eitr.I18n.tr("Pointer speed")
            Binding { target: speed; property: "value"; value: card.settings.sensitivity || 0; when: !speed.pressed }
            // Hyprland reloads on each change, so the speed is saved once the slider is let go.
            onPressedChanged: if (!pressed) card.set("sensitivity", Math.round(value * 100) / 100)
        }
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-pointer-acceleration" }
        text: Eitr.I18n.tr("Pointer acceleration")
        description: Eitr.I18n.tr("Fast movements carry the pointer further. Off moves it the same distance at any speed.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.acceleration
        available: card.ready && !operation.running
        onToggled: checked => card.set("acceleration", checked)
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-natural-scroll" }
        text: Eitr.I18n.tr("Natural scrolling")
        description: Eitr.I18n.tr("The mouse wheel moves the content, like a touchscreen.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.natural_scroll
        available: card.ready && !operation.running
        onToggled: checked => card.set("natural_scroll", checked)
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-left-handed" }
        text: Eitr.I18n.tr("Left-handed buttons")
        description: Eitr.I18n.tr("Swap the left and right mouse buttons.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.left_handed
        available: card.ready && !operation.running
        onToggled: checked => card.set("left_handed", checked)
    }
    Text {
        visible: !!card.settings.touchpad
        topPadding: 6
        text: Eitr.I18n.tr("Touchpad")
        color: card.foreground; opacity: PanelStyle.secondaryTextOpacity
        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-touchpad-natural-scroll" }
        visible: !!card.settings.touchpad
        text: Eitr.I18n.tr("Natural scrolling")
        description: Eitr.I18n.tr("Two fingers move the content, like a touchscreen.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.touchpad_natural_scroll
        available: card.ready && !operation.running
        onToggled: checked => card.set("touchpad_natural_scroll", checked)
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-tap-to-click" }
        visible: !!card.settings.touchpad
        text: Eitr.I18n.tr("Tap to click")
        description: Eitr.I18n.tr("A light tap on the touchpad clicks.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.tap_to_click
        available: card.ready && !operation.running
        onToggled: checked => card.set("tap_to_click", checked)
    }
    ToggleRow {
        SettingsTarget { objectName: "setting-input-disable-while-typing" }
        visible: !!card.settings.touchpad
        text: Eitr.I18n.tr("Ignore the touchpad while typing")
        description: Eitr.I18n.tr("A palm resting on the touchpad does not move the pointer while you type.")
        width: parent.width
        foreground: card.foreground; accent: card.accent
        checked: !!card.settings.disable_while_typing
        available: card.ready && !operation.running
        onToggled: checked => card.set("disable_while_typing", checked)
    }
    PanelButton {
        SettingsTarget { objectName: "setting-input-pointer-reset" }
        width: 180
        foreground: card.foreground
        text: Eitr.I18n.tr("Reset to defaults")
        available: !!card.settings.customized && !operation.running
        onClicked: card.change(["reset"])
    }
    Text {
        width: parent.width; visible: card.error !== ""
        text: card.error; wrapMode: Text.WordWrap
        color: card.foreground; font.pixelSize: PanelStyle.captionSize
    }
}
