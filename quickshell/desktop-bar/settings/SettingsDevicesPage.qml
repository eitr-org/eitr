import ".."
import QtQuick
import Quickshell
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Flickable {
    id: view
    objectName: "settings-devices-page"
    required property string page
    required property string title
    required property color foreground
    required property color background
    required property color accent
    signal tabRequested(string value)
    property string tab: "wifi"
    property bool active: false
    property bool live: true
    property var networkService: null
    contentHeight: content.implicitHeight + 18
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    onPageChanged: contentY = 0
    function dismiss() {
        if (page === "connections" && wifiSlot.item && wifiSlot.item.escapeHandler)
            return wifiSlot.item.escapeHandler();
        return false;
    }
    Column {
        id: content
        width: view.width
        spacing: 18
        SettingsPageHeader {
            page: view.page
            foreground: view.foreground
        }
        TabStrip { foreground: SettingsPalette.foreground; gold: SettingsPalette.gold; carved: true;
            width: parent.width
            visible: ["connections", "displays"].includes(view.page)
            height: visible ? 42 : 0
            choices: view.page === "displays" ? [{id: "displays", label: Eitr.I18n.tr("Displays")}, {id: "nightlight", label: Eitr.I18n.tr("Night Light")}] : [{id: "wifi", label: Eitr.I18n.tr("Wi-Fi")}, {id: "bluetooth", label: Eitr.I18n.tr("Bluetooth")}]
            current: view.tab
            onChosen: value => { view.tabRequested(value); view.contentY = 0; }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Displays")
            foreground: view.foreground
            visible: displaySlot.active
            Loader {
                id: displaySlot
                width: parent.width
                height: active && item ? item.implicitHeight : 0
                active: view.active && view.page === "displays"
                sourceComponent: Component {
                    BrightnessMenu {
                        objectName: "settings-displaySlot"
                        settingsSection: view.tab || "displays"
                        mapHighlight: SettingsInk.gold
                        inlineParent: displaySlot
                        target: null
                        anchors.fill: parent
                        foreground: view.foreground
                        background: view.background
                        accent: view.accent
                        opened: view.active
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Sound")
            foreground: view.foreground
            visible: audioSlot.active
            Loader {
                id: audioSlot
                width: parent.width
                height: active && item ? item.implicitHeight : 0
                active: view.active && view.page === "sound"
                sourceComponent: Component {
                    AudioMenu {
                        objectName: "settings-audioSlot"
                        inlineParent: audioSlot
                        target: null
                        anchors.fill: parent
                        foreground: view.foreground
                        background: view.background
                        accent: view.accent
                        opened: view.active
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Event sounds")
            foreground: view.foreground
            visible: view.page === "sound"
            EventSoundSettings {
                visible: view.page === "sound"
                width: parent.width
                foreground: view.foreground
                accent: view.accent
                live: view.live
                hasBattery: view.active && view.page === "sound" && PowerService.battery.available
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("WiFi")
            foreground: view.foreground
            visible: wifiSlot.active
            Loader {
                id: wifiSlot
                width: parent.width
                height: active && item ? item.implicitHeight : 0
                active: view.active && view.page === "connections" && view.tab !== "bluetooth" && !!view.networkService
                sourceComponent: Component {
                    WifiMenu {
                        objectName: "settings-wifiSlot"
                        inlineParent: wifiSlot
                        target: null
                        anchors.fill: parent
                        networkService: view.networkService
                        foreground: view.foreground
                        background: view.background
                        accent: view.accent
                        opened: view.active
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Bluetooth")
            foreground: view.foreground
            visible: bluetoothSlot.active
            Loader {
                id: bluetoothSlot
                width: parent.width
                height: active && item ? item.implicitHeight : 0
                active: view.active && view.page === "connections" && view.tab === "bluetooth"
                sourceComponent: Component {
                    BluetoothMenu {
                        objectName: "settings-bluetoothSlot"
                        inlineParent: bluetoothSlot
                        target: null
                        anchors.fill: parent
                        foreground: view.foreground
                        background: view.background
                        accent: view.accent
                        opened: view.active
                    }
                }
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("Keyboard Layout")
            foreground: view.foreground
            visible: view.page === "input"
            SettingsInputPage {
                id: inputContent
                visible: view.page === "input"
                width: parent.width
                active: view.active && visible
                live: view.live
                foreground: view.foreground
                background: view.background
                accent: view.accent
            }
        }
        ControlCard { surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true;
            title: Eitr.I18n.tr("WiFi backend")
            foreground: view.foreground
            visible: view.page === "connections" && view.tab !== "bluetooth"
            Column {
                visible: view.page === "connections" && view.tab !== "bluetooth"
                width: parent.width
                spacing: 6
                Text {
                    text: Eitr.I18n.tr("WiFi backend")
                    color: view.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                Text {
                    width: parent.width
                    text: Eitr.I18n.tr("Applies after reboot; saved profiles are kept.")
                    wrapMode: Text.WordWrap
                    color: view.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                }
                ChoiceSegmented { gold: SettingsInk.gold; background: SettingsInk.background;
                    width: parent.width
                    foreground: view.foreground
                    choices: [
                        {
                            id: "iwd",
                            label: "iwd"
                        },
                        {
                            id: "NetworkManager",
                            label: "NetworkManager"
                        }
                    ]
                    current: view.networkService ? view.networkService.details.data.backend : ""
                    onChosen: value => {
                        if (view.live)
                            Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), "network-backend", value]);
                    }
                }
                PanelButton {
                    width: parent.width
                    text: Eitr.I18n.tr("Restore Original Network Configuration")
                    foreground: view.foreground
                    onClicked: if (view.live)
                        Quickshell.execDetached(["python3", Eitr.Paths.code("quickshell/desktop-bar/scripts/menu-action.py"), "network-backend", "Restore Original Network Configuration"])
                }
            }
        }
        PanelButton {
            objectName: "settings-page-handbook"
            width: 160
            text: Eitr.I18n.tr("Learn more")
            foreground: view.foreground
            onClicked: if (view.live)
                Quickshell.execDetached(["bash", Eitr.Paths.code("quickshell/desktop-bar/scripts/handbook.sh"), "open", view.page === "connections" ? "connectivity" : "control-center"])
        }
    }
}
