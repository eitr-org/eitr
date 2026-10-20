pragma Singleton
// Shared import for package shells and deliberate component overrides.
import QtQuick
import Quickshell

QtObject {
    readonly property string codeRoot: Quickshell.env("EITR_CODE_ROOT") || "/usr/share/eitr"
    readonly property string configRoot: {
        const configured = Quickshell.env("XDG_CONFIG_HOME");
        return configured && configured.startsWith("/") ? configured : Quickshell.env("HOME") + "/.config";
    }
    function code(relative) { return codeRoot + "/" + relative; }
    function config(relative) { return configRoot + "/" + relative; }
    function settings(text) {
        const value = JSON.parse(text);
        if (!value || typeof value !== "object" || Array.isArray(value)
            || (value.version !== undefined && value.version !== 1))
            throw new Error("Unsupported EITR settings schema");
        return Object.assign({}, value, {version: 1});
    }
}
