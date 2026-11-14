import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import "../StoreKinds.js" as StoreKinds
import "StoreSearch.js" as StoreSearch

Item {
    property var scroll
    property var detailScroll
    property var addressInput
    property var removePackagesChoice
    property var searchField
    property var sidebar
    id: catalog
    property color foreground: SettingsPalette.foreground
    property color background: SettingsPalette.background
    property color accent: SettingsPalette.accent
    readonly property color surface: SettingsPalette.surface
    readonly property color raised: SettingsPalette.raised
    readonly property color muted: Qt.alpha(foreground, 0.72)
    readonly property color line: Qt.alpha(foreground, 0.12)
    readonly property color lineStrong: Qt.alpha(foreground, 0.24)
    readonly property color gold: SettingsInk.gold
    readonly property color glow: Qt.alpha(accent, 0.28)
    property bool opened: false
    property bool live: true
    property string kind: "themes"
    property var installed: []
    property var availableItems: []
    property bool indexLoaded: false
    readonly property bool communityEmpty: tab === "discover" && sourceFilter === "community" && indexLoaded && !repositoryError && !availableItems.some(item => item.kind === "community")
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
    property string reviewUpdating: ""
    property bool addingAddress: false
    property var gitSelected: []
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
    property var videoPlayer
    property int mediaIndex: 0
    readonly property var pluginMedia: (detailItem.preview ? [{type: "image", path: detailItem.preview, imageUrl: detailItem.preview.startsWith("file:") ? detailItem.preview : "", caption: ""}] : []).concat(detailItem.media || [])
    readonly property var currentMedia: pluginMedia[mediaIndex] || ({})
    function selectMedia(index) { mediaIndex = index; if (pluginMedia[index]) fetchArtwork(pluginMedia[index], false); }
    function resetTransient() {
        addingAddress = false; catalog.addressInput.text = ""; gitSelected = []; gitArtwork = ({});
        detail = null; reviewing = false; removing = null; managing = null; selected = []; error = ""; progress = "";
        query = ""; tone = "all"; sourceFilter = "all"; cursor = -1; shown = pageSize; catalog.scroll.contentY = 0;
    }
    function discardReview() {
        if (live && ["themes", "plugins"].includes(kind)) transport("discard", {kind: kind}, function() {}, cleanupOwner);
        nativeReview = null; nativeReviewing = false; advice = ""; pluginQueue = []; pluginQueueTotal = 0;
    }
    function reviewChosenPlugins() {
        pluginQueueUrl = nativeReview.url; pluginQueueTotal = gitSelected.length;
        pluginQueue = gitSelected.slice(1).map(id => ({url: pluginQueueUrl, id: id}));
        prepareReview({url: pluginQueueUrl, id: gitSelected[0]}, true);
    }
    readonly property var pendingUpdates: installed.filter(item => (updates[item.id] || 0) > 0).map(item => item.id)
    function updateAll() {
        const ids = pendingUpdates;
        if (!ids.length || busy) return;
        if (capabilities.useOnClick) { updateThemes(ids); return; }
        pluginQueueTotal = ids.length;
        pluginQueue = ids.slice(1).map(id => ({id: id, updating: true}));
        prepareReview({id: ids[0], updating: true}, true);
    }
    function updateThemes(ids) {
        if (ids.length) act("update", {id: ids[0]}, () => updateThemes(ids.slice(1)));
    }
    function prepareReview(args, queued) {
        if (!args.ids && !queued) { gitSelected = []; gitArtwork = ({}); pluginQueue = []; pluginQueueTotal = 0; }
        reviewUpdating = args.updating ? args.id : "";
        nativeReviewing = true; nativeReview = null; reviewSourcePath = ""; reviewSourceText = ""; addingAddress = false; advice = ""; error = ""; busy = true;
        request("prepare", args, function(failure, data) {
            if (!failure && data.bundled) { nativeReviewing = false; busy = false; catalog.act("install", {ids:[args.id]}); return; }
            if (!nativeReviewing) return;
            busy = false;
            if (!failure && data.upToDate) {
                nativeReviewing = false; nativeReview = null; forgetUpdate(args.id);
                progress = Eitr.I18n.tr("Already up to date."); forceActiveFocus();
                return;
            }
            error = failure; nativeReview = failure ? null : data.review;
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
        wallpaperIndex = index; detailError = ""; catalog.detailScroll.contentY = 0;
        if (index >= 0 && index < wallpapers.length) fetchArtwork(wallpapers[index], false);
    }
    function openDetail(item) {
        if (item.storeKind && item.storeKind !== kind) kind = item.storeKind;
        const serial = ++detailGeneration;
        detail = item; mediaIndex = 0; wallpaperIndex = -1; detailError = ""; catalog.detailScroll.contentY = 0;
        if (channelFor(item) === "community" && !isInstalled(item) && live) {
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
    function reviewDetail() { if (!capabilities.useOnClick) { prepareReview({id: detail.id, updating: isInstalled(detailItem)}); return; } reviewIds = [detail.id]; reviewing = true; forceActiveFocus(); }
    property var removing: null
    property var managing: null
    property int generation: 0
    property var transport: function(name, args, callback, owner) { return DesktopData.queryCatalog(name, args, owner || catalog, callback); }
    Item { id: updateOwner }
    Item { id: cleanupOwner }
    signal closeRequested()
    readonly property var more: availableItems.filter(item => !installed.some(local => local.id === item.id))
    property string tab: "discover"
    property string query: ""
    readonly property bool getMore: tab !== "installed"
    property bool sidebarFocus: true
    readonly property bool compact: width < 760
    readonly property int sidebarWidth: Math.min(260, width * 0.31) + PanelStyle.padding * 3
    readonly property var kinds: StoreKinds.kinds
    readonly property var definition: kinds.find(entry => entry.id === kind) || kinds[0]
    readonly property var capabilities: definition.capabilities
    property string sourceFilter: "all"
    readonly property var navigation: {
        const rows = [];
        for (const entry of kinds)
            for (const page of ["installed", "discover"])
                rows.push({id: entry.id + "/" + page, kind: entry.id, tab: page,
                    title: page === "installed" ? Eitr.I18n.tr("Installed") : Eitr.I18n.tr("Discover"),
                    rune: entry.rune, group: Eitr.I18n.tr(entry.label), groupRune: entry.rune,
                    description: Eitr.I18n.tr(entry.descriptions[page])});
        return rows;
    }
    readonly property int navigationIndex: Math.max(0, navigation.findIndex(row => row.kind === kind && row.tab === tab))
    readonly property var currentPage: navigation[navigationIndex]
    function navigate(index) {
        const row = navigation[Math.max(0, Math.min(navigation.length - 1, index))];
        kind = row.kind; tab = row.tab;
        cursor = -1; catalog.scroll.contentY = 0;
        sidebarFocus = true; forceActiveFocus();
    }
    property string tone: "all"
    property int cursor: -1
    readonly property int pageSize: 24
    property int shown: pageSize
    onCursorChanged: if (cursor >= shown - columns) shown = Math.ceil((cursor + columns + 1) / pageSize) * pageSize
    readonly property int columns: Math.max(1, Math.min(3, Math.floor((width - sidebarWidth - 48) / 230)))
    function filtered(items) { return items.filter(item => StoreSearch.matches(item, query) && (kind !== "themes" || tone === "all" || item.light === (tone === "light"))); }
    readonly property var locals: filtered(installed)
    readonly property var discoveries: filtered(availableItems.map(item => Object.assign({}, item, installed.find(local => local.id === item.id) || {}, {kind: item.kind, channel: item.channel}))).filter(item => sourceFilter === "all" || (sourceFilter === "official" ? ["builtin", "official"].includes(item.kind) : item.kind === "community"))
    readonly property var navigable: query.trim() && live ? StoreSearch.rows(store, kinds, tab, query, sourceFilter, kind === "themes" ? tone : "all") : getMore ? discoveries : locals
    function toggle(item) {
        if (item.storeKind && item.storeKind !== kind) kind = item.storeKind;
        if (!capabilities.useOnClick || capabilities.needsAdministrator || busy || isInstalled(item)) return;
        selected = selected.includes(item.id) ? selected.filter(themeId => themeId !== item.id) : selected.concat([item.id]);
    }
    function isInstalled(item) { return (item.storeKind && item.storeKind !== kind ? (store[item.storeKind + ":installed"] || {}).items || [] : installed).some(local => local.id === item.id); }
    function activate(item, local) {
        if (item.storeKind && item.storeKind !== kind) kind = item.storeKind;
        if (busy) return;
        if (kind === "lockscreens" && getMore) return;
        if (getMore) openDetail(item);
        else if (local && capabilities.useOnClick && !item.current) act("apply", {id: item.id});
        else if (local && kind === "plugins") managing = item;
        else if (!local) toggle(item);
        sidebarFocus = false; forceActiveFocus();
    }
    function channelFor(item) { return item.channel || (item.kind === "community" ? "community" : "official"); }
    function previewKey(item) { return (item.storeKind || kind) + ":" + channelFor(item) + ":" + item.id; }
    function imageFor(item) { return item.previewUrl || ((item.storeKind || kind) === "plugins" && isInstalled(item) ? item.preview || item.icon : "") || previews[previewKey(item)] || previews[item.id] || ""; }
    readonly property var chosen: more.filter(item => (reviewIds || selected).includes(item.id)).map(item => reviewIds && detail && detail.id === item.id ? Object.assign({}, item, detail) : item)
    readonly property real totalSize: chosen.some(item => !item.size) ? 0 : chosen.reduce((total, item) => total + item.size, 0)
    function sizeText(bytes) { if (!bytes) return Eitr.I18n.tr("Size unavailable"); return bytes < 1048576 ? Math.ceil(bytes / 1024) + " KiB" : (bytes / 1048576).toFixed(1) + " MiB"; }
    function badge(item) {
        return ({builtin: getMore ? Eitr.I18n.tr("Official") : Eitr.I18n.tr("Built in"), official: Eitr.I18n.tr("Official"), community: Eitr.I18n.tr("Community"), "third-party": Eitr.I18n.tr("Third-party"), own: Eitr.I18n.tr("Yours")})[item.kind] || Eitr.I18n.tr("Official");
    }
    function request(name, args, callback) {
        const current = generation;
        transport(name, Object.assign({kind: kind, channel: detail ? channelFor(detail) : "official"}, args), function(failure, data) {
            if (!opened || current !== generation) return;
            callback(failure || data.error || "", data);
        });
    }
    property var store: ({})
    readonly property var sources: ["installed", "official", "community"]
    function fetch(catalogKind, source) {
        const key = catalogKind + ":" + source;
        store = Object.assign({}, store, {[key]: Object.assign({}, store[key] || {items: []}, {pending: true, error: ""})});
        sync();
        request(source === "installed" ? "installed" : "index", {kind: catalogKind, channel: source}, function(failure, data) {
            store = Object.assign({}, store, {[key]: {items: failure ? (store[key].items || []) : (data.items || []).map(item => Object.assign({}, item, source === "installed" ? {} : {kind: item.kind === "builtin" ? "builtin" : item.kind === "community" ? "community" : "official", channel: source})), error: failure, pending: false, loaded: !failure}});
            sync();
        });
    }
    function sync() {
        const local = store[kind + ":installed"] || {items: []};
        const indexes = definition.sources.map(source => store[kind + ":" + source] || {items: []});
        const merged = [];
        for (const index of indexes) for (const item of index.items) if (!merged.some(row => row.id === item.id)) merged.push(item);
        const index = {items: merged, loaded: indexes.every(entry => entry.loaded), error: indexes.map(entry => entry.error || "").filter(value => value).join("\n")};
        installed = local.items; installedError = local.error || ""; loading = !!local.pending;
        indexLoaded = !!index.loaded; availableItems = index.items; repositoryError = index.error || "";
    }
    function refreshInstalled() { fetch(kind, "installed"); }
    function refreshIndex() { if (tab !== "installed") for (const source of definition.sources) fetch(kind, source); }
    function load() {
        generation++;
        store = ({}); installed = []; availableItems = []; selected = []; updates = updateCache[kind] || ({}); previews = ({}); previewRequests = ({});
        detail = null; reviewIds = null; artwork = ({}); artworkRequests = ({}); reviewing = false; removing = null; busy = false; error = ""; repositoryError = ""; installedError = ""; progress = "";
        if (!live || !opened) return;
        for (const entry of kinds) for (const source of ["installed"].concat(entry.sources)) fetch(entry.id, source);
    }
    function switchView() {
        detail = null; cursor = -1; catalog.scroll.contentY = 0; shown = pageSize; selected = []; error = ""; progress = "";
        updates = updateCache[kind] || ({});
        if (live && opened) sync();
    }
    function checkUpdates() {
        const currentOpening = opening;
        for (const catalogKind of kinds.filter(entry => entry.capabilities.update).map(entry => entry.id)) {
            transport("check", {kind: catalogKind}, function(failure, data) {
                if (!opened || opening !== currentOpening || failure || data.error) return;
                updateCache = Object.assign({}, updateCache, {[catalogKind]: data.updates || {}});
                if (kind === catalogKind) updates = updateCache[catalogKind];
            }, updateOwner);
        }
    }
    function forgetUpdate(id) {
        const remaining = Object.assign({}, updates);
        delete remaining[id];
        updates = remaining;
        updateCache = Object.assign({}, updateCache, {[kind]: remaining});
    }
    function act(name, args, done) {
        if (busy) return;
        busy = true; error = "";
        progress = Eitr.I18n.tr("Applying changes…");
        request(name, args, function(failure, data) {
            busy = false; confirmingReview = false; progress = ""; error = failure;
            if (name === "confirm" && failure) nativeReview = null;
            if (!failure) { nativeReview = null; nativeReviewing = false; selected = []; reviewing = false; reviewIds = null; removing = null; }
            if (!failure && name === "update") forgetUpdate(args.id);
            if (!failure && name === "confirm" && reviewUpdating) { forgetUpdate(reviewUpdating); reviewUpdating = ""; }
            refreshInstalled();
            if (!failure && name === "confirm" && pluginQueue.length) {
                const next = pluginQueue[0];
                pluginQueue = pluginQueue.slice(1);
                prepareReview(next, true);
            }
            if (!failure && done) done();
        });
    }
    function preview(item) {
        const itemKind = item.storeKind || kind;
        const key = previewKey(item);
        if (itemKind === "lockscreens" || itemKind === "wallpapers" || !live || !opened || previews[key] || previewRequests[key]) return;
        if (itemKind === "themes" && channelFor(item) === "community") return;
        if (itemKind === "plugins" && !item.preview && !item.icon) return;
        previewRequests = Object.assign({}, previewRequests, {[key]: true});
        request(itemKind === "themes" ? "artwork" : "preview", itemKind === "themes" ? {kind: itemKind, id: item.id, path: item.preview, channel: channelFor(item)} : {kind: itemKind, id: item.id, channel: channelFor(item)}, function(failure, data) {
            if (!failure) previews = Object.assign({}, previews, {[key]: data.image});
        });
    }
    function cancelSheet() { if (!busy) { reviewing = false; reviewIds = null; removing = null; forceActiveFocus(); } }
    function confirm() {
        if (busy) return;
        if (reviewing) {
            const groups = [];
            for (const item of chosen) {
                const channel = channelFor(item);
                let group = groups.find(entry => entry.channel === channel);
                if (!group) { group = {channel: channel, ids: []}; groups.push(group); }
                group.ids.push(item.id);
            }
            function next(index) { if (index < groups.length) act("install", groups[index], () => next(index + 1)); }
            next(0);
        }
        else if (removing) act("remove", {id: removing.id, removePackages: catalog.removePackagesChoice.checked ? removing.removablePackages || [] : []});
    }
    onTabChanged: switchView()
    onKindChanged: switchView()
    onToneChanged: { shown = pageSize; catalog.scroll.contentY = 0; }
    onQueryChanged: { shown = pageSize; cursor = -1; catalog.scroll.contentY = 0; }
    onOpenedChanged: {
        if (opened) { opening++; updateCache = ({}); load(); if (live) checkUpdates(); forceActiveFocus(); }
        else { resetTransient(); discardReview(); mediaIndex = -1; generation++; DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); busy = false; }
    }
    Component.onDestruction: { DesktopData.releaseOwner(catalog); DesktopData.releaseOwner(updateOwner); }
}
