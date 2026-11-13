.pragma library

// Which display shows the login screen. Nobody is signed in yet, so the desktop's own
// Main display choice is unknown; like the desktop before a choice is saved, the
// largest display wins, the leftmost then topmost on a tie. A display missing from the
// list still shows the login screen, so it can never end up black everywhere.
function largest(screens) {
    var best = null;
    for (var index = 0; index < screens.length; index++) {
        var screen = screens[index];
        if (!best) { best = screen; continue; }
        var area = screen.width * screen.height, bestArea = best.width * best.height;
        if (area > bestArea || (area === bestArea && (screen.virtualX < best.virtualX
                || (screen.virtualX === best.virtualX && screen.virtualY < best.virtualY))))
            best = screen;
    }
    return best;
}

function isMain(name, screens) {
    if (!screens || screens.length < 2 || !name) return true;
    var known = false;
    for (var index = 0; index < screens.length; index++)
        if (screens[index].name === name) known = true;
    if (!known) return true;
    return largest(screens).name === name;
}
