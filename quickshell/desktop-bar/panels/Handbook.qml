import ".."
import Eitr as Eitr
import QtQuick
import "../JsonState.js" as JsonState
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import "../PanelStyle.js" as PanelStyle
import "../HandbookModel.js" as Model

// Offline, read-only reader and first-login welcome in a remembered native window,
// framed like Settings: the shared sidebar, page header and cards.
FamilyWindow {
    id: book
    readonly property real reveal: opened ? 1 : 0
    title: "EITR Handbook"
    property var chapters: []
    property string selectedId: "getting-started"
    property string query: ""
    property string loadError: ""
    readonly property var filtered: Model.matches(chapters, query)
    readonly property int selectedIndex: chapters.findIndex(chapter => chapter.id === selectedId)
    readonly property var chapter: selectedIndex >= 0 ? chapters[selectedIndex] : null
    property int pick: 0
    readonly property var chapterGroup: Model.groupOf(chapters, chapter)
    readonly property color ink: SettingsPalette.foreground
    readonly property color line: Qt.tint(SettingsPalette.background, Qt.alpha(SettingsPalette.foreground, 0.16))
    readonly property var htmlStyle: ({body: DesktopFonts.family, mono: SiteStyle.mono, carved: SiteStyle.carved, fg: String(ink),
        gold: String(SettingsInk.gold), raised: String(SettingsPalette.raised), line: String(line)})
    readonly property string welcomeChapter: "getting-started"
    property bool showAtLogin: false
    property bool offerProblemReports: false
    property bool welcomeShown: false
    readonly property bool welcomeVisible: selectedId === welcomeChapter && loadError === "" && !!chapter && !!chapter.welcome
    // Asks the shell to open a Settings page, such as "connections/wifi"; the welcome stays open behind it.
    signal setupRequested(string route)
    signal welcomeChoice(string action)
    signal problemReportsChoice(bool offer)
    onOpenedChanged: {
        if (opened) { focusDelay.restart(); return; }
        // Closing the automatic welcome without asking to see it again dismisses it for good.
        if (welcomeShown && !showAtLogin) welcomeChoice("dismiss");
        welcomeShown = false;
    }
    onSelectedIdChanged: articleScroll.contentY = 0
    function choose(id) {
        if (!chapters.some(chapter => chapter.id === id)) return;
        selectedId = id;
        articleScroll.contentY = 0;
    }
    function show(id) {
        if (id) { query = ""; selectedId = id; }
        showWindow();
        articleScroll.contentY = 0;
    }
    function scrollBy(distance) {
        articleScroll.contentY = Math.max(0, Math.min(articleScroll.contentY + distance, articleScroll.contentHeight - articleScroll.height));
    }
    function openStep(route) { setupRequested(route); }
    function stepWelcome(delta) { welcomePage.step(delta); }
    // The first-login welcome, opened by the shell once it has read the saved state.
    function showWelcome(pending) {
        showAtLogin = pending;
        if (opened) return;
        show(welcomeChapter);
        welcomeShown = true;
    }
    function activateLink(link) {
        var target = Model.linkTarget(link, chapters);
        if (target.chapter) choose(target.chapter);
        else if (target.external) Qt.openUrlExternally(target.external);
    }
    CurrentWallpaper { id: wallpaper; live: book.opened }
    FileView {
        id: catalog
        path: Quickshell.shellDir + "/handbook/" + (Eitr.I18n.locale === "en" ? "catalog.json" : "catalogs/" + Eitr.I18n.locale + ".json")
        watchChanges: true
        onFileChanged: reload()
        printErrors: false
        onLoaded: { book.pendingCatalog = text(); book.applyCatalog(); }
        onLoadFailed: book.loadError = Eitr.I18n.tr("The handbook is missing. Reinstall or update the Eitr desktop files.")
    }
    property string pendingCatalog: ""
    function applyCatalog() {
        if (!pendingCatalog || (reveal > 0 && reveal < 1)) return;
        try {
            const data = JSON.parse(pendingCatalog);
            if (JsonState.changed(chapters, data.chapters)) chapters = data.chapters;
            pendingCatalog = "";
            loadError = "";
            if (selectedIndex < 0 && chapters.length) selectedId = chapters[0].id;
        } catch (error) { loadError = Eitr.I18n.tr("The handbook catalog is invalid."); }
    }
    onRevealChanged: if (reveal === 0 || reveal === 1) catalogSettled.restart()
    Timer { id: catalogSettled; interval: 0; onTriggered: book.applyCatalog() }
    Timer { id: focusDelay; interval: 80; onTriggered: if (book.opened) sidebar.searchField.forceActiveFocus() }
    IpcHandler {
        target: "handbook"
        function toggle(): void { book.toggle(); }
        function open(chapter: string): void { book.show(chapter); }
        function close(): void { book.opened = false; }
        function scroll(y: int): void { articleScroll.contentY = Math.max(0, Math.min(y, articleScroll.contentHeight - articleScroll.height)); }
        function status(): string { return JSON.stringify({opened: book.opened, chapter: book.selectedId, chapters: book.chapters.length, scroll: articleScroll.contentY, error: book.loadError}); }
    }
    Item {
        id: inputRoot
        anchors.fill: parent
        focus: book.opened
        enabled: book.opened
        Keys.priority: Keys.BeforeItem
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Escape) { book.opened = false; event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_F) { sidebar.searchField.forceActiveFocus(); sidebar.searchField.selectAll(); event.accepted = true; }
            else if (event.key === Qt.Key_PageDown) { book.scrollBy(articleScroll.height * 0.9); event.accepted = true; }
            else if (event.key === Qt.Key_PageUp) { book.scrollBy(-articleScroll.height * 0.9); event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_Home) { book.scrollBy(-articleScroll.contentHeight); event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_End) { book.scrollBy(articleScroll.contentHeight); event.accepted = true; }
            else if ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_Left && book.selectedIndex > 0) { book.choose(book.chapters[book.selectedIndex - 1].id); event.accepted = true; }
            else if ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_Right && book.selectedIndex + 1 < book.chapters.length) { book.choose(book.chapters[book.selectedIndex + 1].id); event.accepted = true; }
            else if (book.welcomeVisible && !event.modifiers && (event.key === Qt.Key_Left || event.key === Qt.Key_Right)) { book.stepWelcome(event.key === Qt.Key_Left ? -1 : 1); event.accepted = true; }
        }
        Rectangle {
            id: surface
            anchors.fill: parent
            color: book.color
            opacity: book.reveal
            MouseArea { anchors.fill: parent; onClicked: {} }
            FamilySidebar {
                id: sidebar
                width: Math.min(260, surface.width * 0.31)
                anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                anchors.margins: PanelStyle.padding
                foreground: book.ink; background: book.color; accent: SettingsPalette.accent
                subtitle: Eitr.I18n.tr("Handbook")
                closeName: Eitr.I18n.tr("Close handbook")
                placeholder: Eitr.I18n.tr("Search the handbook…")
                query: book.query
                entries: Model.sidebarEntries(book.chapters, book.filtered, book.query ? Eitr.I18n.tr("Results") : "")
                currentId: book.selectedId
                highlighted: searchField.activeFocus && book.query !== "" ? book.pick : -1
                emptyText: book.chapters.length ? Eitr.I18n.tr("No matching chapters") : ""
                onChosen: entry => { book.pick = Math.max(0, book.filtered.findIndex(chapter => chapter.id === entry.id)); book.choose(entry.id); }
                onCloseRequested: book.opened = false
                onSearchEdited: text => { book.query = text; book.pick = 0; }
                onSearchAccepted: if (book.filtered.length) book.choose(book.filtered[Math.min(book.pick, book.filtered.length - 1)].id)
                onSearchKey: event => {
                    if (event.key === Qt.Key_Down) { book.pick = Math.min(book.filtered.length - 1, book.pick + 1); event.accepted = true; }
                    else if (event.key === Qt.Key_Up) { book.pick = Math.max(0, book.pick - 1); event.accepted = true; }
                }
            }
            Rectangle { x: sidebar.x + sidebar.width + PanelStyle.padding; width: 1; height: parent.height; color: Qt.alpha(book.ink, PanelStyle.dividerAlpha) }
            Flickable {
                id: articleScroll
                x: sidebar.x + sidebar.width + PanelStyle.padding * 3; y: PanelStyle.padding
                width: surface.width - x - PanelStyle.padding
                height: surface.height - y - 62
                contentHeight: article.height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {
                    width: 4; policy: ScrollBar.AsNeeded
                    contentItem: Rectangle { radius: 2; color: Qt.alpha(book.ink, 0.25) }
                }
                Column {
                    id: article
                    width: articleScroll.width - 16
                    spacing: 16
                    FamilyPageHeader {
                        visible: !!book.chapter && !book.welcomeVisible
                        foreground: book.ink
                        rune: book.chapterGroup.rune
                        group: book.chapterGroup.name
                        title: book.chapter ? book.chapter.title : ""
                        description: book.chapter ? book.chapter.summary || "" : ""
                    }
                    WelcomePage {
                        id: welcomePage
                        visible: book.welcomeVisible
                        welcome: book.chapter && book.chapter.welcome || ({})
                        artSource: wallpaper.source
                        caption: book.chapterGroup.rune + "  " + book.chapterGroup.name.toLocaleUpperCase()
                        moreTitles: Model.sectionTitles(Model.articleBlocks(book.chapter))
                        active: book.opened && book.welcomeVisible
                        foreground: book.ink; background: book.color; accent: SettingsPalette.accent
                        showAtLogin: book.showAtLogin
                        offerProblemReports: book.offerProblemReports
                        onSetupRequested: route => book.openStep(route)
                        onShowAtLoginToggled: checked => { book.showAtLogin = checked; book.welcomeChoice(checked ? "remind" : "dismiss"); }
                        onProblemReportsToggled: checked => { book.offerProblemReports = checked; book.problemReportsChoice(checked); }
                    }
                    Text { visible: book.loadError !== ""; width: parent.width; wrapMode: Text.Wrap; text: book.loadError; color: book.ink; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                    Column {
                        visible: !book.welcomeVisible || welcomePage.expanded
                        width: parent.width
                        spacing: 12
                        Repeater {
                            model: Model.articleBlocks(book.chapter)
                            Rectangle {
                                id: block
                                required property string modelData
                                readonly property bool framed: /^<(pre|table)>/.test(modelData)
                                width: parent.width
                                height: blockText.contentHeight + (framed ? 28 : 0)
                                color: framed ? SettingsPalette.surface : "transparent"
                                border.width: framed ? 1 : 0
                                border.color: SettingsPalette.line
                                radius: DesktopStyle.radius(10)
                                TextEdit {
                                    id: blockText
                                    x: block.framed ? 14 : 0; y: block.framed ? 14 : 0
                                    width: parent.width - 2 * x
                                    height: contentHeight
                                    topPadding: /^<h[2-6]/.test(block.modelData) ? 12 : 0
                                    text: Model.readableHtml(block.modelData, String(SettingsPalette.accent), book.selectedId === "shortcuts", "", book.htmlStyle)
                                    textFormat: TextEdit.RichText
                                    renderType: TextEdit.NativeRendering
                                    baseUrl: Qt.resolvedUrl("../handbook/")
                                    readOnly: true; selectByMouse: true; cursorVisible: false
                                    wrapMode: TextEdit.Wrap
                                    color: book.ink
                                    selectionColor: SettingsPalette.accent
                                    selectedTextColor: PanelStyle.readableInk(SettingsPalette.accent, book.ink, book.color)
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.bodySize
                                    onLinkActivated: link => book.activateLink(link)
                                    HoverHandler { enabled: book.opened; cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.IBeamCursor }
                                }
                            }
                        }
                    }
                    Repeater {
                        model: book.chapter ? book.chapter.figures || [] : []
                        Column {
                            required property var modelData
                            width: article.width
                            spacing: 8
                            Image {
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: Math.min(parent.width, sourceSize.width)
                                height: Math.min(320, width * sourceSize.height / Math.max(1, sourceSize.width))
                                fillMode: Image.PreserveAspectFit
                                source: Qt.resolvedUrl("../handbook/" + parent.modelData.src)
                                asynchronous: true
                                Rectangle { anchors.fill: parent; color: "transparent"; radius: DesktopStyle.radius(6); border.width: 1; border.color: SettingsPalette.line }
                            }
                            Text { width: parent.width; text: parent.modelData.caption; wrapMode: Text.Wrap; color: SettingsPalette.muted; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        }
                    }
                }
            }
            Row {
                x: articleScroll.x; y: surface.height - 48
                spacing: 8
                PanelButton { width: 100; height: 32; text: Eitr.I18n.tr("Previous"); foreground: book.ink; outlined: true; available: book.selectedIndex > 0; onClicked: book.choose(book.chapters[book.selectedIndex - 1].id) }
                PanelButton { width: 100; height: 32; text: Eitr.I18n.tr("Next"); foreground: book.ink; outlined: true; available: book.selectedIndex >= 0 && book.selectedIndex + 1 < book.chapters.length; onClicked: book.choose(book.chapters[book.selectedIndex + 1].id) }
                Text { visible: articleScroll.width > 620; height: 32; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("PgUp/PgDn to scroll · Escape or × to close"); color: SettingsPalette.muted; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            }
        }
    }
}
