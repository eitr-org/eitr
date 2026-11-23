.pragma library

function hostsCarousel(mode, edge, dynamicLayout, dropLayout, barOnScreen) {
    return (mode === "wallpaper" || mode.startsWith("theme"))
        && (edge === "top" || edge === "bottom") && (dynamicLayout || dropLayout) && barOnScreen;
}
