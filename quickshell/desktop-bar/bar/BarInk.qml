import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// The colour of text and icons drawn on the bar itself. Theme Color and Website use the
// theme's text colour. Blur and Clear show the wallpaper through the bar, so they keep it
// only while it stays readable over the wallpaper behind every region of the bar (measured by
// scripts/wallpaper-domain.py on the main bar's screen and edge); otherwise they switch to the
// theme's opposite colour, whichever reads better where the wallpaper is hardest. Panels and
// tooltips have their own surfaces and keep the theme's colours.
QtObject {
    id: ink
    required property var host
    // Contrast that ordinary bar text needs (WCAG AA for text).
    readonly property real readable: 4.5
    // How much of the theme's colour Blur lays over the wallpaper (shell.qml's bg).
    readonly property real tint: 0.38
    readonly property bool seeThrough: host.barAppearance === "transparent" || host.barAppearance === "clear"
    property var token: null
    readonly property var snapshot: DesktopData.topics["wallpaper.tone"] || ({})
    readonly property var monitors: (snapshot.data || {}).monitors || ({})
    readonly property string screenName: {
        const screen = host.targetScreens()[0];
        return screen ? screen.name : "";
    }
    readonly property var regions: {
        const entry = monitors[screenName];
        return entry && entry.edges ? entry.edges[host.barEdge] || [] : [];
    }

    function behind(region) {
        const wallpaper = Qt.color(region);
        if (host.barAppearance === "clear") return wallpaper;
        const theme = host.workspaceMenuBg;
        return Qt.rgba(wallpaper.r * (1 - tint) + theme.r * tint, wallpaper.g * (1 - tint) + theme.g * tint,
                       wallpaper.b * (1 - tint) + theme.b * tint, 1);
    }
    function contrast(surface, colour) {
        const first = PanelStyle.luminance(surface), second = PanelStyle.luminance(colour);
        return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
    }
    // How well a colour reads across the bar: the regions where it is readable, then the
    // contrast where it reads worst. A wallpaper that is pale on one side and dark on the
    // other cannot suit one colour everywhere; the one readable over more of the bar wins.
    function score(colour) {
        const contrasts = ink.regions.map(region => ink.contrast(ink.behind(region), colour));
        return contrasts.filter(value => value >= ink.readable).length * 100 + Math.min(...contrasts);
    }
    readonly property color colour: {
        if (!seeThrough || regions.length === 0) return host.fg;
        const opposite = Qt.rgba(host.workspaceMenuBg.r, host.workspaceMenuBg.g, host.workspaceMenuBg.b, 1);
        return score(opposite) > score(host.fg) ? opposite : host.fg;
    }

    function follow() {
        if (token !== null) DesktopData.release(token);
        token = seeThrough ? DesktopData.observe("wallpaper.tone", ink) : null;
    }
    onSeeThroughChanged: follow()
    Component.onCompleted: follow()
    Component.onDestruction: DesktopData.releaseOwner(ink)

    // A new wallpaper (or a per-display one) is measured once Hyprpaper shows it.
    readonly property Timer remeasure: Timer {
        interval: 1500
        onTriggered: if (ink.seeThrough) DesktopData.refresh("wallpaper.tone")
    }
    readonly property CurrentWallpaper wallpaper: CurrentWallpaper {
        live: ink.seeThrough
        onSourceChanged: ink.remeasure.restart()
    }
    readonly property FileView displayWallpapers: FileView {
        path: ink.seeThrough ? Eitr.Paths.config("eitr/wallpapers.json") : ""
        printErrors: false
        watchChanges: true
        onFileChanged: { reload(); ink.remeasure.restart(); }
    }
    readonly property Connections screens: Connections {
        target: ink.host
        function onBarEdgeChanged() { ink.remeasure.restart(); }
    }
}
