import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import QtQuick.Shapes
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../EdgeSlopes.js" as EdgeSlopes

Item {
    id: catalog
    property color foreground: SiteStyle.fg
    property color background: SiteStyle.card
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
    property var detail: null
    property int detailGeneration: 0
    property int wallpaperIndex: -1
    property var artwork: ({})
    property var artworkRequests: ({})
    property string detailError: ""
    readonly property var detailItem: detail ? Object.assign({}, detail, installed.find(item => item.id === detail.id) || {}) : ({})
    readonly property var wallpapers: detailItem.wallpapers || []
    property var nativeReview: null
    property bool nativeReviewing: false
    property bool confirmingReview: false
    property bool addingAddress: false
    // Themes a Git address offers: chosen as cards, then reviewed together.
    property var gitSelected: []
    // Plugins chosen from one address are reviewed one after another.
    property var pluginQueue: []
    property string pluginQueueUrl: ""
    property int pluginQueueTotal: 0
    property var gitArtwork: ({})
    function gitArtworkFor(row) {
        const path = row.preview || row.icon;
        if (!live || !opened || !path || gitArtwork[row.id] !== undefined || !nativeReview) return;
        gitArtwork = Object.assign({}, gitArtwork, {[row.id]: ""});
        request("artwork", {kind: kind, channel: "git", url: nativeReview.url, id: row.id, path: path}, function(failure, data) {
            if (!failure) gitArtwork = Object.assign({}, gitArtwork, {[row.id]: data.image});
        });
    }
    function toggleGitTheme(themeId) {
        gitSelected = gitSelected.includes(themeId) ? gitSelected.filter(selectedId => selectedId !== themeId) : gitSelected.concat([themeId]);
    }
    property string advice: ""
    property string reviewSourcePath: ""
    property string reviewSourceText: ""
    property int reviewSourceOffset: 0
    property int reviewSourceTotal: 0
    function loadReviewSource(path, offset) {
        reviewSourcePath = path; reviewSourceOffset = offset;
        request("source", {token: nativeReview.token, path: path, offset: offset}, function(failure, data) {
            reviewSourceText = failure || data.text || ""; reviewSourceTotal = data.total || 0;
        });
    }
    property bool videoPosterOnly: false
    property alias videoPlayer: pluginVideo
    property int mediaIndex: 0
    readonly property var pluginMedia: (detailItem.preview ? [{type: "image", path: detailItem.preview, imageUrl: detailItem.preview.startsWith("file:") ? detailItem.preview : "", caption: ""}] : []).concat(detailItem.media || [])
    readonly property var currentMedia: pluginMedia[mediaIndex] || ({})
    function selectMedia(index) { mediaIndex = index; if (pluginMedia[index]) fetchArtwork(pluginMedia[index], false); }
    // Closing the window forgets what was in progress: sheets, the typed address,
    // selections, filters and scroll positions.
    function resetTransient() {
        addingAddress = false; addressInput.text = ""; gitSelected = []; gitArtwork = ({});
        detail = null; reviewing = false; removing = null; selected = []; error = ""; progress = "";
        query = ""; tone = "all"; cursor = -1; shown = pageSize; scroll.contentY = 0;
    }
    function discardReview() {
        if (live) transport("discard", {kind: kind}, function() {}, cleanupOwner);
        nativeReview = null; nativeReviewing = false; advice = ""; pluginQueue = []; pluginQueueTotal = 0;
    }
    function reviewChosenPlugins() {
        pluginQueueUrl = nativeReview.url; pluginQueueTotal = gitSelected.length;
        pluginQueue = gitSelected.slice(1);
        prepareReview({url: pluginQueueUrl, id: gitSelected[0]}, true);
    }
    function prepareReview(args, queued) {
        if (!args.ids && !queued) { gitSelected = []; gitArtwork = ({}); pluginQueue = []; pluginQueueTotal = 0; }
        nativeReviewing = true; nativeReview = null; reviewSourcePath = ""; reviewSourceText = ""; addingAddress = false; advice = ""; error = ""; busy = true;
        request("prepare", args, function(failure, data) {
            if (!nativeReviewing) return;
            busy = false; error = failure; nativeReview = failure ? null : data.review;
        });
        forceActiveFocus();
    }
    function nativeConfirm() {
        if (!nativeReview || !nativeReview.token || busy) return;
        confirmingReview = true; act("confirm", {token: nativeReview.token});
    }
    function componentsText(spec) {
        const lines = [];
        for (const componentKind of Object.keys(spec.ui || {}))
            for (const entry of spec.ui[componentKind]) {
                lines.push(componentKind + " · " + entry.title + " · " + entry.qml);
                for (const field of ["dataCommand", "dataStream"])
                    if (entry[field]) lines.push(field + " · " + [entry[field].run].concat(entry[field].arguments || []).join(" "));
            }
        for (const entry of spec.rows || []) lines.push(entry.title + " · " + [entry.run].concat(entry.arguments || []).join(" "));
        for (const event of Object.keys(spec.hooks || {})) lines.push(event + " · " + [spec.hooks[event].run].concat(spec.hooks[event].arguments || []).join(" "));
        if (spec.service) lines.push(Eitr.I18n.tr("Background service") + " · " + [spec.service.run].concat(spec.service.arguments || []).join(" "));
        for (const capability of spec.capabilities || []) lines.push(capability);
        return lines.join("\n");
    }
    function closeDetail() { detailGeneration++; detail = null; wallpaperIndex = -1; forceActiveFocus(); }
    function artworkKey(path) { return tab + ":" + detailItem.id + ":" + path; }
    function artworkFor(asset, thumbnail) {
        if (asset.imageUrl) return asset.imageUrl;
        const path = thumbnail ? asset.thumbnail : asset.path;
        return path ? artwork[artworkKey(path)] || "" : "";
    }
    function fetchArtwork(asset, thumbnail) {
        const path = thumbnail ? asset.thumbnail : asset.path;
        if (!path || asset.imageUrl || !detail || !live) return;
        const key = artworkKey(path), id = detail.id, serial = detailGeneration;
        if (artwork[key] || artworkRequests[key]) return;
        artworkRequests = Object.assign({}, artworkRequests, {[key]: true});
        request("artwork", {id: id, path: path}, function(failure, data) {
            if (!failure) {
                artwork = Object.assign({}, artwork, {[key]: data.image});
                if (!thumbnail && data.size && detail && detailGeneration === serial)
                    detail = Object.assign({}, detail, {wallpapers: wallpapers.map(wallpaper => wallpaper.path === path ? Object.assign({}, wallpaper, {size: data.size}) : wallpaper)});
            }
            else { artworkRequests = Object.assign({}, artworkRequests, {[key]: false}); if (detail && detail.id === id) detailError = failure; }
        });
    }
    function showWallpaper(index) {
        wallpaperIndex = index; detailError = ""; detailScroll.contentY = 0;
        if (index >= 0 && index < wallpapers.length) fetchArtwork(wallpapers[index], false);
    }
    function openDetail(item) {
        const serial = ++detailGeneration;
        detail = item; mediaIndex = 0; wallpaperIndex = -1; detailError = ""; detailScroll.contentY = 0;
        if (tab === "community" && !isInstalled(item) && live) {
            request("detail", {id: item.id}, function(failure, data) {
                if (!detail || detailGeneration !== serial) return;
                detailError = failure;
                if (!failure) {
                    detail = Object.assign({}, item, data.item);
                    if (data.item.preview) {
                        const key = previewKey(item);
                        request("artwork", {id: item.id, path: data.item.preview}, function(problem, artworkData) {
                            if (!problem) previews = Object.assign({}, previews, {[key]: artworkData.image});
                        });
                    }
                }
            });
        }
        if (kind === "plugins" && pluginMedia.length) selectMedia(0);
        for (const asset of wallpapers) fetchArtwork(asset, true);
        sidebarFocus = false; forceActiveFocus();
    }
    property var reviewIds: null
    function reviewDetail() { if (kind === "plugins") { prepareReview({id: detail.id, updating: isInstalled(detailItem)}); return; } reviewIds = [detail.id]; reviewing = true; forceActiveFocus(); }
    property var removing: null
    property int generation: 0
    property var transport: function(name, args, callback, owner) { return DesktopData.queryCatalog(name, args, owner || catalog, callback); }
    Item { id: updateOwner }
    Item { id: cleanupOwner }
    signal closeRequested()
    readonly property var more: availableItems.filter(item => !installed.some(local => local.id === item.id))
    property string tab: "official"
    property string query: ""
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
    function matches(item) {
        const words = query.trim().toLowerCase().split(/\s+/).filter(word => word);
        const text = [item.name, item.id, item.description, item.author].filter(value => value).join(" ").toLowerCase();
        return words.every(word => text.includes(word));
    }
    function filtered(items) { return items.filter(item => matches(item) && (kind !== "themes" || tone === "all" || item.light === (tone === "light"))); }
    readonly property var locals: filtered(installed)
    readonly property var discoveries: filtered(tab === "community" ? availableItems.map(item => Object.assign({}, item, installed.find(local => local.id === item.id) || {}, {kind: "community"})) : installed.filter(item => ["builtin", "official"].includes(item.kind)).concat(more.map(item => Object.assign({kind: "official"}, item))))
    readonly property var navigable: getMore ? discoveries : locals
    function toggle(item) {
        if (kind !== "themes" || busy || isInstalled(item)) return;
        selected = selected.includes(item.id) ? selected.filter(themeId => themeId !== item.id) : selected.concat([item.id]);
    }
    function isInstalled(item) { return installed.some(local => local.id === item.id); }
    function activate(item, local) {
        if (busy) return;
        if (getMore) openDetail(item);
        else if (local && kind === "themes" && !item.current) act("apply", {id: item.id});
        else if (!local) toggle(item);
        sidebarFocus = false; forceActiveFocus();
    }
    function previewKey(item) { return kind + ":" + (tab === "community" ? "community" : "official") + ":" + item.id; }
    function imageFor(item) { return item.previewUrl || (kind === "plugins" && isInstalled(item) ? item.preview || item.icon : "") || previews[previewKey(item)] || previews[item.id] || ""; }
    readonly property var chosen: more.filter(item => (reviewIds || selected).includes(item.id)).map(item => reviewIds && detail && detail.id === item.id ? Object.assign({}, item, detail) : item)
    readonly property real totalSize: chosen.some(item => !item.size) ? 0 : chosen.reduce((total, item) => total + item.size, 0)
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
        detail = null; reviewIds = null; artwork = ({}); artworkRequests = ({}); indexLoaded = false; reviewing = false; removing = null; busy = false; error = ""; repositoryError = ""; installedError = ""; progress = "";
        if (!live || !opened) return;
        for (const catalogKind of [kind, kind === "themes" ? "plugins" : "themes"])
            for (const source of sources) fetch(catalogKind, source);
    }
    function switchView() {
        detail = null; cursor = -1; scroll.contentY = 0; shown = pageSize; selected = []; error = ""; progress = "";
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
            busy = false; confirmingReview = false; progress = ""; error = failure;
            if (name === "confirm" && failure) nativeReview = null;
            if (!failure) { nativeReview = null; nativeReviewing = false; selected = []; reviewing = false; reviewIds = null; removing = null; }
            refreshInstalled();
            if (!failure && name === "confirm" && pluginQueue.length) {
                const next = pluginQueue[0];
                pluginQueue = pluginQueue.slice(1);
                prepareReview({url: pluginQueueUrl, id: next}, true);
            }
        });
    }

    function preview(item) {
        const key = previewKey(item);
        if (!live || !opened || previews[key] || previewRequests[key]) return;
        if (kind === "themes" && tab === "community") return;
        if (kind === "plugins" && !item.preview && !item.icon) return;
        previewRequests = Object.assign({}, previewRequests, {[key]: true});
        request(kind === "themes" ? "artwork" : "preview", kind === "themes" ? {id: item.id, path: item.preview} : {id: item.id}, function(failure, data) {
            if (!failure) previews = Object.assign({}, previews, {[key]: data.image});
        });
    }
    function cancelSheet() { if (!busy) { reviewing = false; reviewIds = null; removing = null; forceActiveFocus(); } }
    function confirm() {
        if (busy) return;
        if (reviewing) act("install", {ids: chosen.map(item => item.id)});
        else if (removing) act("remove", {id: removing.id});
    }
    onTabChanged: switchView()
    onKindChanged: switchView()
    onToneChanged: { shown = pageSize; scroll.contentY = 0; }
    onQueryChanged: { shown = pageSize; cursor = -1; scroll.contentY = 0; }
    onOpenedChanged: {
        if (opened) { opening++; updateCache = ({}); load(); if (live) checkUpdates(); forceActiveFocus(); }
        else { resetTransient(); discardReview(); mediaIndex = -1; generation++; DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); busy = false; }
    }
    Component.onDestruction: { DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); }
    focus: opened
    Keys.priority: Keys.AfterItem
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) {
            if (nativeReviewing && confirmingReview) { event.accepted = true; return; }
            if (nativeReviewing) { DesktopData.releaseOwner(catalog); busy = false; discardReview(); } else if (addingAddress) { addingAddress = false; forceActiveFocus(); } else if (reviewing || removing) cancelSheet(); else if (detail) closeDetail(); else if (query) query = ""; else closeRequested();
            event.accepted = true;
        } else if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && (nativeReviewing || reviewing || removing)) {
            if (nativeReviewing) nativeConfirm(); else confirm(); event.accepted = true;
        } else if (!nativeReviewing && !addingAddress && !reviewing && !removing && !detail && !busy) {
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
            if ((event.key === Qt.Key_F && (event.modifiers & Qt.ControlModifier)) || (event.key === Qt.Key_Slash && !event.modifiers)) {
                searchField.forceActiveFocus(); searchField.selectAll(); event.accepted = true; return;
            }
            if (event.text && event.text !== " " && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)) && !/[\x00-\x1f\x7f]/.test(event.text)) {
                query += event.text; sidebarFocus = false; searchField.forceActiveFocus(); searchField.cursorPosition = searchField.text.length;
                event.accepted = true; return;
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
                if (cursor >= 0 && cursor < count) activate(navigable[cursor], isInstalled(navigable[cursor]));
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
    component GitThemeCard: Rectangle {
        id: gitCard
        required property var row
        property bool selectable: true
        readonly property bool chosen: selectable && catalog.gitSelected.includes(row.id)
        height: gitDetails.y + gitDetails.height + 12
        radius: 4; color: SiteStyle.surface
        border.width: 1; border.color: chosen ? catalog.accent : selectable && gitMouse.containsMouse ? SiteStyle.lineStrong : SiteStyle.line
        Component.onCompleted: catalog.gitArtworkFor(row)
        RectangularShadow { anchors.fill: parent; z: -1; visible: gitCard.chosen; radius: gitCard.radius; blur: 18; spread: 2; color: SiteStyle.glow }
        Preview { id: gitArt; x: 2; y: 2; width: parent.width - 4; height: width * 9 / 16; source: catalog.gitArtwork[gitCard.row.id] || ""
            plugin: catalog.kind === "plugins"; iconOnly: plugin && !gitCard.row.preview }
        Column {
            id: gitDetails
            x: 12; y: gitArt.y + gitArt.height + 10; width: parent.width - 24; spacing: 5
            Label { width: parent.width; text: gitCard.row.name || ""; font.family: SiteStyle.carved; font.weight: Font.Medium; font.letterSpacing: 0.7; maximumLineCount: 1; elide: Text.ElideRight }
            Label { width: parent.width; text: gitCard.row.description || ""; font.pixelSize: 13; color: SiteStyle.muted; maximumLineCount: 1; elide: Text.ElideRight }
            Row { spacing: 4; visible: catalog.kind === "themes"
                Repeater {
                    model: gitCard.row.palette ? ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"] : []
                    Rectangle { required property string modelData; width: 14; height: 14; radius: 7; color: gitCard.row.palette[modelData]; border.width: 1; border.color: SiteStyle.lineStrong }
                }
            }
            Row { spacing: 6
                Pill { visible: catalog.kind === "themes"; text: gitCard.row.light ? Eitr.I18n.tr("Light") : Eitr.I18n.tr("Dark") }
                Pill { visible: catalog.kind === "themes"; text: catalog.sizeText(gitCard.row.size || 0) }
                Pill { visible: catalog.kind === "plugins" && !!gitCard.row.version; text: gitCard.row.version || "" }
                Pill { visible: catalog.kind === "plugins" && catalog.isInstalled(gitCard.row); text: Eitr.I18n.tr("Installed") }
            }
        }
        MouseArea { id: gitMouse; anchors.fill: parent; hoverEnabled: true; enabled: gitCard.selectable && !catalog.busy && !(catalog.kind === "plugins" && catalog.isInstalled(gitCard.row))
            cursorShape: Qt.PointingHandCursor; onClicked: catalog.toggleGitTheme(gitCard.row.id) }
        Rectangle {
            visible: gitCard.chosen; x: 10; y: 10; width: 30; height: 30; radius: 15; color: catalog.accent
            Label { anchors.centerIn: parent; text: "\uF00C"; color: SiteStyle.primaryInk; font.pixelSize: 18 }
        }
    }
    component CatalogCard: Rectangle {
        id: tile
        required property var item
        required property bool local
        readonly property bool picked: catalog.getMore && !local && catalog.selected.includes(item.id)
        readonly property bool focused: catalog.cursor >= 0 && !!catalog.navigable[catalog.cursor] && catalog.navigable[catalog.cursor].id === item.id
        readonly property bool actionable: (catalog.getMore || !(local && (catalog.kind === "plugins" || item.current)))
        readonly property real viewportY: parent.parent.y + parent.y + y - scroll.contentY
        readonly property bool inViewport: viewportY + height > 0 && viewportY < scroll.height
        implicitHeight: details.y + details.height + 12
        radius: 4
        color: SiteStyle.surface
        border.width: 1
        border.color: picked || focused || item.current ? catalog.accent : tile.actionable && cardMouse.containsMouse ? SiteStyle.lineStrong : SiteStyle.line
        RectangularShadow {
            anchors.fill: parent; z: -1
            // The current theme keeps the selected border and glow.
            visible: tile.picked || tile.focused || !!tile.item.current
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
                Pill { visible: tile.local && catalog.getMore; text: Eitr.I18n.tr("Installed") }
                Pill { visible: catalog.kind === "plugins" && tile.item.enabled === false; text: Eitr.I18n.tr("Disabled") }
            }
            Item {
                width: parent.width
                height: 32
                visible: catalog.getMore && !tile.local || (catalog.updates[tile.item.id] || 0) > 0
                SiteButton {
                    objectName: "install-" + tile.item.id
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    width: 110; visible: catalog.getMore && !tile.local
                    text: tile.picked ? "\uF00C " + Eitr.I18n.tr("Selected") : Eitr.I18n.tr("Install")
                    selected: tile.picked; available: !catalog.busy
                    onClicked: { if (catalog.kind === "plugins") { catalog.openDetail(tile.item); catalog.reviewDetail(); } else catalog.toggle(tile.item); catalog.cursor = catalog.navigable.findIndex(item => item.id === tile.item.id); catalog.sidebarFocus = false; catalog.forceActiveFocus(); }
                }
                Pill {
                    anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                    visible: (catalog.updates[tile.item.id] || 0) > 0; text: Eitr.I18n.tr("Update"); current: true
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { if (catalog.kind === "themes") catalog.act("update", {id: tile.item.id}); else { catalog.openDetail(tile.item); catalog.prepareReview({id: tile.item.id, updating: true}); } } }
                }
            }
        }
        MouseArea { id: cardMouse; anchors.fill: parent; hoverEnabled: true; enabled: tile.actionable && !catalog.busy && !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
            cursorShape: Qt.PointingHandCursor
            onClicked: { catalog.cursor = catalog.navigable.findIndex(theme => theme.id === tile.item.id); catalog.activate(tile.item, tile.local); }
        }
        Rectangle {
            visible: tile.picked; x: 10; y: 10; width: 30; height: 30; radius: 15; color: catalog.accent
            Label { anchors.centerIn: parent; text: "\uF00C"; color: PanelStyle.readableInk(catalog.accent, catalog.foreground, catalog.background); font.pixelSize: 18 }
        }
        SiteButton {
            id: removeButton
            objectName: "remove-" + tile.item.id
            anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
            width: 28; height: 28; icon: true; text: "󰆴"; foreground: SiteStyle.fg
            color: SiteStyle.night
            visible: catalog.tab === "installed" && tile.local && !tile.item.current && tile.item.kind !== "builtin" && tile.item.kind !== "own"
            Accessible.name: Eitr.I18n.tr("Remove %1").arg(tile.item.name || "")
            onClicked: { catalog.removing = tile.item; catalog.forceActiveFocus(); }
            BarTooltip { target: removeButton; hovered: removeButton.hovered; text: Eitr.I18n.tr("Delete"); foreground: SiteStyle.fg; background: SiteStyle.raised }
        }

    }
    Item {
        id: sidebar
        width: catalog.sidebarWidth; height: parent.height
        enabled: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
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

    SiteButton { z: 1; enabled: !catalog.detail && !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing; anchors.right: parent.right; anchors.top: parent.top; anchors.topMargin: 5; anchors.rightMargin: 8; width: 34; height: 34; text: "󰅖"; icon: true; foreground: catalog.foreground; Accessible.name: Eitr.I18n.tr("Close catalog"); onClicked: catalog.closeRequested() }
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
                    hoverEnabled: true; enabled: !catalog.busy && !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
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
        enabled: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
        x: catalog.sidebarWidth + PanelStyle.padding; y: sourceTabs.height + 14
        width: catalog.width - x - PanelStyle.padding; spacing: 12
        Item {
            width: parent.width; height: 36
            // All themes by default; Sun or Moon shows only that mode, a second click all again.
            Row { anchors.right: parent.right; spacing: PanelStyle.selectionRowGap
                TextField {
                    id: searchField
                    objectName: "catalog-search"
                    width: catalog.compact ? 150 : 220; height: PanelStyle.selectionRowHeight
                    color: SiteStyle.fg; font.family: SiteStyle.mono; font.pixelSize: 13
                    placeholderText: "\uF002  " + (catalog.kind === "themes" ? Eitr.I18n.tr("Search themes") : Eitr.I18n.tr("Search plugins"))
                    placeholderTextColor: SiteStyle.muted; selectionColor: catalog.accent; selectedTextColor: SiteStyle.fg
                    leftPadding: 10; rightPadding: 10; topPadding: 0; bottomPadding: 0; verticalAlignment: TextInput.AlignVCenter
                    background: Rectangle { color: SiteStyle.raised; radius: 4; border.width: 1; border.color: searchField.activeFocus ? catalog.accent : SiteStyle.lineStrong }
                    selectByMouse: true
                    Accessible.name: placeholderText
                    text: catalog.query
                    onTextEdited: catalog.query = text
                    Keys.onEscapePressed: event => { if (text !== "") catalog.query = ""; else catalog.forceActiveFocus(); event.accepted = true; }
                    Keys.onDownPressed: event => { catalog.forceActiveFocus(); if (catalog.navigable.length) catalog.cursor = 0; event.accepted = true; }
                    onAccepted: { catalog.forceActiveFocus(); if (catalog.navigable.length) catalog.cursor = 0; }
                }
                Repeater { model: catalog.kind === "themes" ? [{tone: "light", glyph: "󰖙", label: Eitr.I18n.tr("Light")}, {tone: "dark", glyph: "󰖔", label: Eitr.I18n.tr("Dark")}] : []
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
                SiteButton { width: 100; available: !catalog.busy; text: Eitr.I18n.tr("Add"); foreground: catalog.foreground; Accessible.name: Eitr.I18n.tr("Add from a Git address"); onClicked: { catalog.addingAddress = true; catalog.error = ""; addressInput.forceActiveFocus(); } }
            }
        }
        Label { width: parent.width; visible: text !== ""; text: (!catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing ? catalog.error || catalog.progress : "") || (catalog.loading ? Eitr.I18n.tr("Loading…") : ""); Accessible.role: Accessible.AlertMessage }
        Flickable {
            id: scroll
            objectName: "catalog-scroll"
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
            SiteButton { objectName: "review-selection"; x: 8; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 108; primary: true; textAlignment: Text.AlignLeft; flat: true; text: catalog.chosen.length === 1 ? Eitr.I18n.tr("Install 1 theme · %1").arg(catalog.sizeText(catalog.totalSize)) : Eitr.I18n.tr("Install %1 themes · %2").arg(catalog.chosen.length).arg(catalog.sizeText(catalog.totalSize)); foreground: catalog.foreground; onClicked: { catalog.reviewing = true; catalog.forceActiveFocus(); } }
            SiteButton { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 80; flat: true; text: Eitr.I18n.tr("Clear"); foreground: catalog.foreground; onClicked: catalog.selected = [] }
        }
    }
    Rectangle {
        id: detailSheet
        enabled: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing
        z: 2
        objectName: catalog.kind === "plugins" ? "plugin-detail" : "theme-detail"
        anchors.fill: parent; visible: catalog.detail !== null
        color: Qt.alpha(SiteStyle.night, 0.90); radius: 4
        MouseArea { anchors.fill: parent; onClicked: catalog.closeDetail() }
        Rectangle {
            anchors.centerIn: parent; width: parent.width - (catalog.compact ? 32 : 100); height: parent.height - 40
            color: SiteStyle.surface; radius: 4; border.width: 1; border.color: SiteStyle.line
            MouseArea { anchors.fill: parent }
            Flickable {
                id: detailScroll
                objectName: "detail-scroll"
                anchors.fill: parent; anchors.margins: 22; anchors.topMargin: 52; anchors.bottomMargin: 70
                contentWidth: width; contentHeight: detailColumn.height; clip: true
                boundsBehavior: Flickable.StopAtBounds; ScrollBar.vertical: ScrollBar {}
                Column {
                    id: detailColumn
                    width: parent.width - 12; spacing: 16
                    Image {
                        visible: catalog.kind === "themes"
                        width: parent.width; height: !visible ? 0 : source.toString() ? Math.min(catalog.wallpaperIndex >= 0 ? 480 : 260, width * 9 / 16) : 0
                        source: catalog.wallpaperIndex >= 0 && catalog.wallpaperIndex < catalog.wallpapers.length ? catalog.artworkFor(catalog.wallpapers[catalog.wallpaperIndex], false) : catalog.imageFor(catalog.detailItem)
                        sourceSize: Qt.size(1200, 700); fillMode: Image.PreserveAspectFit; asynchronous: true
                    }
                    Column {
                        visible: catalog.kind === "plugins"; width: parent.width; spacing: 10
                        Item {
                            width: parent.width; height: Math.min(300, width * 9 / 16)
                            readonly property bool video: catalog.currentMedia.type === "video"
                            Image { anchors.fill: parent; visible: !parent.video || catalog.videoPosterOnly; source: parent.video ? catalog.imageFor(catalog.detailItem) : catalog.pluginMedia.length ? catalog.artworkFor(catalog.currentMedia, false) : catalog.imageFor(catalog.detailItem); fillMode: Image.PreserveAspectFit; sourceSize: Qt.size(1200, 700); asynchronous: true }
                            Label { anchors.centerIn: parent; visible: !catalog.pluginMedia.length && !catalog.imageFor(catalog.detailItem); text: "󰏗"; font.pixelSize: 80 }
                            VideoOutput { id: videoOutput; objectName: "plugin-video-output"; anchors.fill: parent; visible: parent.video && !catalog.videoPosterOnly; fillMode: VideoOutput.PreserveAspectFit }
                            Component { id: audioFactory; AudioOutput { muted: false } }
                            MediaPlayer {
                                id: pluginVideo; objectName: "plugin-video-player"
                                source: catalog.opened && catalog.detail && catalog.kind === "plugins" && catalog.currentMedia.type === "video" ? catalog.artworkFor(catalog.currentMedia, false) : ""
                                videoOutput: videoOutput
                                property bool muted: !audioOutput || audioOutput.muted
                                loops: MediaPlayer.Infinite; autoPlay: true
                                onSourceChanged: { if (audioOutput) audioOutput.muted = true; }
                                onErrorOccurred: catalog.detailError = errorString
                            }
                        }
                        Row {
                            visible: catalog.currentMedia.type === "video"; spacing: 10
                            SiteButton { width: 110; text: pluginVideo.playbackState === MediaPlayer.PlayingState ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Play"); onClicked: { if (pluginVideo.playbackState === MediaPlayer.PlayingState) pluginVideo.pause(); else pluginVideo.play(); } }
                            SiteButton { width: 110; text: pluginVideo.muted ? Eitr.I18n.tr("Unmute") : Eitr.I18n.tr("Mute"); onClicked: { if (!pluginVideo.audioOutput) pluginVideo.audioOutput = audioFactory.createObject(pluginVideo); else pluginVideo.audioOutput.muted = !pluginVideo.audioOutput.muted; } }
                        }
                        Flickable {
                            width: parent.width; height: 76; contentWidth: mediaStrip.width; clip: true
                            Row { id: mediaStrip; spacing: 8
                                Repeater { model: catalog.pluginMedia
                                    Rectangle {
                                        required property var modelData
                                        required property int index
                                        width: 110; height: 70; radius: 3; color: SiteStyle.raised
                                        border.width: 1; border.color: catalog.mediaIndex === index ? catalog.accent : SiteStyle.line
                                        Image { anchors.fill: parent; anchors.margins: 2; visible: parent.modelData.type === "image"; source: parent.modelData.type === "image" ? catalog.artworkFor(parent.modelData, false) : ""; sourceSize: Qt.size(220, 140); fillMode: Image.PreserveAspectCrop }
                                        Label { anchors.centerIn: parent; text: parent.modelData.type === "video" ? "▶" : String(parent.index + 1) }
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catalog.selectMedia(parent.index) }
                                    }
                                }
                            }
                        }
                        Label { width: parent.width; text: catalog.currentMedia.caption || ""; color: SiteStyle.muted }
                    }
                    Row {
                        visible: catalog.wallpaperIndex >= 0; spacing: 10
                        SiteButton { objectName: "wallpaper-back"; width: 100; text: Eitr.I18n.tr("Back"); onClicked: catalog.wallpaperIndex = -1 }
                        SiteButton { width: 100; text: Eitr.I18n.tr("Previous"); available: catalog.wallpaperIndex > 0; onClicked: catalog.showWallpaper(catalog.wallpaperIndex - 1) }
                        SiteButton { width: 100; text: Eitr.I18n.tr("Next"); available: catalog.wallpaperIndex < catalog.wallpapers.length - 1; onClicked: catalog.showWallpaper(catalog.wallpaperIndex + 1) }
                    }
                    Label { visible: catalog.wallpaperIndex >= 0; width: parent.width; text: catalog.wallpaperIndex >= 0 && catalog.wallpaperIndex < catalog.wallpapers.length ? catalog.wallpapers[catalog.wallpaperIndex].path.split("/").pop() : ""; color: SiteStyle.muted }
                    Column {
                        width: parent.width; spacing: 16; visible: catalog.wallpaperIndex < 0
                    Label { width: parent.width; text: catalog.detailItem.name || ""; font.family: SiteStyle.carved; font.pixelSize: 24; font.letterSpacing: 1 }
                    Label { width: parent.width; text: catalog.detailItem.description || ""; color: SiteStyle.muted }
                    Flow {
                        width: parent.width; spacing: 8
                        Repeater {
                            model: Object.keys(catalog.detailItem.palette || {})
                            Rectangle {
                                id: swatch
                                required property string modelData
                                width: 24; height: 24; radius: 12; color: catalog.detailItem.palette[modelData]
                                border.width: 1; border.color: SiteStyle.lineStrong
                                MouseArea { id: swatchMouse; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                                BarTooltip { target: swatch; hovered: swatchMouse.containsMouse; text: swatch.modelData + " " + catalog.detailItem.palette[swatch.modelData]; foreground: SiteStyle.fg; background: SiteStyle.raised }
                            }
                        }
                    }
                    Flow {
                        width: parent.width; spacing: 8
                        Pill { text: catalog.badge(catalog.detailItem) }
                        Pill { visible: typeof catalog.detailItem.light === "boolean"; text: catalog.detailItem.light ? Eitr.I18n.tr("Light") : Eitr.I18n.tr("Dark") }
                        Pill { visible: catalog.isInstalled(catalog.detailItem); text: Eitr.I18n.tr("Installed") }
                        Pill { visible: catalog.detailItem.enabled === false; text: Eitr.I18n.tr("Disabled") }
                        Pill { visible: !!catalog.detailItem.current; current: true; text: Eitr.I18n.tr("Current") }
                    }
                    Label {
                        width: parent.width
                        text: [catalog.detailItem.author || "", catalog.detailItem.maintainer || (["builtin", "official"].includes(catalog.detailItem.kind) ? Eitr.I18n.tr("The Eitr project") : ""), catalog.detailItem.license || (catalog.kind === "themes" && ["builtin", "official"].includes(catalog.detailItem.kind) ? "GPL-3.0" : "")].filter(value => value).join(" · ")
                        color: SiteStyle.muted
                    }
                    Label { visible: catalog.kind === "plugins"; width: parent.width; text: (catalog.detailItem.version || "") + (catalog.tab === "community" ? " · " + (catalog.detailItem.commit || "").slice(0, 12) : ""); color: SiteStyle.muted }
                    Label { visible: catalog.kind === "plugins"; width: parent.width; text: catalog.componentsText(catalog.detailItem.components || {}); color: SiteStyle.muted }
                    Label { visible: catalog.kind === "themes"; width: parent.width; text: catalog.sizeText(catalog.detailItem.size || 0); color: SiteStyle.muted }
                    Label { width: parent.width; text: (catalog.detailItem.repository || (catalog.detailItem.source || {}).url || (catalog.detailItem.kind === "builtin" ? "eitr-org/eitr" : catalog.detailItem.kind === "official" ? "eitr-org/eitr-themes" : "")) + " / " + (catalog.detailItem.folder || catalog.detailItem.repositoryPath || (catalog.detailItem.source || {}).folder || (catalog.kind === "plugins" ? "." : "themes/" + (catalog.detailItem.id || ""))); color: SiteStyle.muted; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
                    Rectangle { width: parent.width; height: 1; color: SiteStyle.line }
                    Label { visible: catalog.kind === "themes"; text: Eitr.I18n.tr("Wallpapers"); font.family: SiteStyle.carved; font.pixelSize: 18 }
                    Label { visible: catalog.kind === "themes" && catalog.wallpapers.length === 0; text: Eitr.I18n.tr("No wallpapers"); color: SiteStyle.muted }
                    Flow {
                        width: parent.width; spacing: 10
                        Repeater {
                            model: catalog.wallpapers
                            Rectangle {
                                id: wallpaperTile
                                required property var modelData
                                required property int index
                                objectName: "wallpaper-" + index
                                width: Math.min(210, detailColumn.width); height: modelData.thumbnail || modelData.imageUrl ? 146 : 76
                                color: SiteStyle.raised; radius: 3; border.width: 1; border.color: SiteStyle.line
                                Image { x: 1; y: 1; width: parent.width - 2; height: 100; visible: !!wallpaperTile.modelData.thumbnail || !!wallpaperTile.modelData.imageUrl; source: catalog.artworkFor(wallpaperTile.modelData, true); sourceSize: Qt.size(480, 270); asynchronous: true; fillMode: Image.PreserveAspectCrop }
                                Column { x: 8; y: wallpaperTile.height - 42; width: parent.width - 16; spacing: 3
                                    Label { width: parent.width; text: wallpaperTile.modelData.path.split("/").pop(); maximumLineCount: 1; elide: Text.ElideMiddle; font.pixelSize: 11 }
                                    Label { text: catalog.sizeText(wallpaperTile.modelData.size); color: SiteStyle.muted; font.pixelSize: 11 }
                                }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catalog.showWallpaper(wallpaperTile.index) }
                            }
                        }
                    }
                    Label { width: parent.width; visible: text !== ""; text: catalog.detailError || catalog.error; color: SiteStyle.muted }
                    }

                }
            }
                    SiteButton {
                        objectName: "detail-install"
                        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 22
                        width: 150; primary: true; available: !catalog.busy
                        visible: !catalog.detailItem.current && (catalog.kind === "themes" || !catalog.isInstalled(catalog.detailItem) || (catalog.updates[catalog.detailItem.id] || catalog.detailItem.updateCount || 0) > 0)
                        text: catalog.isInstalled(catalog.detailItem) ? (catalog.kind === "plugins" ? Eitr.I18n.tr("Update") : Eitr.I18n.tr("Apply")) : Eitr.I18n.tr("Install")
                        onClicked: { if (catalog.kind === "plugins") catalog.reviewDetail(); else if (catalog.isInstalled(catalog.detailItem)) { const themeId = catalog.detailItem.id; catalog.closeDetail(); catalog.act("apply", {id: themeId}); } else catalog.reviewDetail(); }
                    }
            SiteButton { objectName: "detail-close"; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 10; width: 32; icon: true; text: "󰅖"; Accessible.name: Eitr.I18n.tr("Close"); onClicked: catalog.closeDetail() }
        }
    }
    Rectangle {
        z: 3; anchors.fill: parent; visible: catalog.reviewing || catalog.removing !== null
        color: SiteStyle.night; radius: 4
        MouseArea { anchors.fill: parent }
        Rectangle {
            // Removal is a short confirmation; the install review needs room for previews.
            anchors.centerIn: parent
            width: catalog.reviewing ? parent.width - 72 : Math.min(520, parent.width - 48)
            height: catalog.reviewing ? 420 : sheetColumn.implicitHeight + 48 + 32 + 20
            radius: 4; color: SiteStyle.surface
            border.width: 1; border.color: SiteStyle.line
            Column {
                id: sheetColumn
                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 24; spacing: 18
                Label { width: parent.width; font.family: SiteStyle.carved; font.pixelSize: PanelStyle.headingSize; font.weight: Font.Medium; text: catalog.reviewing ? Eitr.I18n.tr("Review theme installation") : Eitr.I18n.tr("Remove %1?").arg(catalog.removing ? catalog.removing.name : "") }
                Label { width: parent.width; text: catalog.reviewing ? Eitr.I18n.tr("Data-only themes · Review selected sources") : catalog.kind === "plugins" ? Eitr.I18n.tr("The plugin and its files are deleted from this computer.") : Eitr.I18n.tr("The theme is deleted from this computer."); color: SiteStyle.muted }
                ListView {
                    visible: catalog.reviewing
                    width: parent.width; height: 190; orientation: ListView.Horizontal; spacing: 12; clip: true
                    model: catalog.reviewing ? catalog.chosen : []; boundsBehavior: Flickable.StopAtBounds
                    delegate: Column { required property var modelData; width: 200; spacing: 8
                        Preview { width: 200; height: 112; source: catalog.imageFor(parent.modelData) }
                        Label { width: parent.width; text: parent.modelData.repository || "eitr-org/eitr-themes"; font.pixelSize: 11; elide: Text.ElideMiddle }
                        Label { width: parent.width; text: parent.modelData.name; maximumLineCount: 1; elide: Text.ElideRight; font.bold: true }
                        Label { text: catalog.sizeText(parent.modelData.size || 0); font.pixelSize: PanelStyle.captionSize; color: SiteStyle.muted }
                    }
                }
                Label { visible: text !== ""; text: catalog.busy ? catalog.progress : catalog.error || (catalog.reviewing ? Eitr.I18n.tr("Total download: %1").arg(catalog.sizeText(catalog.totalSize)) : ""); width: parent.width }
                ProgressBar { width: parent.width; height: 6; visible: catalog.busy; indeterminate: true; palette.highlight: catalog.accent; palette.base: Qt.alpha(catalog.foreground, 0.08) }
            }
            Row {
                anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24; spacing: 8
                SiteButton { width: 100; available: !catalog.busy; text: Eitr.I18n.tr("Cancel"); foreground: catalog.foreground; onClicked: catalog.cancelSheet() }
                SiteButton { width: 100; available: !catalog.busy; primary: true; text: catalog.reviewing ? Eitr.I18n.tr("Install") : Eitr.I18n.tr("Remove"); foreground: catalog.foreground; onClicked: catalog.confirm() }
            }
        }
    }
    Rectangle {
        objectName: "native-review"; z: 4; anchors.fill: parent
        visible: catalog.nativeReviewing || catalog.addingAddress
        color: Qt.alpha(SiteStyle.night, 0.94)
        MouseArea { anchors.fill: parent }
        Rectangle {
            anchors.centerIn: parent; width: parent.width - (catalog.compact ? 32 : 100); height: parent.height - 40
            color: SiteStyle.surface; radius: 4; border.width: 1; border.color: SiteStyle.line
            Column {
                anchors.fill: parent; anchors.margins: 24; spacing: 16
                Label { width: parent.width; font.family: SiteStyle.carved; font.pixelSize: 22; text: catalog.addingAddress ? Eitr.I18n.tr("Add from a Git address") : catalog.nativeReview && catalog.nativeReview.changes && catalog.nativeReview.changes.new ? Eitr.I18n.tr("Review plugin update") : catalog.nativeReview && catalog.nativeReview.choices ? (catalog.kind === "themes" ? Eitr.I18n.tr("Choose themes") : Eitr.I18n.tr("Choose plugins")) : catalog.pluginQueueTotal > 1 ? Eitr.I18n.tr("Review plugin %1 of %2").arg(catalog.pluginQueueTotal - catalog.pluginQueue.length).arg(catalog.pluginQueueTotal) : catalog.kind === "themes" ? Eitr.I18n.tr("Review theme installation") : Eitr.I18n.tr("Review plugin installation") }
                Column {
                    visible: catalog.addingAddress; width: parent.width; spacing: 14
                    Label { width: parent.width; text: Eitr.I18n.tr("HTTPS or SSH Git address"); color: SiteStyle.muted }
                    TextField { id: addressInput; objectName: "git-address"; width: parent.width; color: SiteStyle.fg; placeholderText: "https://…"; placeholderTextColor: SiteStyle.muted; font.family: SiteStyle.mono; selectionColor: catalog.accent; selectedTextColor: SiteStyle.fg; background: Rectangle { color: SiteStyle.raised; radius: 4; border.width: 1; border.color: SiteStyle.lineStrong } selectByMouse: true; onAccepted: catalog.prepareReview({url: text.trim()}) }
                    Label { width: parent.width; text: catalog.kind === "plugins" ? Eitr.I18n.tr("Plugins run with your account's full permissions") : Eitr.I18n.tr("Data-only themes · Review selected sources"); color: SiteStyle.muted }
                }
                Flickable {
                    width: parent.width; height: Math.max(40, parent.height - 150); visible: !catalog.addingAddress
                    contentWidth: width; contentHeight: reviewColumn.height; clip: true; boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    Column {
                        id: reviewColumn; width: parent.width - 12; spacing: 14
                        readonly property var facts: catalog.nativeReview || ({})
                        Label { width: parent.width; visible: text !== ""; text: catalog.busy ? Eitr.I18n.tr("Loading…") : catalog.error; color: SiteStyle.muted }
                        Label { width: parent.width; visible: !!catalog.nativeReview; text: reviewColumn.facts.dataOnly ? Eitr.I18n.tr("Data-only themes · Review selected sources") : Eitr.I18n.tr("Plugins run with your account's full permissions"); font.bold: true }
                        Label { width: parent.width; visible: !!catalog.nativeReview && !reviewColumn.facts.dataOnly; text: reviewColumn.facts.official ? Eitr.I18n.tr("Official Eitr plugin") : Eitr.I18n.tr("Eitr has not reviewed it. Its code belongs to its author, not to Eitr. Only add plugins from people and repositories you trust."); color: reviewColumn.facts.official ? SiteStyle.muted : SiteStyle.accent; font.bold: !reviewColumn.facts.official }
                        Label { width: parent.width; visible: !reviewColumn.facts.themes && text !== ""; text: (reviewColumn.facts.spec || {}).name || ""; font.family: SiteStyle.carved; font.pixelSize: 22 }
                        Label { width: parent.width; text: [reviewColumn.facts.url, reviewColumn.facts.folder, reviewColumn.facts.commit, reviewColumn.facts.author, (reviewColumn.facts.spec || {}).author, (reviewColumn.facts.spec || {}).version, reviewColumn.facts.license].filter(value => value).join("\n"); wrapMode: Text.WrapAnywhere; color: SiteStyle.muted }
                        Flow {
                            width: reviewColumn.width; spacing: 14
                            visible: !!reviewColumn.facts.choices || catalog.kind === "themes" && !!reviewColumn.facts.themes
                            Repeater { model: reviewColumn.facts.choices || (catalog.kind === "themes" ? reviewColumn.facts.themes || [] : [])
                                GitThemeCard { required property var modelData; row: modelData; selectable: !!reviewColumn.facts.choices; width: Math.floor((reviewColumn.width - 14 * (catalog.columns - 1)) / catalog.columns) }
                            }
                        }
                        Label { width: parent.width; visible: text !== ""; text: catalog.componentsText(reviewColumn.facts.spec || {}); wrapMode: Text.WrapAnywhere }
                        Label { width: parent.width; visible: text !== ""; text: (reviewColumn.facts.flags || []).join("\n"); color: SiteStyle.accent; wrapMode: Text.WrapAnywhere }
                        Label { width: parent.width; text: Eitr.I18n.tr("Files"); font.bold: true; visible: (reviewColumn.facts.files || []).length > 0 }
                        Label { width: parent.width; visible: text !== ""; text: (reviewColumn.facts.files || []).join("\n"); wrapMode: Text.WrapAnywhere; color: SiteStyle.muted }
                        Label { width: parent.width; visible: text !== ""; text: reviewColumn.facts.changes && reviewColumn.facts.changes.new ? [reviewColumn.facts.changes.old + " → " + reviewColumn.facts.changes.new].concat(reviewColumn.facts.changes.subjects || [], (reviewColumn.facts.changes.files || []).map(file => file.status + " " + file.path + " +" + file.added + " −" + file.removed), reviewColumn.facts.changes.flags || []).join("\n") : ""; wrapMode: Text.WrapAnywhere }
                        Repeater { model: reviewColumn.facts.qml || []
                            SiteButton { required property var modelData; width: reviewColumn.width; text: modelData.path; onClicked: catalog.loadReviewSource(modelData.path, 0) }
                        }
                        Label { width: parent.width; visible: !!catalog.reviewSourcePath; text: catalog.reviewSourcePath + "\n" + catalog.reviewSourceText; font.family: SiteStyle.mono; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
                        Row { spacing: 10; visible: !!catalog.reviewSourcePath
                            SiteButton { width: 100; text: Eitr.I18n.tr("Previous"); available: catalog.reviewSourceOffset > 0; onClicked: catalog.loadReviewSource(catalog.reviewSourcePath, Math.max(0, catalog.reviewSourceOffset - 16384)) }
                            SiteButton { width: 100; text: Eitr.I18n.tr("Next"); available: catalog.reviewSourceOffset + 16384 < catalog.reviewSourceTotal; onClicked: catalog.loadReviewSource(catalog.reviewSourcePath, catalog.reviewSourceOffset + 16384) }
                        }
                        SiteButton { width: 220; visible: !!reviewColumn.facts.assistant; available: !catalog.busy; text: Eitr.I18n.tr("Ask the AI to check"); onClicked: { catalog.busy = true; catalog.request("advice", {token: catalog.nativeReview.token}, function(failure, data) { catalog.busy = false; catalog.advice = failure || (data.answer || []).join("\n"); }); } }
                        Label { width: parent.width; visible: text !== ""; text: catalog.advice; wrapMode: Text.WrapAnywhere }
                    }
                }
                Row {
                    spacing: 12
                    SiteButton { width: 110; text: Eitr.I18n.tr("Cancel"); available: !catalog.confirmingReview; onClicked: { DesktopData.releaseOwner(catalog); catalog.busy = false; catalog.addingAddress = false; catalog.discardReview(); catalog.forceActiveFocus(); } }
                    SiteButton { objectName: "address-review"; width: 110; visible: catalog.addingAddress; primary: true; text: Eitr.I18n.tr("Review"); onClicked: catalog.prepareReview({url: addressInput.text.trim()}) }
                    SiteButton { objectName: "git-continue"; width: 150; visible: !!catalog.nativeReview && !!catalog.nativeReview.choices; primary: true; available: catalog.gitSelected.length > 0 && !catalog.busy
                        text: catalog.gitSelected.length > 1 ? Eitr.I18n.tr("Continue · %1").arg(catalog.gitSelected.length) : Eitr.I18n.tr("Continue")
                        onClicked: { if (catalog.kind === "plugins") catalog.reviewChosenPlugins(); else catalog.prepareReview({url: catalog.nativeReview.url, ids: catalog.gitSelected}); } }
                    SiteButton { objectName: "native-confirm"; width: 110; visible: !!catalog.nativeReview && !!catalog.nativeReview.token; available: !catalog.busy; primary: true; text: Eitr.I18n.tr("Confirm"); onClicked: catalog.nativeConfirm() }
                }
            }
        }
    }

}
