pragma ComponentBehavior: Bound
import ".."
import QtQuick
import Eitr as Eitr

Grid {
    id: zoneGrid
    required property var host
    required property var barHost
    required property string zone
    property bool vertical: false
    property bool open: true
    property bool observing: true
    property int slotSize: host.workspaceItemSize
    property int slotSpacing: host.workspaceItemSpacing
    property int verticalWifiWidth: 56
    property real reveal: 1
    property bool clipReveal: false

    readonly property bool naturalPluginSize: zone !== "right"
    readonly property var items: BarIconOrder.zoneItems(zone)
    readonly property int keyboardCount: barHost && barHost.keyboardMenu && barHost.keyboardMenu.layouts ? barHost.keyboardMenu.layouts.length : 0
    readonly property bool remoteAllowed: !!(barHost && barHost.remoteServiceRef && barHost.remoteServiceRef.allowed)
    readonly property var obsState: barHost && barHost.obsMenu && barHost.obsMenu.obsState ? barHost.obsMenu.obsState : ({recording: false, paused: false})
    // Full bar only renders its collapse chevron when at least one item in right can collapse.
    readonly property bool hasHideable: items.some(entry => {
        if (entry.id === "notifications" || entry.id === "battery") return false;
        if (entry.id === "streaming") return remoteAllowed;
        if (entry.id === "keyboard") return keyboardCount > 1;
        return true;
    })

    signal panelRequested(string plugin, string panel, Item target)

    columns: vertical ? 1 : Math.max(1, items.length)
    spacing: slotSpacing
    horizontalItemAlignment: Grid.AlignHCenter
    verticalItemAlignment: Grid.AlignVCenter
    width: clipReveal && !vertical ? implicitWidth * reveal : implicitWidth
    height: clipReveal && vertical ? implicitHeight * reveal : implicitHeight
    clip: clipReveal

    function builtinIcon(item) {
        if (item.id === "idleLock") return zoneGrid.host.idleLockGlyph;
        if (item.id === "obs") return obsState.recording ? (obsState.paused ? "󰏤" : "󰑋") : "󰻂";
        if (item.id === "keyboard") return (barHost && barHost.keyboardMenu && barHost.keyboardMenu.activeCode) || "󰌌";
        if (item.id === "updates") return zoneGrid.host.updatesIcon;
        if (item.id === "battery") return zoneGrid.host.batteryIcon;
        return item.glyph;
    }

    function builtinIconSize(item) {
        if (item.id === "obs") return obsState.recording && !obsState.paused ? 22 : 16;
        if (item.id === "keyboard") return 11;
        return item.iconSize || 15;
    }

    function builtinTooltip(item) {
        if (item.id === "ai") return Eitr.I18n.tr("AI Usage");
        if (item.id === "hardware") return Eitr.I18n.tr("Hardware");
        if (item.id === "idleLock") return zoneGrid.host.idleLockTooltip;
        if (item.id === "bluetooth") return Eitr.I18n.tr("Bluetooth");
        if (item.id === "display") return Eitr.I18n.tr("Display");
        if (item.id === "audio") return Eitr.I18n.tr("Audio/Mic");
        if (item.id === "streaming") return Eitr.I18n.tr("Streaming");
        if (item.id === "obs") return obsState.recording ? (obsState.paused ? Eitr.I18n.tr("Recording paused") : Eitr.I18n.tr("Recording")) : Eitr.I18n.tr("OBS Studio");
        if (item.id === "keyboard") return barHost && barHost.keyboardMenu && barHost.keyboardMenu.activeLabel ? Eitr.I18n.tr("Keyboard · {layout}", {layout: barHost.keyboardMenu.activeLabel}) : Eitr.I18n.tr("Keyboard");
        if (item.id === "updates") return zoneGrid.host.updatesTooltip;
        if (item.id === "battery") return Math.round(zoneGrid.host.battery.percent) + "% · " + zoneGrid.host.battery.status;
        return item.title || "";
    }

    function builtinMenu(itemId) {
        if (!barHost) return null;
        if (itemId === "ai") return barHost.aiMenu;
        if (itemId === "hardware") return barHost.hardwareMenu;
        if (itemId === "wifi") return barHost.wifiMenu;
        if (itemId === "bluetooth") return barHost.bluetoothMenu;
        if (itemId === "display") return barHost.brightnessMenu;
        if (itemId === "audio") return barHost.volumeMenu;
        if (itemId === "streaming") return barHost.streamingMenu;
        if (itemId === "obs") return barHost.obsMenu;
        if (itemId === "keyboard") return barHost.keyboardMenu;
        if (itemId === "battery") return barHost.batteryMenu;
        return null;
    }

    function activateBuiltin(itemId, button) {
        if (itemId === "idleLock") {
            if (zoneGrid.host.switchIdleLock) zoneGrid.host.switchIdleLock();
            return;
        }
        if (itemId === "updates") {
            if (button === Qt.RightButton) zoneGrid.host.checkUpdates();
            else zoneGrid.host.openSystemUpdate();
            return;
        }
        if (itemId === "battery") {
            if (barHost && barHost.toggleKind) barHost.toggleKind("battery");
            return;
        }
        const menu = builtinMenu(itemId);
        if (menu && barHost && barHost.togglePanel) barHost.togglePanel(menu);
    }

    function closeOnCollapse(itemId, itemOpen) {
        if (itemOpen) return;
        const menu = builtinMenu(itemId);
        if (menu) menu.opened = false;
    }

    Repeater {
        model: zoneGrid.items
        delegate: Item {
            id: slotItem
            required property var modelData
            readonly property string itemId: modelData.id
            readonly property bool isBuiltin: modelData.kind === "builtin"
            readonly property bool isWifi: isBuiltin && itemId === "wifi"
            readonly property bool isNotifications: isBuiltin && itemId === "notifications"
            readonly property bool isGenericBuiltin: (isBuiltin && !isWifi && !isNotifications) || itemId === "ai" || itemId === "hardware"
            readonly property bool isPlugin: modelData.kind === "plugin" && itemId !== "ai" && itemId !== "hardware"
            readonly property bool itemAvailable: {
                if (itemId === "streaming") return zoneGrid.remoteAllowed;
                if (itemId === "battery") return !!zoneGrid.host.battery.available;
                if (itemId === "keyboard") return zoneGrid.keyboardCount > 1;
                return true;
            }
            readonly property bool itemOpen: {
                if (!itemAvailable) return false;
                if (isNotifications || itemId === "battery") return zoneGrid.zone === "right" ? true : zoneGrid.open;
                return zoneGrid.zone === "right" ? zoneGrid.open : zoneGrid.open;
            }
            readonly property Item control: wifiLoader.item || notifyLoader.item || builtinLoader.item || pluginLoader.item || null

            property Item registeredControl: null
            property string registeredId: ""
            property bool registeredVertical: false
            function syncRegistration() {
                if (registeredControl && registeredId && (registeredControl !== control || registeredId !== itemId || registeredVertical !== zoneGrid.vertical)) {
                    if (zoneGrid.barHost && zoneGrid.barHost.unregisterIconItem)
                        zoneGrid.barHost.unregisterIconItem(registeredVertical, registeredId, registeredControl);
                    registeredControl = null;
                    registeredId = "";
                }
                if (control && itemId && (registeredControl !== control || registeredId !== itemId || registeredVertical !== zoneGrid.vertical)) {
                    registeredControl = control;
                    registeredId = itemId;
                    registeredVertical = zoneGrid.vertical;
                    if (zoneGrid.barHost && zoneGrid.barHost.registerIconItem)
                        zoneGrid.barHost.registerIconItem(registeredVertical, registeredId, registeredControl);
                }
            }
            onControlChanged: syncRegistration()
            onItemIdChanged: syncRegistration()
            Connections {
                target: zoneGrid
                function onVerticalChanged() { slotItem.syncRegistration(); }
            }
            Component.onCompleted: syncRegistration()
            Component.onDestruction: {
                if (registeredControl && registeredId && zoneGrid.barHost && zoneGrid.barHost.unregisterIconItem)
                    zoneGrid.barHost.unregisterIconItem(registeredVertical, registeredId, registeredControl);
            }

            width: control ? control.width : 0
            height: control ? control.height : 0
            visible: itemAvailable && (itemOpen || (zoneGrid.vertical ? height : width) > 0)

            Loader {
                id: wifiLoader
                active: slotItem.isWifi
                sourceComponent: StatusCommand {
                    host: zoneGrid.host
                    text: zoneGrid.host.wifiGlyph
                    hoverLabel: "WiFi"
                    fontSize: 16
                    open: slotItem.itemOpen
                    slotWidth: zoneGrid.slotSize
                    fixedWidth: zoneGrid.vertical ? zoneGrid.verticalWifiWidth : zoneGrid.slotSize
                    height: zoneGrid.vertical ? (open ? 24 : 0) : 24
                    clickable: true
                    onClicked: zoneGrid.activateBuiltin("wifi", Qt.LeftButton)
                    onOpenChanged: zoneGrid.closeOnCollapse("wifi", open)
                }
            }

            Loader {
                id: notifyLoader
                active: slotItem.isNotifications && !!(zoneGrid.barHost && zoneGrid.barHost.notificationsRef)
                sourceComponent: NotificationWidget {
                    host: zoneGrid.host
                    notificationService: zoneGrid.barHost.notificationsRef
                    swing: zoneGrid.barHost.clockActivity ? zoneGrid.barHost.clockActivity.bellAngle : 0
                    visible: slotItem.itemOpen
                    width: slotItem.itemOpen ? zoneGrid.slotSize : 0
                    height: slotItem.itemOpen ? 24 : 0
                    onOpenRequested: if (zoneGrid.barHost && zoneGrid.barHost.toggleKind) zoneGrid.barHost.toggleKind("notifications")
                }
            }

            Loader {
                id: builtinLoader
                active: slotItem.isGenericBuiltin
                sourceComponent: StatusIcon {
                    readonly property bool barItem: slotItem.itemId === "ai" || slotItem.itemId === "hardware"
                    readonly property var entry: slotItem.modelData.entry
                    host: zoneGrid.host
                    visible: slotItem.itemAvailable
                    icon: zoneGrid.builtinIcon(slotItem.modelData)
                    iconSize: zoneGrid.builtinIconSize(slotItem.modelData)
                    spinning: slotItem.itemId === "updates" && !!(zoneGrid.host.updates && zoneGrid.host.updates.checking)
                    tooltip: zoneGrid.builtinTooltip(slotItem.modelData)
                    slotWidth: zoneGrid.slotSize
                    height: zoneGrid.vertical ? (open ? 24 : 0) : 24
                    open: slotItem.itemOpen
                    clickable: true
                    rightClickable: slotItem.itemId === "updates"
                    onClicked: function(button) {
                        if (barItem) zoneGrid.panelRequested(entry.plugin, entry.panel, slotItem.control);
                        else zoneGrid.activateBuiltin(slotItem.itemId, button);
                    }
                    onOpenChanged: zoneGrid.closeOnCollapse(slotItem.itemId, open)
                }
            }

            Loader {
                id: pluginLoader
                active: slotItem.isPlugin && !!slotItem.modelData.entry
                sourceComponent: PluginComponent {
                    id: pluginSlot
                    property real reservedWidth: 0
                    function fit() {
                        const target = Math.min(960, implicitWidth);
                        if (target > reservedWidth || reservedWidth - target > 16) reservedWidth = target;
                    }
                    onImplicitWidthChanged: fit()
                    Component.onCompleted: fit()
                    entry: slotItem.modelData.entry
                    clockFormat: zoneGrid.host.barClock
                    observing: zoneGrid.observing && slotItem.itemOpen
                    verticalBar: zoneGrid.vertical
                    iconSlot: !zoneGrid.naturalPluginSize
                    readonly property real naturalWidth: zoneGrid.naturalPluginSize ? (zoneGrid.vertical ? zoneGrid.slotSize : reservedWidth) : zoneGrid.slotSize
                    readonly property real naturalHeight: zoneGrid.naturalPluginSize
                        ? (zoneGrid.vertical ? ((entry.capabilities || []).includes("weather") ? zoneGrid.slotSize : reservedWidth) : barContentHeight)
                        : zoneGrid.slotSize
                    width: slotItem.itemOpen ? naturalWidth : 0
                    height: slotItem.itemOpen ? naturalHeight : 0
                    visible: slotItem.itemOpen
                    verticalContent: zoneGrid.naturalPluginSize && zoneGrid.vertical
                    foreground: zoneGrid.host.barFg
                    background: zoneGrid.host.barBackground ? zoneGrid.host.barBackground() : zoneGrid.host.workspaceMenuBg
                    accent: zoneGrid.host.activeBg
                    onPanelRequested: function(plugin, panel) { zoneGrid.panelRequested(plugin, panel, pluginSlot); }
                    HoverHandler { id: pluginHover }
                    BarTooltip {
                        target: pluginSlot
                        hovered: pluginHover.hovered && ((pluginSlot.entry.capabilities || []).includes("weather")
                            ? zoneGrid.vertical
                            : !(zoneGrid.zone === "clockStart" || zoneGrid.zone === "clockEnd"))
                        text: (pluginSlot.entry.capabilities || []).includes("weather")
                            ? Eitr.I18n.tr("Weather") + (zoneGrid.vertical && pluginSlot.detail ? " · " + pluginSlot.detail : "")
                            : pluginSlot.entry.title + (pluginSlot.detail ? " · " + pluginSlot.detail : "")
                        foreground: zoneGrid.host.fg
                        background: zoneGrid.host.workspaceMenuBg
                    }
                }
            }
        }
    }
}
