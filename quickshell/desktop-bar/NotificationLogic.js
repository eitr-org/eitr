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
