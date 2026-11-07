.pragma library

// Settings snapshots contain applied trial values; topology supplies model and coordinates.
function screens(monitors, settings, pending) {
    return monitors.map(function(monitor) {
        const detail = (settings || []).find(function(item) { return item.name === monitor.name; }) || {};
        const values = Object.assign({}, monitor, detail, pending && pending.name === monitor.name ? pending : {});
        const mode = String(values.mode || (monitor.width || 1920) + "x" + (monitor.height || 1080)).split("@")[0].split("x");
        const scale = Math.max(0.25, Number(values.scale) || 1);
        const rotated = Number(values.transform || 0) % 2 === 1;
        const position = String(values.position || (Number(monitor.x) || 0) + "x" + (Number(monitor.y) || 0)).split("x");
        return {name: monitor.name, model: monitor.model || "", resolution: mode.join("×"),
            x: Number(position[0]) || 0, y: Number(position[1]) || 0,
            width: Math.max(1, Number(mode[rotated ? 1 : 0]) || 1920) / scale,
            height: Math.max(1, Number(mode[rotated ? 0 : 1]) || 1080) / scale,
            disabled: !!monitor.disabled, pending: !!pending && pending.name === monitor.name};
    });
}
function fit(screens, width, height, margin) {
    if (!screens.length) return [];
    const left = Math.min.apply(null, screens.map(function(screen) { return screen.x; }));
    const top = Math.min.apply(null, screens.map(function(screen) { return screen.y; }));
    const extentWidth = Math.max.apply(null, screens.map(function(screen) { return screen.x + screen.width; })) - left;
    const extentHeight = Math.max.apply(null, screens.map(function(screen) { return screen.y + screen.height; })) - top;
    const ratio = Math.max(0, Math.min((width - 2 * margin) / extentWidth, (height - 2 * margin) / extentHeight));
    return screens.map(function(screen) {
        return Object.assign({}, screen, {x: (width - extentWidth * ratio) / 2 + (screen.x - left) * ratio,
            y: (height - extentHeight * ratio) / 2 + (screen.y - top) * ratio,
            width: screen.width * ratio, height: screen.height * ratio});
    });
}
