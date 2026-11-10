import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import QtQuick.Effects
import Quickshell

Column {
    id: navigation
    required property var centerRef
    signal pageSelected(string page)
    signal chatRequested()
    signal settingsRequested()
    Layout.alignment: Qt.AlignTop
    Layout.preferredWidth: 34
    spacing: 10
    // Display-only: the picture is changed in Settings > User. Without one, nothing is shown.
    Eitr.Avatar {
        objectName: "controlCenterAvatar"
        anchors.horizontalCenter: parent.horizontalCenter
        size: 28
        showInitial: false
        source: navigation.centerRef.accountPicture.path ? "file://" + navigation.centerRef.accountPicture.path + "?v=" + (navigation.centerRef.accountPicture.version || 0) : ""
        accent: navigation.centerRef.accent; background: navigation.centerRef.background
    }
    Repeater {
        model: [{key: "general", icon: "󰕮", name: "General"},
            {key: "plugins", icon: "󰏖", name: "Plugins"},
            {key: "tools", icon: "󱁤", name: "Tools"}]
        PanelButton {
            textSize: 12; iconSize: 20
            id: tab
            required property var modelData
            width: 34; height: 34; icon: true; text: modelData.key === "general" ? "" : modelData.icon
            Image {
                anchors.centerIn: parent; width: 22; height: 22
                visible: tab.modelData.key === "general"
                source: Quickshell.shellDir + "/assets/eitr-logo-white.svg"
                fillMode: Image.PreserveAspectFit
                // Drawn at its shown size: scaling the large SVG down afterwards leaves jagged edges.
                sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                smooth: true
                layer.enabled: true
                layer.effect: MultiEffect { colorization: 1; colorizationColor: navigation.centerRef.foreground }
            }
            foreground: navigation.centerRef.foreground; selected: navigation.centerRef.page === modelData.key && !navigation.centerRef.chatOpen
            onClicked: navigation.pageSelected(modelData.key)
            HoverHandler { id: tabHover }
            BarTooltip { target: tab; hovered: tabHover.hovered; text: Eitr.I18n.tr(tab.modelData.name); foreground: navigation.centerRef.foreground; background: navigation.centerRef.background }
        }
    }
    PanelButton {
        id: chatButton
        visible: !!navigation.centerRef.chatAssistant.identifier && navigation.centerRef.organizationPolicy.development !== false && navigation.centerRef.organizationPolicy.assistants_together !== false
        width: 34; height: 34; icon: true; text: "󰭻"
        foreground: navigation.centerRef.foreground; selected: navigation.centerRef.chatOpen
        onClicked: navigation.chatRequested()
        HoverHandler { id: chatHover }
        BarTooltip { target: chatButton; hovered: chatHover.hovered; text: Eitr.I18n.tr("Chat with %1", [navigation.centerRef.chatAssistant.name || ""]); foreground: navigation.centerRef.foreground; background: navigation.centerRef.background }
    }
    // Appearance, devices and system settings live in the Settings window; always the last button.
    PanelButton {
        id: settingsButton
        objectName: "allSettingsButton"
        width: 34; height: 34; icon: true; text: "󰒓"
        foreground: navigation.centerRef.foreground
        Accessible.name: Eitr.I18n.tr("All settings")
        onClicked: navigation.settingsRequested()
        HoverHandler { id: settingsHover }
        BarTooltip { target: settingsButton; hovered: settingsHover.hovered; text: Eitr.I18n.tr("All settings"); foreground: navigation.centerRef.foreground; background: navigation.centerRef.background }
    }
}
