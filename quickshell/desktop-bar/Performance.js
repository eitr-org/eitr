function wallpaperInterval(hasWindows) { return hasWindows ? 200 : 50; }
function workspaceHasWindows(windows, workspaceId) {
    return windows.some(window => window.workspace && window.workspace.id === workspaceId);
}
function obsPolling(hasWindow, running, detailObservers) { return detailObservers === 0 && (hasWindow || running); }
if (typeof module !== "undefined") module.exports = {wallpaperInterval, workspaceHasWindows, obsPolling};
