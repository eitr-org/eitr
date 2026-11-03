import ".."
import Eitr as Eitr
import QtQuick
import "../JsonState.js" as JsonState
import QtQuick.Effects
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle
import "../HandbookModel.js" as Model

// Offline, read-only reader and first-login welcome in a remembered native window.
LibraryWindow {
    id: book
    required property color foreground
    required property color background
    required property color accent
    readonly property real reveal: opened ? 1 : 0
    color: SiteStyle.bg
    stateName: "handbook"
    title: "EITR Handbook"
    property var chapters: []
    property string selectedId: "getting-started"
    property string query: ""
    property string loadError: ""
    readonly property var filtered: Model.matches(chapters, query)
    readonly property int selectedIndex: chapters.findIndex(chapter => chapter.id === selectedId)
    readonly property var chapter: selectedIndex >= 0 ? chapters[selectedIndex] : null
    readonly property string codeBackground: String(SiteStyle.surface)
    readonly property string welcomeChapter: "getting-started"
    readonly property var setupSteps: [
        {kind: "theme", icon: "󰸌", label: Eitr.I18n.tr("Choose a theme")},
        {kind: "wallpaper", icon: "󰋩", label: Eitr.I18n.tr("Pick a wallpaper")},
        {kind: "display", icon: "󰍹", label: Eitr.I18n.tr("Set the main display")},
        {kind: "keyboard", icon: "󰌌", label: Eitr.I18n.tr("Add keyboard layouts")},
        {kind: "wifi", icon: "", label: Eitr.I18n.tr("Connect to WiFi")},
        {kind: "bluetooth", icon: "", label: Eitr.I18n.tr("Pair Bluetooth devices")},
        {kind: "learn", icon: "󰧑", label: Eitr.I18n.tr("Learn shortcuts and gestures")}
    ]
    property bool showAtLogin: false
    property bool offerProblemReports: false
    property bool welcomeShown: false
    property string pendingStep: ""
    signal setupRequested(string kind)
    signal welcomeChoice(string action)
    signal problemReportsChoice(bool offer)
    onOpenedChanged: {
        if (opened) { focusDelay.restart(); return; }
        // Closing the automatic welcome without asking to see it again dismisses it for good.
        if (welcomeShown && !showAtLogin) welcomeChoice("dismiss");
        welcomeShown = false;
    }
    onVisibleChanged: {
        if (visible || pendingStep === "") return;
        setupRequested(pendingStep);
        pendingStep = "";
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
    // A setup step closes the handbook, then opens its workflow once the window is gone.
    function openStep(kind) {
        if (kind === "learn") { choose("shortcuts"); return; }
        pendingStep = kind;
        opened = false;
    }
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
    Timer { id: focusDelay; interval: 80; onTriggered: if (book.opened) search.forceActiveFocus() }
    IpcHandler {
        target: "handbook"
        function toggle(): void { book.toggle(); }
        function open(chapter: string): void { book.show(chapter); }
        function close(): void { book.opened = false; }
        function scroll(y: int): void { articleScroll.contentY = Math.max(0, Math.min(y, articleScroll.contentHeight - articleScroll.height)); }
        function status(): string { return JSON.stringify({opened: book.opened, chapter: book.selectedId, chapters: book.chapters.length, scroll: articleScroll.contentY, error: book.loadError}); }
    }
    component SiteButton: Rectangle {
        id: control
        property color foreground: SiteStyle.fg
        property string text: ""
        property string leadingIcon: ""
        property bool icon: false
        property bool available: true
        property int textAlignment: Text.AlignHCenter
        signal clicked()
        width: 100; height: 40; radius: 4
        enabled: available
        opacity: available ? 1 : 0.45
        activeFocusOnTab: true
        color: pointer.containsMouse || activeFocus ? SiteStyle.raised : SiteStyle.surface
        border.width: 1
        border.color: pointer.containsMouse || activeFocus ? SiteStyle.accent : SiteStyle.lineStrong
        Keys.onReturnPressed: clicked()
        Keys.onEnterPressed: clicked()
        Keys.onSpacePressed: clicked()
        Text {
            x: 10; width: parent.width - 20; height: parent.height
            verticalAlignment: Text.AlignVCenter; horizontalAlignment: control.textAlignment
            text: control.icon ? control.text : control.text.toUpperCase()
            color: control.foreground
            font.family: control.icon ? SiteStyle.mono : SiteStyle.carved
            font.pixelSize: control.icon ? 20 : 11
            font.letterSpacing: control.icon ? 0 : 1
            elide: Text.ElideRight
            leftPadding: control.leadingIcon ? 24 : 0
        }
        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: control.leadingIcon; color: control.foreground; font.family: SiteStyle.mono; font.pixelSize: 16 }
        MouseArea { id: pointer; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { control.forceActiveFocus(); control.clicked(); } }
    }
    Item {
        id: inputRoot
        anchors.fill: parent
        focus: book.opened
        enabled: book.opened
        Keys.priority: Keys.BeforeItem
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Escape) { book.opened = false; event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_F) { search.forceActiveFocus(); search.selectAll(); event.accepted = true; }
            else if (event.key === Qt.Key_PageDown) { book.scrollBy(articleScroll.height * 0.9); event.accepted = true; }
            else if (event.key === Qt.Key_PageUp) { book.scrollBy(-articleScroll.height * 0.9); event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_Home) { book.scrollBy(-articleScroll.contentHeight); event.accepted = true; }
            else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_End) { book.scrollBy(articleScroll.contentHeight); event.accepted = true; }
            else if ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_Left && book.selectedIndex > 0) { book.choose(book.chapters[book.selectedIndex - 1].id); event.accepted = true; }
            else if ((event.modifiers & Qt.AltModifier) && event.key === Qt.Key_Right && book.selectedIndex + 1 < book.chapters.length) { book.choose(book.chapters[book.selectedIndex + 1].id); event.accepted = true; }
        }
        Rectangle {
            id: surface
            anchors.fill: parent
            radius: 4
            color: SiteStyle.bg
            opacity: book.reveal
            border.width: 1
            border.color: SiteStyle.line
            MouseArea { anchors.fill: parent; onClicked: {} }
            Item {
                id: header
                x: PanelStyle.padding; y: PanelStyle.padding
                width: parent.width - 2 * x; height: 44
                Image {
                    width: 26; height: 26
                    anchors.verticalCenter: parent.verticalCenter
                    source: Quickshell.shellDir + "/assets/eitr-logo-white.svg"
                    fillMode: Image.PreserveAspectFit
                    // Drawn at its shown size: scaling the large SVG down afterwards leaves jagged edges.
                    sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
                    smooth: true
                    layer.enabled: true
                    layer.effect: MultiEffect { colorization: 1; colorizationColor: SiteStyle.fg }
                }
                Text { x: 38; width: parent.width - 80; text: Eitr.I18n.tr("EITR Handbook"); color: SiteStyle.fg; font.family: SiteStyle.serif; font.pixelSize: 32; elide: Text.ElideRight; anchors.verticalCenter: parent.verticalCenter }
                SiteButton { width: 34; height: 34; text: "󰅖"; icon: true; foreground: SiteStyle.fg; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; Accessible.name: Eitr.I18n.tr("Close handbook"); onClicked: book.opened = false }
            }
            PanelDivider { x: PanelStyle.padding; y: header.y + header.height + 8; width: parent.width - 2 * x; height: 8; foreground: SiteStyle.fg }
            Item {
                id: sidebar
                x: PanelStyle.padding; y: header.y + header.height + 22
                width: Math.min(250, surface.width * 0.30)
                height: surface.height - y - PanelStyle.padding
                TextField {
                    id: search
                    width: parent.width; height: 40
                    placeholderText: Eitr.I18n.tr("Search the handbook…")
                    text: book.query
                    color: SiteStyle.fg
                    placeholderTextColor: SiteStyle.muted
                    font.family: SiteStyle.mono; font.pixelSize: PanelStyle.bodySize
                    selectionColor: SiteStyle.accent
                    selectedTextColor: SiteStyle.bg
                    background: Rectangle { radius: 4; color: SiteStyle.surface; border.width: 1; border.color: search.activeFocus ? SiteStyle.accent : SiteStyle.lineStrong }
                    onTextEdited: { book.query = text; chapterList.currentIndex = 0; }
                    onAccepted: if (book.filtered.length) book.choose(book.filtered[Math.max(0, chapterList.currentIndex)].id)
                    Keys.onDownPressed: { chapterList.currentIndex = Math.min(book.filtered.length - 1, chapterList.currentIndex + 1); chapterList.positionViewAtIndex(chapterList.currentIndex, ListView.Contain); }
                    Keys.onUpPressed: { chapterList.currentIndex = Math.max(0, chapterList.currentIndex - 1); chapterList.positionViewAtIndex(chapterList.currentIndex, ListView.Contain); }
                }
                Text {
                    id: chapterGroup
                    anchors.top: search.bottom; anchors.topMargin: 16
                    text: book.query ? search.placeholderText.replace("…", "").toUpperCase() : Eitr.I18n.tr("EITR Handbook").toUpperCase()
                    color: SiteStyle.muted; font.family: SiteStyle.carved; font.pixelSize: 11; font.letterSpacing: 2
                }
                ListView {
                    id: chapterList
                    anchors.top: chapterGroup.bottom; anchors.topMargin: 12; anchors.bottom: parent.bottom
                    width: parent.width
                    model: book.filtered
                    clip: true
                    spacing: PanelStyle.selectionRowGap
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        contentItem: Rectangle { implicitWidth: 4; implicitHeight: 4; radius: 2; color: Qt.alpha(SiteStyle.fg, 0.35) }
                    }
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        width: chapterList.width - 8; height: PanelStyle.selectionRowHeight
                        radius: 4
                        color: book.selectedId === modelData.id ? SiteStyle.raised : chapterMouse.containsMouse || search.activeFocus && book.query !== "" && chapterList.currentIndex === index ? SiteStyle.surface : SiteStyle.bg
                        border.width: 1
                        border.color: book.selectedId === modelData.id ? SiteStyle.accent : SiteStyle.line
                        RectangularShadow {
                            anchors.fill: parent
                            radius: 4; blur: 18; spread: 2; color: SiteStyle.glow
                            visible: book.selectedId === modelData.id
                        }
                        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.icon; color: SiteStyle.fg; font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.headingSize }
                        Text { x: 36; width: parent.width - 46; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.title; elide: Text.ElideRight; color: SiteStyle.fg; font.family: SiteStyle.mono; font.pixelSize: PanelStyle.bodySize }
                        MouseArea { id: chapterMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { chapterList.currentIndex = parent.index; book.choose(parent.modelData.id); } }
                    }
                    Text { visible: book.filtered.length === 0; width: parent.width; text: Eitr.I18n.tr("No matching chapters"); wrapMode: Text.Wrap; color: SiteStyle.muted; font.family: SiteStyle.mono; font.pixelSize: PanelStyle.bodySize }
                }
            }
            Rectangle { x: sidebar.x + sidebar.width + 12; y: sidebar.y; width: 1; height: sidebar.height; color: SiteStyle.line }
            Flickable {
                id: articleScroll
                x: sidebar.x + sidebar.width + 30; y: sidebar.y
                width: surface.width - x - PanelStyle.padding
                height: surface.height - y - 62
                contentHeight: article.height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {
                    contentItem: Rectangle { implicitWidth: 4; implicitHeight: 4; radius: 2; color: Qt.alpha(SiteStyle.fg, 0.35) }
                }
                Column {
                    id: article
                    width: articleScroll.width - 16
                    spacing: 16
                    Column {
                        id: welcomeSetup
                        visible: book.selectedId === book.welcomeChapter && book.loadError === ""
                        width: parent.width
                        spacing: 12
                        Flow {
                            width: parent.width
                            spacing: PanelStyle.selectionRowGap
                            Repeater {
                                model: book.setupSteps
                                SiteButton {
                                    required property var modelData
                                    width: welcomeSetup.width < 540 ? welcomeSetup.width : (welcomeSetup.width - PanelStyle.selectionRowGap) / 2
                                    text: modelData.label
                                    leadingIcon: modelData.icon
                                    textAlignment: Text.AlignLeft
                                    foreground: SiteStyle.fg
                                    onClicked: book.openStep(modelData.kind)
                                }
                            }
                        }
                        Row {
                            width: parent.width
                            Text {
                                width: parent.width - loginSwitch.width
                                height: Math.max(implicitHeight, loginSwitch.height)
                                wrapMode: Text.Wrap
                                verticalAlignment: Text.AlignVCenter
                                text: Eitr.I18n.tr("Show this welcome at the next login")
                                color: SiteStyle.fg
                                font.family: SiteStyle.mono
                                font.pixelSize: PanelStyle.bodySize
                            }
                            PanelSwitch {
                                id: loginSwitch
                                objectName: "handbookShowAtLoginSwitch"
                                checked: book.showAtLogin
                                foreground: SiteStyle.fg
                                accent: SiteStyle.accent
                                onToggled: { book.showAtLogin = checked; book.welcomeChoice(checked ? "remind" : "dismiss"); }
                            }
                        }
                        Row {
                            width: parent.width
                            Column {
                                width: parent.width - reportsSwitch.width
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 2
                                Text {
                                    width: parent.width
                                    wrapMode: Text.Wrap
                                    text: Eitr.I18n.tr("Offer to report problems when something breaks")
                                    color: SiteStyle.fg
                                    font.family: SiteStyle.mono
                                    font.pixelSize: PanelStyle.bodySize
                                }
                                Text {
                                    width: parent.width
                                    wrapMode: Text.Wrap
                                    text: Eitr.I18n.tr("Nothing is sent automatically. You read each report first and choose whether to email it or open a GitHub issue; your name, computer name and network addresses are removed.")
                                    color: SiteStyle.muted
                                    font.family: SiteStyle.mono
                                    font.pixelSize: PanelStyle.captionSize
                                }
                            }
                            PanelSwitch {
                                id: reportsSwitch
                                objectName: "handbookProblemReportsSwitch"
                                anchors.verticalCenter: parent.verticalCenter
                                checked: book.offerProblemReports
                                foreground: SiteStyle.fg
                                accent: SiteStyle.accent
                                onToggled: { book.offerProblemReports = checked; book.problemReportsChoice(checked); }
                            }
                        }
                        PanelDivider { width: parent.width; height: 8; foreground: SiteStyle.fg }
                    }
                    Text { visible: book.loadError !== ""; width: parent.width; wrapMode: Text.Wrap; text: book.loadError; color: SiteStyle.fg; font.family: SiteStyle.mono; font.pixelSize: PanelStyle.bodySize }
                    Column {
                        width: parent.width
                        spacing: 12
                        Repeater {
                            model: book.chapter ? book.chapter.blocks || [] : []
                            Rectangle {
                                id: block
                                required property string modelData
                                readonly property bool framed: /^<(pre|table)>/.test(modelData)
                                width: parent.width
                                height: blockText.contentHeight + (framed ? 28 : 0)
                                color: framed ? SiteStyle.surface : SiteStyle.bg
                                border.width: framed ? 1 : 0
                                border.color: SiteStyle.line
                                radius: 3
                                TextEdit {
                                    id: blockText
                                    x: block.framed ? 14 : 0; y: block.framed ? 14 : 0
                                    width: parent.width - 2 * x
                                    height: contentHeight
                                    topPadding: /^<h[2-6]/.test(block.modelData) ? 12 : 0
                                    text: Model.readableHtml(block.modelData, String(SiteStyle.accent), book.selectedId === "shortcuts", book.codeBackground, SiteStyle)
                                    textFormat: TextEdit.RichText
                                    renderType: TextEdit.NativeRendering
                                    baseUrl: Qt.resolvedUrl("../handbook/")
                                    readOnly: true; selectByMouse: true; cursorVisible: false
                                    wrapMode: TextEdit.Wrap
                                    color: SiteStyle.fg
                                    selectionColor: SiteStyle.accent
                                    selectedTextColor: Qt.rgba(SiteStyle.bg.r, SiteStyle.bg.g, SiteStyle.bg.b, 1)
                                    font.family: SiteStyle.mono
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
                                Rectangle { anchors.fill: parent; color: "transparent"; border.width: 1; border.color: SiteStyle.lineStrong }
                            }
                            Text { width: parent.width; text: parent.modelData.caption; wrapMode: Text.Wrap; color: SiteStyle.muted; font.family: SiteStyle.mono; font.pixelSize: PanelStyle.captionSize }
                        }
                    }
                }
            }
            Row {
                x: articleScroll.x; y: surface.height - 48
                spacing: 8
                SiteButton { width: 100; height: 32; text: Eitr.I18n.tr("Previous"); foreground: SiteStyle.fg; available: book.selectedIndex > 0; onClicked: book.choose(book.chapters[book.selectedIndex - 1].id) }
                SiteButton { width: 100; height: 32; text: Eitr.I18n.tr("Next"); foreground: SiteStyle.fg; available: book.selectedIndex >= 0 && book.selectedIndex + 1 < book.chapters.length; onClicked: book.choose(book.chapters[book.selectedIndex + 1].id) }
                Text { visible: articleScroll.width > 620; height: 32; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("PgUp/PgDn to scroll · Escape or × to close"); color: SiteStyle.muted; font.family: SiteStyle.mono; font.pixelSize: PanelStyle.captionSize }
            }
        }
    }
}
