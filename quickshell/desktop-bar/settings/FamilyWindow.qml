import ".."
import QtQuick

// The opaque window shared by Settings, the Handbook and Eitr Store: theme
// colours through SettingsPalette, or the website palette when Settings chooses it.
LibraryWindow {
    id: window
    required property color foreground
    required property color background
    required property color accent
    Binding { target: SettingsPalette; property: "themeBackground"; value: window.background }
    Binding { target: SettingsPalette; property: "themeForeground"; value: window.foreground }
    Binding { target: SettingsPalette; property: "themeAccent"; value: window.accent }
    color: Qt.rgba(SettingsPalette.background.r, SettingsPalette.background.g, SettingsPalette.background.b, 1)
}
