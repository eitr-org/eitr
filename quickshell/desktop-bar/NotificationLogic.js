.pragma library

var thumbnailWidth = 160;
var thumbnailHeight = 120;

function imageSource(notification) {
    if (!notification) return "";
    // Use Qt's file loader/cache, not an icon-provider lookup for local images.
    var image = notification.image || "";
    var hints = notification.hints || {};
    var path = hints["image-path"] || hints.image_path || "";
    if (/^image:\/\/qs(image|pixmap)\//.test(image)) return image;
    if (path.charAt(0) === "/") return "file://" + encodeURI(path).replace(/#/g, "%23").replace(/\?/g, "%3F");
    if (path.indexOf("file:") === 0) return path;
    return image;
}

function imageIsPreview(notification, width, height) {
    if (!notification) return false;
    var identity = (notification.appName || "") + " " + (notification.desktopEntry || "");
    if (/\b(satty|flameshot|spectacle|shutter|swappy|screenshot)\b/i.test(identity)) return true;
    var category = notification.hints ? notification.hints.category || "" : "";
    // Chat/browser images commonly identify the sender, even when not square.
    if (/^(im|email)(\.|$)/i.test(category)
        || /\b(slack|discord|telegram|signal|whatsapp|chrome|chromium|firefox|brave)\b/i.test(identity)) return false;
    return width > 0 && height > 0 && Math.max(width / height, height / width) > 1.2;
}

function ignored(appName) {
    return /^(kitty|terminal)$/i.test(appName || "");
}

function popupDuration(notification) {
    if (notification.urgency === 2 || notification.expireTimeout === 0) return 0;
    return notification.expireTimeout > 0 ? notification.expireTimeout : 6500;
}

function grouped(notifications, timestamps, includeTransient) {
    var groups = {};
    notifications.filter(notification => includeTransient || !notification.transient).forEach(notification => {
        var name = notification.appName || "Application";
        if (!groups[name]) groups[name] = [];
        groups[name].push(notification);
    });
    return Object.keys(groups).sort((a, b) => {
        var newest = name => Math.max.apply(null, groups[name].map(notification => timestamps[notification.id] || 0));
        return newest(b) - newest(a);
    }).map(name => ({name: name, notifications: groups[name].sort((a, b) => (timestamps[b.id] || 0) - (timestamps[a.id] || 0) || b.id - a.id)}));
}

// Logos Eitr ships for tools that install no icon of their own (walker/icons/).
var shippedLogos = ["herdr", "cmux"];

// The app's icon, in order: the icon the notification names, the icon of its desktop
// entry, a logo Eitr ships for it; "" leaves the bell.
// `resolve(name)` answers an icon-theme name's source, or "" when the theme lacks it
// (Quickshell.iconPath(name, true)); a missing name would otherwise draw Qt's
// placeholder square. The app's own icon then stands in, as for KDE Connect's
// battery warnings, which name a battery icon the theme may not have.
function appIconSource(notification, entryIcon, logoRoot, resolve) {
    if (!notification) return "";
    function themed(name, filePrefix) {
        if (!name) return "";
        if (name.indexOf("/") === 0) return filePrefix + name;
        if (name.indexOf("/") !== -1 || name.indexOf(":") !== -1) return name;
        return resolve ? resolve(name) || "" : "image://icon/" + name;
    }
    var icon = themed(notification.appIcon || "", "") || themed(entryIcon || "", "file://");
    if (icon) return icon;
    var name = String(notification.appName || "").toLowerCase();
    return shippedLogos.indexOf(name) !== -1 && logoRoot ? "file://" + logoRoot + "/" + name + ".png" : "";
}

// Herdr names agents in lower case and adds its workspace number after the workspace
// name ("claude finished", "Doola · 1 · Automations"): show "Claude finished" over
// "Doola · Automations" (workspace, then the tab when it has a name).
var agentNames = {claude: "Claude", codex: "Codex", gemini: "Gemini", grok: "Grok", copilot: "Copilot",
    opencode: "OpenCode", pi: "Pi", agy: "Antigravity", cursor: "Cursor"};
function presentation(notification) {
    if (!notification) return {summary: "", body: ""};
    var summary = notification.summary || "", body = notification.body || "";
    if (/^herdr$/i.test(notification.appName || "")) {
        summary = summary.replace(/^(\S+)/, word => agentNames[word.toLowerCase()] || word.charAt(0).toUpperCase() + word.slice(1));
        body = body.split(" · ").filter(part => !/^\d+$/.test(part.trim())).join(" · ");
    }
    return {summary: summary, body: body};
}

// The command that opens the app behind a notification without an action of its own
// (scripts/notification-open.py), shared by a click and the keyboard shortcut.
function openCommand(notification, script) {
    var hints = notification.hints || {};
    return ["python3", script, "--app", notification.appName || "", "--desktop-entry", notification.desktopEntry || "",
        "--pid", String(Number(hints["sender-pid"]) || 0), "--body", notification.body || ""];
}
