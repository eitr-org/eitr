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
    required property color foreground
    required property color background
    required property color accent
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
    readonly property int columns: Math.max(1, Math.min(3, Math.floor((width - sidebarWidth - 48) / 250)))
    function filtered(items) { return kind !== "themes" ? items : items.filter(item => tone === "all" || item.light === (tone === "light")); }
    readonly property var locals: filtered(installed.filter(item => showHidden || !item.hidden))
    readonly property var discoveries: filtered(tab === "community" ? availableItems.map(item => Object.assign({}, item, installed.find(local => local.id === item.id) || {}, {kind: "community"})) : installed.filter(item => !item.hidden && ["builtin", "official"].includes(item.kind)).concat(more.map(item => Object.assign({kind: "official"}, item))))
    readonly property var navigable: getMore ? discoveries : locals
    function toggle(item) {
        if (kind !== "themes" || busy) return;
        selected = selected.includes(item.id) ? selected.filter(themeId => themeId !== item.id) : selected.concat([item.id]);
    }
    function isInstalled(item) { return installed.some(local => local.id === item.id); }
    function activate(item, local) {
        if (item.hidden) return;
        if (busy) return;
        if (local && kind === "themes" && !item.current) act("apply", {id: item.id});
        else if (!local) toggle(item);
        sidebarFocus = false; forceActiveFocus();
    }
    function imageFor(item) { return item.previewUrl || previews[item.id] || ""; }
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
    function refreshInstalled() {
        installedError = "";
        loading = true;
        request("installed", {}, function(failure, data) {
            loading = false;
            installedError = failure;
            if (!failure) installed = data.items || [];
        });
    }
    function refreshIndex() {
        repositoryError = "";
        if (tab === "installed") return;
        request("index", {}, function(failure, data) {
            repositoryError = failure;
            if (!failure) { availableItems = data.items || []; indexLoaded = true; }
        });
    }
    function load() {
        generation++;
        indexLoaded = false;
        installed = []; availableItems = []; selected = []; updates = updateCache[kind] || ({}); previews = ({}); previewRequests = ({});
        reviewing = false; removing = null; busy = false; error = ""; repositoryError = ""; installedError = ""; progress = "";
        if (live && opened) {
            refreshInstalled(); refreshIndex();
            const other = kind === "themes" ? "plugins" : "themes";
            request("installed", {kind: other}, function(failure, data) {
                if (!failure) counts = Object.assign({}, counts, {[other]: Object.assign({}, counts[other] || {}, {installed: (data.items || []).length})});
            });
        }
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
        if (!live || !opened || kind !== "themes" || previews[item.id] || previewRequests[item.id]) return;
        previewRequests = Object.assign({}, previewRequests, {[item.id]: true});
        request("preview", {id: item.id}, function(failure, data) {
            if (!failure) previews = Object.assign({}, previews, {[item.id]: data.image});
        });
    }
    function cancelSheet() { if (!busy) { reviewing = false; removing = null; } }
    function confirm() {
        if (busy) return;
        if (reviewing) act("install", {ids: chosen.map(item => item.id)});
        else if (removing) act("remove", {id: removing.id});
    }
    onTabChanged: { cursor = -1; scroll.contentY = 0; DesktopData.releaseOwner(catalog); load(); }
    onKindChanged: { DesktopData.releaseOwner(catalog); load(); }
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
            } else if (event.key === Qt.Key_Left && (cursor < 0 || cursor % (kind === "themes" ? columns : 1) === 0)) {
                sidebarFocus = true; cursor = -1; event.accepted = true; return;
            }
            const count = navigable.length;
            let delta = 0;
            if (event.key === Qt.Key_Right) delta = 1;
            if (event.key === Qt.Key_Left) delta = -1;
            if (event.key === Qt.Key_Down) delta = kind === "themes" ? columns : 1;
            if (event.key === Qt.Key_Up) delta = kind === "themes" ? -columns : -1;
            if (delta && count) { cursor = Math.max(0, Math.min(count - 1, cursor < 0 ? 0 : cursor + delta)); event.accepted = true; }
            else if (event.key === Qt.Key_Space && getMore && cursor >= 0 && cursor < count) { toggle(navigable[cursor]); event.accepted = true; }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                if (chosen.length) reviewing = true;
                else if (cursor >= 0 && cursor < count) activate(navigable[cursor], isInstalled(navigable[cursor]));
                event.accepted = true;
            }
        }
    }
    component Label: Text {
        color: catalog.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.bodySize
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
    component Pill: Rectangle {
        property string text: ""
        property bool current: false
        implicitWidth: pillLabel.implicitWidth + 16; height: 22
        radius: 11
        color: Qt.alpha(catalog.foreground, current ? 0.18 : 0.08)
        Label { id: pillLabel; anchors.centerIn: parent; text: parent.text; font.pixelSize: PanelStyle.captionSize; font.bold: parent.current }
    }
    component Preview: Rectangle {
        property string source: ""
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        color: Qt.alpha(catalog.foreground, 0.08)
        Image {
            anchors.fill: parent; source: parent.source; fillMode: Image.PreserveAspectCrop
            sourceSize: Qt.size(640, 360); asynchronous: true
            layer.enabled: GraphicsInfo.api !== GraphicsInfo.Software
            layer.effect: MultiEffect { maskEnabled: true; maskSource: imageMask }
        }
        Item { id: imageMask; anchors.fill: parent; layer.enabled: true; visible: false
            Rectangle { anchors.fill: parent; radius: parent.parent.radius; color: "white" }
        }
    }
    component ThemeCard: Rectangle {
        id: tile
        required property var item
        required property bool local
        readonly property bool picked: catalog.getMore && !local && catalog.selected.includes(item.id)
        readonly property bool focused: catalog.cursor >= 0 && !!catalog.navigable[catalog.cursor] && catalog.navigable[catalog.cursor].id === item.id
        readonly property real viewportY: parent.parent.y + parent.y + y - scroll.contentY
        readonly property bool inViewport: viewportY + height > 0 && viewportY < scroll.height
        implicitHeight: details.y + details.height + 12
        opacity: item.hidden ? 0.55 : 1
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(item.current || picked, cardMouse.containsMouse))
        border.width: picked || focused ? 2 : 1
        border.color: picked || focused ? catalog.accent : Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
        onFocusedChanged: {
            if (!focused) return;
            const top = mapToItem(scroll, 0, 0).y;
            if (top < 0) scroll.contentY = Math.max(0, scroll.contentY + top);
            else if (top + height > scroll.height) scroll.contentY = Math.min(scroll.contentHeight - scroll.height, scroll.contentY + top + height - scroll.height);
        }
        onInViewportChanged: if (inViewport && !local) catalog.preview(item)
        Component.onCompleted: if (inViewport && !local) catalog.preview(item)
        Preview { id: art; x: 2; y: 2; width: parent.width - 4; height: width * 9 / 16; source: catalog.imageFor(tile.item) }
        Column {
            id: details
            z: 1
            x: 12; y: art.y + art.height + 10; width: parent.width - 24; spacing: 5
            Label { width: parent.width; text: tile.item.name || ""; font.bold: true; maximumLineCount: 1; elide: Text.ElideRight }
            Label { width: parent.width; text: tile.item.description || Eitr.I18n.tr("Desktop theme"); font.pixelSize: PanelStyle.captionSize; opacity: PanelStyle.secondaryTextOpacity; maximumLineCount: 1; elide: Text.ElideRight }
            Row { spacing: 4
                Repeater {
                    model: tile.item.palette ? ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"] : []
                    Rectangle { required property string modelData; width: 14; height: 14; radius: 7; color: tile.item.palette[modelData]; border.width: 1; border.color: Qt.alpha(catalog.foreground, 0.2) }
                }
            }
            Row { spacing: 6
                Pill { text: catalog.badge(tile.item) }
                Pill { visible: !!tile.item.hidden; text: Eitr.I18n.tr("Hidden") }
                Pill { visible: !!tile.item.current; current: true; text: Eitr.I18n.tr("Current") }
            }
            Item {
                width: parent.width
                height: 32
                visible: !!tile.item.hidden || (catalog.updates[tile.item.id] || 0) > 0
                PanelButton {
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    width: 86; foreground: catalog.foreground
                    visible: !!tile.item.hidden
                    text: Eitr.I18n.tr("Restore")
                    onClicked: catalog.act("unhide", {id: tile.item.id})
                }
                Pill {
                    anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                    visible: !tile.item.hidden && (catalog.updates[tile.item.id] || 0) > 0; text: Eitr.I18n.tr("Update"); current: true
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catalog.act("update", {id: tile.item.id}) }
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
        PanelButton {
            anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
            width: 28; height: 28; icon: true; text: "󰆴"; foreground: catalog.foreground
            color: catalog.background
            visible: catalog.tab === "installed" && tile.local && !tile.item.current && tile.item.id !== "eitr" && tile.item.kind !== "own" && !tile.item.hidden
            Accessible.name: Eitr.I18n.tr("Remove %1").arg(tile.item.name || "")
            onClicked: { catalog.removing = tile.item; catalog.forceActiveFocus(); }
        }

    }
    Item {
        id: sidebar
        width: catalog.sidebarWidth; height: parent.height
        enabled: !catalog.reviewing && !catalog.removing
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Qt.alpha(catalog.foreground, PanelStyle.dividerAlpha) }
        Label {
            x: 18; y: 24; width: parent.width - 36
            text: catalog.compact ? "󰏘" : Eitr.I18n.tr("Themes & Plugins")
            font.bold: true; font.pixelSize: catalog.compact ? 22 : PanelStyle.bodySize
            horizontalAlignment: catalog.compact ? Text.AlignHCenter : Text.AlignLeft
        }
        Column {
            x: 10; y: 88; width: parent.width - 20; spacing: 6
            Repeater {
                model: ["themes", "plugins"]
                Rectangle {
                    id: navigationRow
                    required property int index
                    required property string modelData
                    readonly property bool selected: catalog.navigationIndex === index
                    width: parent.width; height: 40
                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                    color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(selected, navigationMouse.containsMouse))
                    Label { x: 10; anchors.verticalCenter: parent.verticalCenter; text: navigationRow.modelData === "themes" ? "󰏘" : "󰏗"; font.pixelSize: 18 }
                    Label { visible: !catalog.compact; x: 42; anchors.verticalCenter: parent.verticalCenter; text: navigationRow.modelData === "themes" ? Eitr.I18n.tr("Themes") : Eitr.I18n.tr("Plugins") }
                    Label { visible: !catalog.compact; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; opacity: PanelStyle.secondaryTextOpacity; text: (catalog.counts[navigationRow.modelData] || {}).installed || "" }
                    MouseArea { id: navigationMouse; cursorShape: Qt.PointingHandCursor; anchors.fill: parent; hoverEnabled: true; enabled: !catalog.busy; onClicked: catalog.navigate(navigationRow.index) }
                }
            }
        }
    }

    PanelButton { z: 1; anchors.right: parent.right; anchors.top: parent.top; anchors.topMargin: 5; anchors.rightMargin: 8; width: 34; height: 34; text: "󰅖"; icon: true; foreground: catalog.foreground; Accessible.name: Eitr.I18n.tr("Close catalog"); onClicked: catalog.closeRequested() }
    // Source tabs like browser tabs: the strip is tinted and the selected tab
    // is cut out of it, joining the page below with curved feet.
    Item {
        id: sourceTabs
        x: catalog.sidebarWidth; width: catalog.width - x; height: 44
        readonly property real tabTop: 8
        readonly property real round: 8
        readonly property real start: PanelStyle.padding
        readonly property real tabWidth: catalog.compact ? 108 : 140
        readonly property var tabs: ["official", "community", "installed"]
        readonly property int selectedIndex: tabs.indexOf(catalog.tab)
        property int hoveredIndex: -1
        Shape {
            anchors.fill: parent; antialiasing: true
            ShapePath {
                strokeWidth: -1
                fillColor: Qt.alpha(catalog.foreground, 0.06)
                PathSvg { path: {
                    const width = sourceTabs.width, height = sourceTabs.height, round = sourceTabs.round, top = sourceTabs.tabTop;
                    const corner = DesktopStyle.radius(PanelStyle.cornerRadius);
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
                    radius: sourceTabs.round; color: Qt.alpha(catalog.foreground, 0.08)
                }
                // Dividers sit only between two unselected, unhovered tabs.
                Rectangle {
                    visible: sourceTab.index < sourceTabs.tabs.length - 1
                        && ![sourceTab.index, sourceTab.index + 1].some(index => index === sourceTabs.selectedIndex || index === sourceTabs.hoveredIndex)
                    x: parent.width - 0.5; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -2
                    width: 1; height: 16; color: Qt.alpha(catalog.foreground, 0.2)
                }
                Label {
                    anchors.centerIn: parent; anchors.verticalCenterOffset: -2; wrapMode: Text.NoWrap
                    text: sourceTab.label
                    font.bold: sourceTab.selected
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
                    PanelButton {
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
                    PanelButton { anchors.fill: parent; available: false; text: Eitr.I18n.tr("Add from a Git address"); foreground: catalog.foreground }
                    MouseArea { id: addHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                    BarTooltip { target: addAddress; hovered: addHover.containsMouse; text: Eitr.I18n.tr("Coming soon"); foreground: catalog.foreground; background: catalog.background }
                }
                PanelButton { width: 136; visible: catalog.kind === "themes"; selected: catalog.showHidden; text: Eitr.I18n.tr("Show hidden"); foreground: catalog.foreground; activeFocusOnTab: false; onClicked: { catalog.showHidden = !catalog.showHidden; catalog.forceActiveFocus(); } }
            }
        }
        Label { width: parent.width; visible: text !== ""; text: (!catalog.reviewing && !catalog.removing ? catalog.error || catalog.progress : "") || (catalog.loading ? Eitr.I18n.tr("Loading…") : ""); Accessible.role: Accessible.AlertMessage }
        Flickable {
            id: scroll
            width: parent.width; height: Math.max(1, catalog.height - contentLayout.y - y - PanelStyle.padding - (selectionBar.visible ? selectionBar.height + 12 : 0))
            contentWidth: width; contentHeight: sections.height; clip: true; boundsBehavior: Flickable.StopAtBounds
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
                            visible: catalog.kind === "themes"; columns: catalog.columns; columnSpacing: 14; rowSpacing: 14
                            Repeater { model: catalog.kind === "themes" ? section.items : []
                                ThemeCard { required property var modelData; item: modelData; local: catalog.isInstalled(modelData); Layout.preferredWidth: (section.width - 14 * (catalog.columns - 1)) / catalog.columns; Layout.fillHeight: true }
                            }
                        }
                        Column {
                            width: parent.width; spacing: PanelStyle.selectionRowGap; visible: catalog.kind === "plugins"
                            Repeater { model: catalog.kind === "plugins" ? section.items : []
                                Rectangle {
                                    id: pluginRow; required property var modelData
                                    width: section.width; height: PanelStyle.selectionRowHeight
                                    radius: DesktopStyle.radius(PanelStyle.controlRadius)
                                    color: Qt.alpha(catalog.foreground, PanelStyle.selectionAlpha(catalog.isInstalled(pluginRow.modelData), false))
                                    border.width: PanelStyle.selectionBorderWidth(catalog.isInstalled(pluginRow.modelData)); border.color: Qt.alpha(catalog.foreground, PanelStyle.selectionBorderAlpha)
                                    Label { x: PanelStyle.selectionInset; anchors.verticalCenter: parent.verticalCenter; text: catalog.isInstalled(pluginRow.modelData) ? "\uF00C" : "󰏗"; font.pixelSize: PanelStyle.selectionIconSize }
                                    Column { x: PanelStyle.selectionTextInset; anchors.verticalCenter: parent.verticalCenter; width: parent.width - x - pluginBadge.width - 54; spacing: PanelStyle.selectionDetailGap
                                        Label { width: parent.width; text: pluginRow.modelData.name || ""; font.pixelSize: PanelStyle.bodySize; maximumLineCount: 1; elide: Text.ElideRight }
                                        Label { width: parent.width; text: pluginRow.modelData.description || ""; font.pixelSize: 11; maximumLineCount: 1; elide: Text.ElideRight; opacity: PanelStyle.secondaryTextOpacity }
                                    }
                                    Pill { id: pluginBadge; anchors.right: removePlugin.left; anchors.rightMargin: PanelStyle.selectionActionGap; anchors.verticalCenter: parent.verticalCenter; text: catalog.badge(pluginRow.modelData) }
                                    PanelButton { id: removePlugin; anchors.right: parent.right; anchors.rightMargin: PanelStyle.selectionActionInset; anchors.verticalCenter: parent.verticalCenter; width: 24; height: 24; icon: true; text: "󰆴"; foreground: catalog.foreground; visible: section.modelData.local && ["official", "third-party", "community"].includes(pluginRow.modelData.kind); Accessible.name: Eitr.I18n.tr("Remove %1").arg(pluginRow.modelData.name || ""); onClicked: { catalog.removing = pluginRow.modelData; catalog.forceActiveFocus(); } }
                                }
                            }
                        }
                        Item {
                            visible: !section.items.length
                            width: parent.width; height: scroll.height
                            Column { anchors.centerIn: parent; width: parent.width - 40; spacing: 14
                                Label { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: section.pageError || (section.modelData.local ? Eitr.I18n.tr("No installed items match this filter.") : Eitr.I18n.tr("No themes available. Try again shortly.")); opacity: PanelStyle.secondaryTextOpacity }
                                PanelButton { anchors.horizontalCenter: parent.horizontalCenter; visible: !section.modelData.local || catalog.installedError !== ""; width: 90; text: Eitr.I18n.tr("Retry"); foreground: catalog.foreground; onClicked: { catalog.previewRequests = ({}); if (section.modelData.local) catalog.refreshInstalled(); else catalog.refreshIndex(); } }
                            }
                        }
                    }
                }
            }
        }
        Rectangle {
            id: selectionBar; visible: catalog.getMore && catalog.chosen.length > 0 && catalog.kind === "themes"; width: parent.width; height: 48
            radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(catalog.foreground, 0.08)
            PanelButton { x: 8; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 108; textAlignment: Text.AlignLeft; flat: true; text: catalog.chosen.length === 1 ? Eitr.I18n.tr("Install 1 theme · %1").arg(catalog.sizeText(catalog.totalSize)) : Eitr.I18n.tr("Install %1 themes · %2").arg(catalog.chosen.length).arg(catalog.sizeText(catalog.totalSize)); foreground: catalog.foreground; onClicked: { catalog.reviewing = true; catalog.forceActiveFocus(); } }
            PanelButton { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 80; flat: true; text: Eitr.I18n.tr("Clear"); foreground: catalog.foreground; onClicked: catalog.selected = [] }
        }
    }
    Rectangle {
        anchors.fill: parent; visible: catalog.reviewing || catalog.removing !== null
        color: Qt.alpha(catalog.background, 0.88); radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        MouseArea { anchors.fill: parent }
        Rectangle {
            anchors.centerIn: parent; width: parent.width - 72; height: 420
            radius: DesktopStyle.radius(PanelStyle.cornerRadius); color: catalog.background
            border.width: 1; border.color: Qt.alpha(catalog.foreground, PanelStyle.dividerAlpha)
            Column {
                anchors.fill: parent; anchors.margins: 24; spacing: 18
                Label { width: parent.width; font.pixelSize: PanelStyle.headingSize; font.bold: true; text: catalog.reviewing ? Eitr.I18n.tr("Review theme installation") : Eitr.I18n.tr("Remove %1?").arg(catalog.removing ? catalog.removing.name : "") }
                Label { width: parent.width; text: catalog.reviewing ? Eitr.I18n.tr("Data-only themes · Review selected sources") : Eitr.I18n.tr("Built-in themes are hidden and can be restored with Show hidden. Other installed themes are removed."); opacity: PanelStyle.secondaryTextOpacity }
                ListView {
                    width: parent.width; height: 190; orientation: ListView.Horizontal; spacing: 12; clip: true
                    model: catalog.reviewing ? catalog.chosen : []; boundsBehavior: Flickable.StopAtBounds
                    delegate: Column { required property var modelData; width: 200; spacing: 8
                        Preview { width: 200; height: 112; source: catalog.imageFor(parent.modelData) }
                        Label { width: parent.width; text: parent.modelData.repository || "eitr-org/eitr-themes"; font.pixelSize: 11; elide: Text.ElideMiddle }
                        Label { width: parent.width; text: parent.modelData.name; maximumLineCount: 1; elide: Text.ElideRight; font.bold: true }
                        Label { text: catalog.sizeText(parent.modelData.size || 0); font.pixelSize: PanelStyle.captionSize; opacity: PanelStyle.secondaryTextOpacity }
                    }
                }
                Label { text: catalog.busy ? catalog.progress : catalog.error || (catalog.reviewing ? Eitr.I18n.tr("Total download: %1").arg(catalog.sizeText(catalog.totalSize)) : ""); width: parent.width }
                ProgressBar { width: parent.width; height: 6; visible: catalog.busy; indeterminate: true; palette.highlight: catalog.accent; palette.base: Qt.alpha(catalog.foreground, 0.08) }
            }
            Row {
                anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24; spacing: 8
                PanelButton { width: 100; available: !catalog.busy; text: Eitr.I18n.tr("Cancel"); foreground: catalog.foreground; onClicked: catalog.cancelSheet() }
                PanelButton { width: 100; available: !catalog.busy; selected: true; text: catalog.reviewing ? Eitr.I18n.tr("Install") : Eitr.I18n.tr("Remove"); foreground: catalog.foreground; onClicked: catalog.confirm() }
            }
        }
    }
}
