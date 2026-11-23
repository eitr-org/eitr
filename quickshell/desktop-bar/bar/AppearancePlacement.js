.pragma library

function hostsCarousel(mode, edge, dropLayout, barOnScreen) {
    return (mode === "wallpaper" || mode.startsWith("theme"))
        && (edge === "top" || edge === "bottom") && dropLayout && barOnScreen;
}
