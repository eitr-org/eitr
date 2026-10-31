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

// The handbook overlay. It closes only from its close button, Escape or its
// shortcut, never from a click beside it. Its first chapter doubles as the
// first-login welcome: reader controls above the text ask the shell to open
// existing setup workflows. The reader itself runs nothing.
PanelWindow {
    id: book
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property real reveal: opened ? 1 : 0
    property var chapters: []
    property string selectedId: "getting-started"
    property string query: ""
    property string loadError: ""
    readonly property var filtered: Model.matches(chapters, query)
    readonly property int selectedIndex: chapters.findIndex(chapter => chapter.id === selectedId)
    readonly property var chapter: selectedIndex >= 0 ? chapters[selectedIndex] : null
    readonly property string codeBackground: String(Qt.alpha(foreground, 0.08))
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
    visible: opened || reveal > 0
    color: "transparent"
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-handbook"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    Behavior on reveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
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
        opened = true;
        articleScroll.contentY = 0;
    }
    function scrollBy(distance) {
        articleScroll.contentY = Math.max(0, Math.min(articleScroll.contentY + distance, articleScroll.contentHeight - articleScroll.height));
    }
    // A setup step closes the handbook, then opens its workflow once the overlay is gone.
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
        function toggle(): void { book.opened = !book.opened; }
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
            anchors.centerIn: parent
            width: Math.max(1, Math.min(1100, parent.width - 48))
            height: Math.max(1, Math.min(800, parent.height - 64))
            radius: DesktopStyle.radius(PanelStyle.cornerRadius)
            color: book.background
            opacity: book.reveal
            scale: 0.97 + 0.03 * book.reveal
            transform: Translate { y: 18 * (1 - book.reveal) }
            border.width: 1
            border.color: Qt.alpha(book.foreground, 0.12)
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
                    layer.effect: MultiEffect { colorization: 1; colorizationColor: book.foreground }
                }
                PanelHeading { x: 38; width: parent.width - 80; seal: false; text: Eitr.I18n.tr("EITR Handbook"); foreground: book.foreground; accent: book.accent; anchors.verticalCenter: parent.verticalCenter }
                PanelButton { width: 34; height: 34; text: "󰅖"; icon: true; foreground: book.foreground; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; Accessible.name: Eitr.I18n.tr("Close handbook"); onClicked: book.opened = false }
            }
            PanelDivider { x: PanelStyle.padding; y: header.y + header.height + 8; width: parent.width - 2 * x; height: 8; foreground: book.foreground }
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
                    color: book.foreground
                    placeholderTextColor: Qt.alpha(book.foreground, 0.5)
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.alpha(book.foreground, 0.08) }
                    onTextEdited: { book.query = text; chapterList.currentIndex = 0; }
                    onAccepted: if (book.filtered.length) book.choose(book.filtered[Math.max(0, chapterList.currentIndex)].id)
                    Keys.onDownPressed: { chapterList.currentIndex = Math.min(book.filtered.length - 1, chapterList.currentIndex + 1); chapterList.positionViewAtIndex(chapterList.currentIndex, ListView.Contain); }
                    Keys.onUpPressed: { chapterList.currentIndex = Math.max(0, chapterList.currentIndex - 1); chapterList.positionViewAtIndex(chapterList.currentIndex, ListView.Contain); }
                }
                ListView {
                    id: chapterList
                    anchors.top: search.bottom; anchors.topMargin: 12; anchors.bottom: parent.bottom
                    width: parent.width
                    model: book.filtered
                    clip: true
                    spacing: PanelStyle.selectionRowGap
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        contentItem: Rectangle { implicitWidth: 4; implicitHeight: 4; radius: 2; color: Qt.alpha(book.foreground, 0.35) }
                    }
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        width: chapterList.width - 8; height: PanelStyle.selectionRowHeight
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: Qt.alpha(book.foreground, PanelStyle.selectionAlpha(book.selectedId === modelData.id,
                            chapterMouse.containsMouse || search.activeFocus && book.query !== "" && chapterList.currentIndex === index))
                        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.icon; color: book.foreground; font.family: PanelStyle.fontFamily; font.pixelSize: PanelStyle.headingSize }
                        Text { x: 36; width: parent.width - 46; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.title; elide: Text.ElideRight; color: book.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                        MouseArea { id: chapterMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { chapterList.currentIndex = parent.index; book.choose(parent.modelData.id); } }
                    }
                    Text { visible: book.filtered.length === 0; width: parent.width; text: Eitr.I18n.tr("No matching chapters"); wrapMode: Text.Wrap; color: book.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                }
            }
            Rectangle { x: sidebar.x + sidebar.width + 12; y: sidebar.y; width: 1; height: sidebar.height; color: Qt.alpha(book.foreground, PanelStyle.dividerAlpha) }
            Flickable {
                id: articleScroll
                x: sidebar.x + sidebar.width + 30; y: sidebar.y
                width: surface.width - x - PanelStyle.padding
                height: surface.height - y - 62
                contentHeight: article.height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {
                    contentItem: Rectangle { implicitWidth: 4; implicitHeight: 4; radius: 2; color: Qt.alpha(book.foreground, 0.35) }
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
                                PanelButton {
                                    required property var modelData
                                    width: (welcomeSetup.width - PanelStyle.selectionRowGap) / 2
                                    text: modelData.label
                                    leadingIcon: modelData.icon
                                    textAlignment: Text.AlignLeft
                                    foreground: book.foreground
                                    onClicked: book.openStep(modelData.kind)
                                }
                            }
                        }
                        Row {
                            width: parent.width
                            Text {
                                width: parent.width - loginSwitch.width
                                height: loginSwitch.height
                                verticalAlignment: Text.AlignVCenter
                                text: Eitr.I18n.tr("Show this welcome at the next login")
                                color: book.foreground
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                            }
                            PanelSwitch {
                                id: loginSwitch
                                objectName: "handbookShowAtLoginSwitch"
                                checked: book.showAtLogin
                                foreground: book.foreground
                                accent: book.accent
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
                                    color: book.foreground
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.bodySize
                                }
                                Text {
                                    width: parent.width
                                    wrapMode: Text.Wrap
                                    text: Eitr.I18n.tr("Nothing is sent automatically. You read each report first and choose whether to email it or open a GitHub issue; your name, computer name and network addresses are removed.")
                                    color: book.foreground
                                    opacity: 0.65
                                    font.family: DesktopFonts.family
                                    font.pixelSize: PanelStyle.captionSize
                                }
                            }
                            PanelSwitch {
                                id: reportsSwitch
                                objectName: "handbookProblemReportsSwitch"
                                anchors.verticalCenter: parent.verticalCenter
                                checked: book.offerProblemReports
                                foreground: book.foreground
                                accent: book.accent
                                onToggled: { book.offerProblemReports = checked; book.problemReportsChoice(checked); }
                            }
                        }
                        PanelDivider { width: parent.width; height: 8; foreground: book.foreground }
                    }
                    Text { visible: book.loadError !== ""; width: parent.width; wrapMode: Text.Wrap; text: book.loadError; color: book.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                    Column {
                        width: parent.width
                        spacing: 12
                        Repeater {
                            model: book.chapter ? book.chapter.blocks || [] : []
                            TextEdit {
                                required property string modelData
                                width: parent.width
                                height: contentHeight
                                topPadding: /^<h[2-6]/.test(modelData) ? 12 : 0
                                text: Model.readableHtml(modelData, String(book.accent), book.selectedId === "shortcuts", book.codeBackground)
                                textFormat: TextEdit.RichText
                                renderType: TextEdit.NativeRendering
                                baseUrl: Qt.resolvedUrl("../handbook/")
                                readOnly: true; selectByMouse: true; cursorVisible: false
                                wrapMode: TextEdit.Wrap
                                color: book.foreground
                                selectionColor: book.accent
                                selectedTextColor: Qt.rgba(book.background.r, book.background.g, book.background.b, 1)
                                font.family: DesktopFonts.family
                                font.pixelSize: PanelStyle.bodySize
                                onLinkActivated: link => book.activateLink(link)
                                HoverHandler { enabled: book.opened; cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.IBeamCursor }
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
                            }
                            Text { width: parent.width; text: parent.modelData.caption; wrapMode: Text.Wrap; color: book.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        }
                    }
                }
            }
            Row {
                x: articleScroll.x; y: surface.height - 48
                spacing: 8
                PanelButton { width: 100; height: 32; text: Eitr.I18n.tr("Previous"); foreground: book.foreground; available: book.selectedIndex > 0; onClicked: book.choose(book.chapters[book.selectedIndex - 1].id) }
                PanelButton { width: 100; height: 32; text: Eitr.I18n.tr("Next"); foreground: book.foreground; available: book.selectedIndex >= 0 && book.selectedIndex + 1 < book.chapters.length; onClicked: book.choose(book.chapters[book.selectedIndex + 1].id) }
                Text { visible: articleScroll.width > 400; height: 32; verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("PgUp/PgDn to scroll · Escape or × to close"); color: book.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
            }
        }
    }
}
