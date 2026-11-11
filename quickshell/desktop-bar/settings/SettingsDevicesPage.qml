import ".."
import QtQuick
import Quickshell
import Eitr as Eitr

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
        if (page === "connections") return tab === "bluetooth" ? bluetoothPage.dismiss() : wifiPage.dismiss();
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
            title: view.tab === "nightlight" ? Eitr.I18n.tr("Night Light") : Eitr.I18n.tr("Displays")
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
        SettingsSoundPage {
            width: parent.width
            visible: view.page === "sound"
            active: view.active && visible; live: view.live
            foreground: view.foreground; background: view.background; accent: view.accent
        }
        SettingsWifiPage {
            id: wifiPage
            width: parent.width
            visible: view.page === "connections" && view.tab !== "bluetooth"
            active: view.active && visible; live: view.live
            networkService: view.networkService
            foreground: view.foreground; background: view.background; accent: view.accent
        }
        SettingsBluetoothPage {
            id: bluetoothPage
            width: parent.width
            visible: view.page === "connections" && view.tab === "bluetooth"
            active: view.active && visible; live: view.live
            foreground: view.foreground; background: view.background; accent: view.accent
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
        SettingsPointerCard {
            visible: view.page === "input"
            active: view.active && visible; live: view.live
            foreground: view.foreground; background: view.background; accent: view.accent
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
