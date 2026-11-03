import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Shapes
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../EdgeSlopes.js" as EdgeSlopes

Item {
    id: catalog
    property color foreground: SiteStyle.fg
    property color background: SiteStyle.bg
    property color accent: SiteStyle.accent
    property bool opened: false
    property bool live: true
    property string kind: "themes"
    property var installed: []
    property var availableItems: []
    property var selected: []
    property var updates: ({})
    property var updateCache: ({})
    property int opening: 0
    property var previews: ({})
    property var previewRequests: ({})
    property string error: ""
    property string repositoryError: ""
    property string installedError: ""
    property string progress: ""
    property bool busy: false
    property bool loading: false
    property bool reviewing: false
    property var removing: null
    property int generation: 0
    property var transport: function(name, args, callback, owner) { return DesktopData.queryCatalog(name, args, owner || catalog, callback); }
    Item { id: updateOwner }
    signal closeRequested()
    readonly property var more: availableItems.filter(item => !installed.some(local => local.id === item.id))
    property string tab: "official"
    property bool showHidden: false
    readonly property bool getMore: tab !== "installed"
    property bool sidebarFocus: true
    property var counts: ({})
    readonly property bool compact: width < 760
    readonly property int sidebarWidth: compact ? 64 : 220
    readonly property int navigationIndex: (kind === "plugins" ? 1 : 0)
    function navigate(index) {
        kind = index % 2 ? "plugins" : "themes";
        cursor = -1; scroll.contentY = 0;
        sidebarFocus = true; forceActiveFocus();
    }
    function rememberCounts() {
        if (!installed || !availableItems) return;
        counts = Object.assign({}, counts, {[kind]: {installed: installed.length, available: availableItems.filter(item => !installed.some(local => local.id === item.id)).length, loaded: availableItems.length > 0 || indexLoaded}});
    }
    property bool indexLoaded: false
    onInstalledChanged: rememberCounts()
    onAvailableItemsChanged: rememberCounts()
    onIndexLoadedChanged: rememberCounts()
    property string tone: "all"
    property int cursor: -1
    readonly property int pageSize: 24
    property int shown: pageSize
    onCursorChanged: if (cursor >= shown - columns) shown = Math.ceil((cursor + columns + 1) / pageSize) * pageSize
    readonly property int columns: Math.max(1, Math.min(3, Math.floor((width - sidebarWidth - 48) / 250)))
    function filtered(items) { return kind !== "themes" ? items : items.filter(item => tone === "all" || item.light === (tone === "light")); }
    readonly property var locals: filtered(installed.filter(item => showHidden || !item.hidden))
    readonly property var discoveries: filtered(tab === "community" ? availableItems.map(item => Object.assign({}, item, installed.find(local => local.id === item.id) || {}, {kind: "community"})) : installed.filter(item => !item.hidden && ["builtin", "official"].includes(item.kind)).concat(more.map(item => Object.assign({kind: "official"}, item))))
    readonly property var navigable: getMore ? discoveries : locals
    function toggle(item) {
        if (kind !== "themes" || busy || isInstalled(item)) return;
        selected = selected.includes(item.id) ? selected.filter(themeId => themeId !== item.id) : selected.concat([item.id]);
    }
    function isInstalled(item) { return installed.some(local => local.id === item.id); }
    function activate(item, local) {
        if (item.hidden) return;
        if (busy) return;
        if (local && kind === "themes" && !item.current) act("apply", {id: item.id});
        else if (!local && kind === "plugins") progress = pluginNote;
        else if (!local) toggle(item);
        sidebarFocus = false; forceActiveFocus();
    }
    readonly property string pluginNote: Eitr.I18n.tr("Installing plugins from the catalog is coming soon; use Walker > Plugins for now")
    function previewKey(item) { return kind + ":" + (tab === "community" ? "community" : "official") + ":" + item.id; }
    function imageFor(item) { return item.previewUrl || (kind === "plugins" && isInstalled(item) ? item.preview || item.icon : "") || previews[previewKey(item)] || previews[item.id] || ""; }
    readonly property var chosen: more.filter(item => selected.includes(item.id))
    readonly property real totalSize: chosen.reduce((total, item) => total + (item.size || 0), 0)
    function sizeText(bytes) { if (!bytes) return Eitr.I18n.tr("Size unavailable"); return bytes < 1048576 ? Math.ceil(bytes / 1024) + " KiB" : (bytes / 1048576).toFixed(1) + " MiB"; }
    function badge(item) {
        return ({builtin: Eitr.I18n.tr("Built in"), official: Eitr.I18n.tr("Official"), community: Eitr.I18n.tr("Community"), "third-party": Eitr.I18n.tr("Third-party"), own: Eitr.I18n.tr("Yours")})[item.kind] || Eitr.I18n.tr("Official");
    }
    function request(name, args, callback) {
        const current = generation;
        transport(name, Object.assign({kind: kind, channel: tab}, args), function(failure, data) {
            if (!opened || current !== generation) return;
            callback(failure || data.error || "", data);
        });
    }
    // Everything loads once per opening; tabs and the sidebar only switch views.
    property var store: ({})
    readonly property var sources: ["installed", "official", "community"]
    function fetch(catalogKind, source) {
        const key = catalogKind + ":" + source;
        store = Object.assign({}, store, {[key]: Object.assign({}, store[key] || {items: []}, {pending: true, error: ""})});
        sync();
        request(source === "installed" ? "installed" : "index", {kind: catalogKind, channel: source}, function(failure, data) {
            store = Object.assign({}, store, {[key]: {items: failure ? (store[key].items || []) : data.items || [], error: failure, pending: false, loaded: !failure}});
            if (source === "installed" && !failure)
                counts = Object.assign({}, counts, {[catalogKind]: Object.assign({}, counts[catalogKind] || {}, {installed: (data.items || []).length})});
            sync();
        });
    }
    function sync() {
        const local = store[kind + ":installed"] || {items: []};
        const index = tab === "installed" ? {items: [], loaded: true} : store[kind + ":" + tab] || {items: []};
        installed = local.items; installedError = local.error || ""; loading = !!local.pending;
        availableItems = index.items; repositoryError = index.error || ""; indexLoaded = !!index.loaded;
    }
    function refreshInstalled() { fetch(kind, "installed"); }
    function refreshIndex() { if (tab !== "installed") fetch(kind, tab); }
    function load() {
        generation++;
        store = ({}); installed = []; availableItems = []; selected = []; updates = updateCache[kind] || ({}); previews = ({}); previewRequests = ({});
        indexLoaded = false; reviewing = false; removing = null; busy = false; error = ""; repositoryError = ""; installedError = ""; progress = "";
        if (!live || !opened) return;
        for (const catalogKind of [kind, kind === "themes" ? "plugins" : "themes"])
            for (const source of sources) fetch(catalogKind, source);
    }
    function switchView() {
        cursor = -1; scroll.contentY = 0; shown = pageSize; selected = []; error = ""; progress = "";
        updates = updateCache[kind] || ({});
        if (live && opened) sync();
    }
    function checkUpdates() {
        const currentOpening = opening;
        for (const catalogKind of ["themes", "plugins"]) {
            transport("check", {kind: catalogKind}, function(failure, data) {
                if (!opened || opening !== currentOpening || failure || data.error) return;
                updateCache = Object.assign({}, updateCache, {[catalogKind]: data.updates || {}});
                if (kind === catalogKind) updates = updateCache[catalogKind];
            }, updateOwner);
        }
    }
    function act(name, args) {
        if (busy) return;
        busy = true; error = "";
        progress = Eitr.I18n.tr("Applying changes…");
        request(name, args, function(failure, data) {
            busy = false; progress = ""; error = failure;
            if (!failure) { selected = []; reviewing = false; removing = null; }
            refreshInstalled();
        });
    }

    function preview(item) {
        const key = previewKey(item);
        if (!live || !opened || previews[key] || previewRequests[key]) return;
        if (kind === "plugins" && !item.preview && !item.icon) return;
        previewRequests = Object.assign({}, previewRequests, {[key]: true});
        request("preview", {id: item.id}, function(failure, data) {
            if (!failure) previews = Object.assign({}, previews, {[key]: data.image});
        });
    }
    function cancelSheet() { if (!busy) { reviewing = false; removing = null; } }
    function confirm() {
        if (busy) return;
        if (reviewing) act("install", {ids: chosen.map(item => item.id)});
        else if (removing) act("remove", {id: removing.id});
    }
    onTabChanged: switchView()
    onKindChanged: switchView()
    onToneChanged: { shown = pageSize; scroll.contentY = 0; }
    onShowHiddenChanged: shown = pageSize
    onOpenedChanged: {
        if (opened) { opening++; updateCache = ({}); load(); if (live) checkUpdates(); forceActiveFocus(); }
        else { generation++; DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); busy = false; }
    }
    Component.onDestruction: { DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); }
    focus: opened
    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) {
            if (reviewing || removing) cancelSheet(); else closeRequested();
            event.accepted = true;
        } else if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && (reviewing || removing)) {
            confirm(); event.accepted = true;
        } else if (!reviewing && !removing && !busy) {
            if (sidebarFocus) {
                if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) {
                    navigate(Math.max(0, Math.min(1, navigationIndex + (event.key === Qt.Key_Down ? 1 : -1))));
                    event.accepted = true; return;
                }
                if (event.key === Qt.Key_Right || event.key === Qt.Key_Tab) {
                    sidebarFocus = false; cursor = navigable.length ? 0 : -1;
                    event.accepted = true; return;
                }
            } else if (event.key === Qt.Key_Left && (cursor < 0 || cursor % columns === 0)) {
                sidebarFocus = true; cursor = -1; event.accepted = true; return;
            }
            const count = navigable.length;
            let delta = 0;
            if (event.key === Qt.Key_Right) delta = 1;
            if (event.key === Qt.Key_Left) delta = -1;
            if (event.key === Qt.Key_Down) delta = columns;
            if (event.key === Qt.Key_Up) delta = -columns;
            if (delta && count) { cursor = Math.max(0, Math.min(count - 1, cursor < 0 ? 0 : cursor + delta)); event.accepted = true; }
            else if (event.key === Qt.Key_Space && getMore && cursor >= 0 && cursor < count) { toggle(navigable[cursor]); event.accepted = true; }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                if (chosen.length) reviewing = true;
                else if (cursor >= 0 && cursor < count) activate(navigable[cursor], isInstalled(navigable[cursor]));
                event.accepted = true;
            }
        }
    }
    Rectangle { anchors.fill: parent; color: catalog.background; z: -1 }
    component Label: Text {
        color: catalog.foreground
        font.family: SiteStyle.mono
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
    component SiteButton: Rectangle {
        id: button
        property color foreground: catalog.foreground
        property string text: ""
        property bool available: true
        property bool selected: false
        property bool primary: false
        property bool icon: false
        property bool flat: false
        property int textAlignment: Text.AlignHCenter
        readonly property bool hovered: hover.containsMouse
        signal clicked()
        height: 32; radius: 3
        activeFocusOnTab: true
        enabled: available
        opacity: available ? 1 : 0.45
        color: primary ? SiteStyle.primaryStart : selected ? SiteStyle.raised : hover.containsMouse ? SiteStyle.raised : flat ? catalog.background : SiteStyle.surface
        gradient: primary ? primaryGradient : null
        border.width: 1
        border.color: primary ? SiteStyle.primaryStart : selected || activeFocus ? catalog.accent : hover.containsMouse ? SiteStyle.lineStrong : SiteStyle.line
        Gradient { id: primaryGradient; orientation: Gradient.Horizontal
            GradientStop { position: 0; color: SiteStyle.primaryStart }
            GradientStop { position: 1; color: SiteStyle.primaryEnd }
        }
        Text {
            anchors.fill: parent; anchors.margins: 8
            verticalAlignment: Text.AlignVCenter; horizontalAlignment: button.textAlignment
            text: button.text; elide: Text.ElideRight
            color: button.primary ? SiteStyle.primaryInk : button.foreground
            font.family: button.icon ? SiteStyle.mono : button.primary ? SiteStyle.carved : SiteStyle.mono
            font.pixelSize: button.icon ? 20 : 13
            font.capitalization: button.primary ? Font.AllUppercase : Font.MixedCase
            font.letterSpacing: button.primary ? 1.3 : 0
        }
        Keys.onReturnPressed: if (enabled) clicked()
        Keys.onEnterPressed: if (enabled) clicked()
        Keys.onSpacePressed: if (enabled) clicked()
        MouseArea { id: hover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: { button.forceActiveFocus(); button.clicked(); }
        }
    }
    component Pill: Rectangle {
        property string text: ""
        property bool current: false
        implicitWidth: pillLabel.implicitWidth + 16; height: 22
        radius: 11
        color: SiteStyle.night
        border.width: 1; border.color: current ? catalog.accent : SiteStyle.lineStrong
        Label { id: pillLabel; anchors.centerIn: parent; text: parent.text; font.family: SiteStyle.carved; font.capitalization: Font.AllUppercase; font.letterSpacing: 1; font.pixelSize: 11; color: parent.current ? catalog.accent : SiteStyle.muted }
    }
    component Preview: Rectangle {
        property string source: ""
        property bool iconOnly: false
        property bool plugin: false
        radius: 4
        color: SiteStyle.raised
        Image {
            anchors.centerIn: parent; width: parent.iconOnly ? 64 : parent.width; height: parent.iconOnly ? 64 : parent.height
            source: parent.source; fillMode: parent.iconOnly ? Image.PreserveAspectFit : Image.PreserveAspectCrop
            sourceSize: parent.iconOnly ? Qt.size(128, 128) : Qt.size(640, 360); asynchronous: true
            layer.enabled: GraphicsInfo.api !== GraphicsInfo.Software
            layer.effect: MultiEffect { maskEnabled: true; maskSource: imageMask }
        }
        Label { anchors.centerIn: parent; visible: parent.plugin && !parent.source; text: "󰏗"; font.pixelSize: 48; color: SiteStyle.muted }
        Item { id: imageMask; anchors.fill: parent; layer.enabled: true; visible: false
            Rectangle { anchors.fill: parent; radius: parent.parent.radius; color: "white" }
        }
    }
    component CatalogCard: Rectangle {
        id: tile
        required property var item
        required property bool local
        readonly property bool picked: catalog.getMore && !local && catalog.selected.includes(item.id)
        readonly property bool focused: catalog.cursor >= 0 && !!catalog.navigable[catalog.cursor] && catalog.navigable[catalog.cursor].id === item.id
        readonly property real viewportY: parent.parent.y + parent.y + y - scroll.contentY
        readonly property bool inViewport: viewportY + height > 0 && viewportY < scroll.height
        implicitHeight: details.y + details.height + 12
        opacity: item.hidden ? 0.55 : 1
        radius: 4
        color: SiteStyle.surface
        border.width: 1
        border.color: picked || focused ? catalog.accent : cardMouse.containsMouse ? SiteStyle.lineStrong : SiteStyle.line
        RectangularShadow {
            anchors.fill: parent; z: -1
            visible: tile.picked || tile.focused
            radius: tile.radius; blur: 18; spread: 2; color: SiteStyle.glow
        }
        onFocusedChanged: {
            if (!focused) return;
            const top = mapToItem(scroll, 0, 0).y;
            if (top < 0) scroll.contentY = Math.max(0, scroll.contentY + top);
            else if (top + height > scroll.height) scroll.contentY = Math.min(scroll.contentHeight - scroll.height, scroll.contentY + top + height - scroll.height);
        }
        onInViewportChanged: if (inViewport && !local) catalog.preview(item)
        Component.onCompleted: if (inViewport && !local) catalog.preview(item)
        Preview { id: art; x: 2; y: 2; width: parent.width - 4; height: width * 9 / 16; source: catalog.imageFor(tile.item); plugin: catalog.kind === "plugins"; iconOnly: plugin && !tile.item.preview && !(tile.item.previewUrl && !tile.item.icon) }
        Column {
            id: details
            z: 1
            x: 12; y: art.y + art.height + 10; width: parent.width - 24; spacing: 5
            Label { width: parent.width; text: tile.item.name || ""; font.family: SiteStyle.carved; font.weight: Font.Medium; font.letterSpacing: 0.7; maximumLineCount: 1; elide: Text.ElideRight }
            Label { width: parent.width; text: tile.item.description || (catalog.kind === "themes" ? Eitr.I18n.tr("Desktop theme") : ""); font.pixelSize: 13; color: SiteStyle.muted; maximumLineCount: 1; elide: Text.ElideRight }
            Row { spacing: 4; visible: catalog.kind === "themes"
                Repeater {
                    model: catalog.kind === "themes" && tile.item.palette ? ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"] : []
                    Rectangle { required property string modelData; width: 14; height: 14; radius: 7; color: tile.item.palette[modelData]; border.width: 1; border.color: SiteStyle.lineStrong }
                }
            }
            Flow { width: parent.width; spacing: 6
                Pill { text: catalog.badge(tile.item) }
                Pill { visible: catalog.kind === "plugins" && tile.local && catalog.getMore; text: Eitr.I18n.tr("Installed") }
                Pill { visible: catalog.kind === "plugins" && tile.item.enabled === false; text: Eitr.I18n.tr("Disabled") }
                Pill { visible: !!tile.item.hidden; text: Eitr.I18n.tr("Hidden") }
                Pill { visible: !!tile.item.current; current: true; text: Eitr.I18n.tr("Current") }
            }
            Item {
                width: parent.width
                height: 32
                visible: !!tile.item.hidden || (catalog.updates[tile.item.id] || 0) > 0
                SiteButton {
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    width: 86; foreground: catalog.foreground
                    visible: !!tile.item.hidden
                    text: Eitr.I18n.tr("Restore")
                    onClicked: catalog.act("unhide", {id: tile.item.id})
                }
                Pill {
                    anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                    visible: !tile.item.hidden && (catalog.updates[tile.item.id] || 0) > 0; text: Eitr.I18n.tr("Update"); current: true
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { if (catalog.kind === "themes") catalog.act("update", {id: tile.item.id}); else catalog.progress = catalog.pluginNote; } }
                }
            }
        }
        MouseArea { id: cardMouse; anchors.fill: parent; hoverEnabled: true; enabled: !catalog.busy && !catalog.reviewing && !catalog.removing
            cursorShape: Qt.PointingHandCursor
            onClicked: { catalog.cursor = catalog.navigable.findIndex(theme => theme.id === tile.item.id); catalog.activate(tile.item, tile.local); }
        }
        Rectangle {
            visible: tile.picked; x: 10; y: 10; width: 30; height: 30; radius: 15; color: catalog.accent
            Label { anchors.centerIn: parent; text: "\uF00C"; color: PanelStyle.readableInk(catalog.accent, catalog.foreground, catalog.background); font.pixelSize: 18 }
        }
        SiteButton {
            id: removeButton
            anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
            width: 28; height: 28; icon: true; text: "󰆴"; foreground: SiteStyle.fg
            color: SiteStyle.night
            visible: catalog.tab === "installed" && tile.local && !tile.item.current && tile.item.id !== "eitr" && tile.item.kind !== "own" && !tile.item.hidden
            Accessible.name: Eitr.I18n.tr("Remove %1").arg(tile.item.name || "")
            onClicked: { catalog.removing = tile.item; catalog.forceActiveFocus(); }
            // Built-in themes cannot be deleted; removing one hides it.
            BarTooltip { target: removeButton; hovered: removeButton.hovered; text: tile.item.kind === "builtin" ? Eitr.I18n.tr("Hide") : Eitr.I18n.tr("Delete"); foreground: SiteStyle.fg; background: SiteStyle.raised }
        }

    }
    Item {
        id: sidebar
        width: catalog.sidebarWidth; height: parent.height
        enabled: !catalog.reviewing && !catalog.removing
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: SiteStyle.line }
        Label {
            id: windowTitle
            x: 18; y: 22; width: parent.width - 36
            text: catalog.compact ? "󰏘" : Eitr.I18n.tr("Themes & Plugins")
            font.family: catalog.compact ? SiteStyle.mono : SiteStyle.serif; font.weight: Font.Medium; font.pixelSize: 22
            horizontalAlignment: catalog.compact ? Text.AlignHCenter : Text.AlignLeft
        }
        Column {
            x: 10; y: Math.max(72, windowTitle.y + windowTitle.height + 18); width: parent.width - 20; spacing: 6
            Repeater {
                model: ["themes", "plugins"]
                Rectangle {
                    id: navigationRow
                    required property int index
                    required property string modelData
                    readonly property bool selected: catalog.navigationIndex === index
                    width: parent.width; height: 40
                    radius: 3
                    color: selected ? SiteStyle.raised : navigationMouse.containsMouse ? SiteStyle.surface : SiteStyle.night
                    border.width: 1; border.color: selected ? catalog.accent : SiteStyle.line
                    Label { x: 10; anchors.verticalCenter: parent.verticalCenter; text: navigationRow.modelData === "themes" ? "󰏘" : "󰏗"; font.pixelSize: 18 }
                    Label { visible: !catalog.compact; x: 42; anchors.verticalCenter: parent.verticalCenter; text: navigationRow.modelData === "themes" ? Eitr.I18n.tr("Themes") : Eitr.I18n.tr("Plugins"); font.family: SiteStyle.carved; font.capitalization: Font.AllUppercase; font.letterSpacing: 1 }
                    Label { visible: !catalog.compact; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; color: SiteStyle.muted; text: (catalog.counts[navigationRow.modelData] || {}).installed || "" }
                    MouseArea { id: navigationMouse; cursorShape: Qt.PointingHandCursor; anchors.fill: parent; hoverEnabled: true; enabled: !catalog.busy; onClicked: catalog.navigate(navigationRow.index) }
                }
            }
        }
    }

    SiteButton { z: 1; anchors.right: parent.right; anchors.top: parent.top; anchors.topMargin: 5; anchors.rightMargin: 8; width: 34; height: 34; text: "󰅖"; icon: true; foreground: catalog.foreground; Accessible.name: Eitr.I18n.tr("Close catalog"); onClicked: catalog.closeRequested() }
    // Source tabs like browser tabs: the strip is tinted and the selected tab
    // is cut out of it, joining the page below with curved feet.
    Item {
        id: sourceTabs
        x: catalog.sidebarWidth; width: catalog.width - x; height: 44
        readonly property real tabTop: 8
        readonly property real round: 8
        readonly property real start: PanelStyle.padding
        readonly property real tabWidth: Math.max(catalog.compact ? 108 : 140, Math.ceil(tabLabelWidth) + 36)
        readonly property real tabLabelWidth: Math.max(installedMetrics.labelWidth, officialMetrics.labelWidth, communityMetrics.labelWidth)
        component TabMetrics: Text {
            readonly property real labelWidth: implicitWidth
            visible: false
            font.family: SiteStyle.carved; font.capitalization: Font.AllUppercase; font.letterSpacing: 1.5; font.weight: Font.Bold; font.pixelSize: PanelStyle.bodySize
        }
        TabMetrics { id: installedMetrics; text: Eitr.I18n.tr("Installed") }
        TabMetrics { id: officialMetrics; text: Eitr.I18n.tr("Official") }
        TabMetrics { id: communityMetrics; text: Eitr.I18n.tr("Community") }
        readonly property var tabs: ["installed", "official", "community"]
        readonly property int selectedIndex: tabs.indexOf(catalog.tab)
        property int hoveredIndex: -1
        Shape {
            anchors.fill: parent; antialiasing: true
            ShapePath {
                strokeWidth: -1
                fillColor: SiteStyle.night
                PathSvg { path: {
                    const width = sourceTabs.width, height = sourceTabs.height, round = sourceTabs.round, top = sourceTabs.tabTop;
                    const corner = 4;
                    const from = sourceTabs.start + sourceTabs.selectedIndex * sourceTabs.tabWidth, to = from + sourceTabs.tabWidth;
                    let path = "M 0 0 L " + (width - corner) + " 0 Q " + width + " 0 " + width + " " + corner + " L " + width + " " + height;
                    if (sourceTabs.selectedIndex >= 0)
                        path += " L " + (to + round) + " " + height + " Q " + to + " " + height + " " + to + " " + (height - round)
                            + " L " + to + " " + (top + round) + " Q " + to + " " + top + " " + (to - round) + " " + top
                            + " L " + (from + round) + " " + top + " Q " + from + " " + top + " " + from + " " + (top + round)
                            + " L " + from + " " + (height - round) + " Q " + from + " " + height + " " + (from - round) + " " + height;
                    return path + " L 0 " + height + " Z";
                } }
            }
        }
        Repeater {
            id: tabRepeater
            model: sourceTabs.tabs
            Item {
                id: sourceTab
                required property string modelData
                required property int index
                readonly property bool selected: catalog.tab === modelData
                readonly property bool hovered: sourceTabs.hoveredIndex === index
                readonly property string label: ({official:Eitr.I18n.tr("Official"), community:Eitr.I18n.tr("Community"), installed:Eitr.I18n.tr("Installed")})[modelData]
                objectName: "sourceTab-" + modelData
                x: sourceTabs.start + index * sourceTabs.tabWidth; y: sourceTabs.tabTop
                width: sourceTabs.tabWidth; height: sourceTabs.height - sourceTabs.tabTop
                Rectangle {
                    visible: sourceTab.hovered && !sourceTab.selected
                    anchors { fill: parent; topMargin: 2; bottomMargin: 6; leftMargin: 4; rightMargin: 4 }
                    radius: sourceTabs.round; color: SiteStyle.raised
                }
                // Dividers sit only between two unselected, unhovered tabs.
                Rectangle {
                    visible: sourceTab.index < sourceTabs.tabs.length - 1
                        && ![sourceTab.index, sourceTab.index + 1].some(index => index === sourceTabs.selectedIndex || index === sourceTabs.hoveredIndex)
                    x: parent.width - 0.5; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -2
                    width: 1; height: 16; color: SiteStyle.lineStrong
                }
                Label {
                    anchors.centerIn: parent; anchors.verticalCenterOffset: -2; wrapMode: Text.NoWrap
                    text: sourceTab.label
                    color: sourceTab.selected ? catalog.foreground : SiteStyle.muted
                    font.family: SiteStyle.carved; font.capitalization: Font.AllUppercase; font.letterSpacing: 1.5
                    font.weight: sourceTab.selected ? Font.Bold : Font.Medium
                    opacity: sourceTab.selected ? 1 : PanelStyle.secondaryTextOpacity
                }
                MouseArea {
                    id: tabMouse
                    anchors.fill: parent
                    hoverEnabled: true; enabled: !catalog.busy && !catalog.reviewing && !catalog.removing
                    cursorShape: Qt.PointingHandCursor
                    Accessible.role: Accessible.PageTab; Accessible.name: sourceTab.label
                    onContainsMouseChanged: if (containsMouse) sourceTabs.hoveredIndex = sourceTab.index; else if (sourceTabs.hoveredIndex === sourceTab.index) sourceTabs.hoveredIndex = -1
                    onClicked: catalog.tab = sourceTab.modelData
                }
            }
        }
    }
    Column {
        id: contentLayout
        enabled: !catalog.reviewing && !catalog.removing
        x: catalog.sidebarWidth + PanelStyle.padding; y: sourceTabs.height + 14
        width: catalog.width - x - PanelStyle.padding; spacing: 12
        Item {
            width: parent.width; height: 36
            visible: catalog.kind === "themes" || catalog.tab === "installed"
            // All themes by default; Sun or Moon shows only that mode, a second click all again.
            Row { anchors.right: parent.right; spacing: PanelStyle.selectionRowGap; visible: catalog.kind === "themes"
                Repeater { model: [{tone: "light", glyph: "󰖙", label: Eitr.I18n.tr("Light")}, {tone: "dark", glyph: "󰖔", label: Eitr.I18n.tr("Dark")}]
                    SiteButton {
                        required property var modelData
                        width: PanelStyle.selectionRowHeight; height: PanelStyle.selectionRowHeight
                        icon: true; text: modelData.glyph; foreground: catalog.foreground
                        selected: catalog.tone === modelData.tone; available: !catalog.busy
                        Accessible.name: modelData.label
                        activeFocusOnTab: false
                        onClicked: { catalog.tone = catalog.tone === modelData.tone ? "all" : modelData.tone; catalog.cursor = -1; catalog.forceActiveFocus(); }
                    }
                }
            }
            Row { spacing: 12; visible: catalog.tab === "installed"
                Item {
                    id: addAddress; width: 228; height: 32
                    SiteButton { anchors.fill: parent; available: false; text: Eitr.I18n.tr("Add from a Git address"); foreground: catalog.foreground }
                    MouseArea { id: addHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                    BarTooltip { target: addAddress; hovered: addHover.containsMouse; text: Eitr.I18n.tr("Coming soon"); foreground: catalog.foreground; background: catalog.background }
                }
                SiteButton { width: 136; visible: catalog.kind === "themes"; selected: catalog.showHidden; text: Eitr.I18n.tr("Show hidden"); foreground: catalog.foreground; activeFocusOnTab: false; onClicked: { catalog.showHidden = !catalog.showHidden; catalog.forceActiveFocus(); } }
            }
        }
        Label { width: parent.width; visible: text !== ""; text: (!catalog.reviewing && !catalog.removing ? catalog.error || catalog.progress : "") || (catalog.loading ? Eitr.I18n.tr("Loading…") : ""); Accessible.role: Accessible.AlertMessage }
        Flickable {
            id: scroll
            width: parent.width; height: Math.max(1, catalog.height - contentLayout.y - y - PanelStyle.padding - (selectionBar.visible ? selectionBar.height + 12 : 0))
            contentWidth: width; contentHeight: sections.height; clip: true; boundsBehavior: Flickable.StopAtBounds
            function more() { if (contentY + height > contentHeight - 600 && catalog.shown < catalog.navigable.length) catalog.shown += catalog.pageSize; }
            onContentYChanged: more()
            onContentHeightChanged: Qt.callLater(more)
            onHeightChanged: Qt.callLater(more)
            ScrollBar.vertical: ScrollBar {}
            Column {
                id: sections; width: scroll.width - 12; spacing: 14
                Repeater {
                    model: [{local: !catalog.getMore}]
                    Column {
                        id: section
                        required property var modelData
                        readonly property string pageError: modelData.local ? catalog.installedError : catalog.tab === "official" && catalog.discoveries.length ? "" : catalog.repositoryError
                        readonly property var items: pageError ? [] : modelData.local ? catalog.locals : catalog.discoveries
                        width: sections.width; spacing: 12
                        GridLayout {
                            columns: catalog.columns; columnSpacing: 14; rowSpacing: 14
                            Repeater { model: section.items.slice(0, catalog.shown)
                                CatalogCard { required property var modelData; item: modelData; local: catalog.isInstalled(modelData); Layout.preferredWidth: (section.width - 14 * (catalog.columns - 1)) / catalog.columns; Layout.fillHeight: true }
                            }
                        }
                        Item {
                            visible: !section.items.length
                            width: parent.width; height: scroll.height
                            Column { anchors.centerIn: parent; width: parent.width - 40; spacing: 14
                                Label { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: section.pageError || (section.modelData.local ? Eitr.I18n.tr("No installed items match this filter.") : Eitr.I18n.tr("No themes available. Try again shortly.")); color: SiteStyle.muted }
                                SiteButton { anchors.horizontalCenter: parent.horizontalCenter; visible: !section.modelData.local || catalog.installedError !== ""; width: 90; text: Eitr.I18n.tr("Retry"); foreground: catalog.foreground; onClicked: { catalog.previewRequests = ({}); if (section.modelData.local) catalog.refreshInstalled(); else catalog.refreshIndex(); } }
                            }
                        }
                    }
                }
            }
        }
        Rectangle {
            id: selectionBar; visible: catalog.getMore && catalog.chosen.length > 0 && catalog.kind === "themes"; width: parent.width; height: 48
            radius: 3; color: SiteStyle.raised
            SiteButton { x: 8; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 108; primary: true; textAlignment: Text.AlignLeft; flat: true; text: catalog.chosen.length === 1 ? Eitr.I18n.tr("Install 1 theme · %1").arg(catalog.sizeText(catalog.totalSize)) : Eitr.I18n.tr("Install %1 themes · %2").arg(catalog.chosen.length).arg(catalog.sizeText(catalog.totalSize)); foreground: catalog.foreground; onClicked: { catalog.reviewing = true; catalog.forceActiveFocus(); } }
            SiteButton { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 80; flat: true; text: Eitr.I18n.tr("Clear"); foreground: catalog.foreground; onClicked: catalog.selected = [] }
        }
    }
    Rectangle {
        anchors.fill: parent; visible: catalog.reviewing || catalog.removing !== null
        color: SiteStyle.night; radius: 4
        MouseArea { anchors.fill: parent }
        Rectangle {
            anchors.centerIn: parent; width: parent.width - 72; height: 420
            radius: 4; color: SiteStyle.surface
            border.width: 1; border.color: SiteStyle.line
            Column {
                anchors.fill: parent; anchors.margins: 24; spacing: 18
                Label { width: parent.width; font.family: SiteStyle.carved; font.pixelSize: PanelStyle.headingSize; font.weight: Font.Medium; text: catalog.reviewing ? Eitr.I18n.tr("Review theme installation") : Eitr.I18n.tr("Remove %1?").arg(catalog.removing ? catalog.removing.name : "") }
                Label { width: parent.width; text: catalog.reviewing ? Eitr.I18n.tr("Data-only themes · Review selected sources") : Eitr.I18n.tr("Built-in themes are hidden and can be restored with Show hidden. Other installed themes are removed."); color: SiteStyle.muted }
                ListView {
                    width: parent.width; height: 190; orientation: ListView.Horizontal; spacing: 12; clip: true
                    model: catalog.reviewing ? catalog.chosen : []; boundsBehavior: Flickable.StopAtBounds
                    delegate: Column { required property var modelData; width: 200; spacing: 8
                        Preview { width: 200; height: 112; source: catalog.imageFor(parent.modelData) }
                        Label { width: parent.width; text: parent.modelData.repository || "eitr-org/eitr-themes"; font.pixelSize: 11; elide: Text.ElideMiddle }
                        Label { width: parent.width; text: parent.modelData.name; maximumLineCount: 1; elide: Text.ElideRight; font.bold: true }
                        Label { text: catalog.sizeText(parent.modelData.size || 0); font.pixelSize: PanelStyle.captionSize; color: SiteStyle.muted }
                    }
                }
                Label { text: catalog.busy ? catalog.progress : catalog.error || (catalog.reviewing ? Eitr.I18n.tr("Total download: %1").arg(catalog.sizeText(catalog.totalSize)) : ""); width: parent.width }
                ProgressBar { width: parent.width; height: 6; visible: catalog.busy; indeterminate: true; palette.highlight: catalog.accent; palette.base: Qt.alpha(catalog.foreground, 0.08) }
            }
            Row {
                anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24; spacing: 8
                SiteButton { width: 100; available: !catalog.busy; text: Eitr.I18n.tr("Cancel"); foreground: catalog.foreground; onClicked: catalog.cancelSheet() }
                SiteButton { width: 100; available: !catalog.busy; primary: true; text: catalog.reviewing ? Eitr.I18n.tr("Install") : Eitr.I18n.tr("Remove"); foreground: catalog.foreground; onClicked: catalog.confirm() }
            }
        }
    }
}
