.pragma library
.import "SettingsCatalog.js" as Catalog

var pages = [
    {
        "group": "Overview",
        "id": "system",
        "title": "System",
        "description": "Your system at a glance.",
        "keywords": "hardware cpu gpu ram uptime profile avatar user"
    },
    {
        "group": "Devices",
        "id": "displays",
        "title": "Displays",
        "description": "Resolution, scaling and connected displays.",
        "keywords": "monitor refresh brightness rotation scale night light schedule temperature"
    },
    {
        "group": "Devices",
        "id": "sound",
        "title": "Sound",
        "description": "Output, input and event sounds.",
        "keywords": "audio microphone volume"
    },
    {
        "group": "Devices",
        "id": "connections",
        "title": "Connections",
        "description": "Connections, saved networks and Bluetooth devices.",
        "keywords": "network wifi wi-fi ethernet wireless bluetooth"
    },
    {
        "group": "Devices",
        "id": "streaming",
        "title": "Streaming",
        "description": "Share this PC with Sunshine or connect with Moonlight.",
        "keywords": "streaming sunshine moonlight remote game desktop sharing"
    },
    {
        "group": "Devices",
        "id": "input",
        "title": "Input",
        "description": "Keyboard layouts, mouse and touchpad.",
        "keywords": "keyboard pointer language"
    },
    {
        "group": "Desktop",
        "id": "appearance",
        "title": "Appearance",
        "description": "Theme, wallpaper, fonts and cursor.",
        "keywords": "style colors palette cursor fonts terminal opacity wallpaper"
    },
    {
        "group": "Desktop",
        "id": "bar",
        "title": "Desktop Bar",
        "description": "Layout, position and desktop bar controls.",
        "keywords": "clock islands tabs workspaces dots glyph numbers runes layout position media dock auto-hide"
    },
    {
        "group": "Desktop",
        "id": "windows",
        "title": "Windows",
        "description": "Window layout, gaps, corners and motion.",
        "keywords": "gaps corners rounded square shape animations effects tiling scrolling columns direction focus width"
    },
    {
        "group": "Desktop",
        "id": "lockscreen",
        "title": "Lockscreen",
        "description": "Lockscreen design and idle settings.",
        "keywords": "lock idle"
    },
    {
        "group": "Desktop",
        "id": "notifications",
        "title": "Notifications",
        "description": "Notification history and Do Not Disturb.",
        "keywords": "alerts dnd"
    },
    {
        "group": "Desktop",
        "id": "focus",
        "title": "Focus",
        "description": "A quiet desktop with tabs and panes.",
        "keywords": "split concentration"
    },
    {
        "group": "Apps & Keys",
        "id": "assistant",
        "title": "AI Assistant",
        "description": "Installed assistants and collaboration preferences.",
        "keywords": "ai usage assistants collaboration default access permissions accounts claude codex gemini grok copilot"
    },
    {
        "group": "Apps & Keys",
        "id": "keybinds",
        "title": "Keybinds",
        "description": "Browse the keyboard and mouse shortcuts.",
        "keywords": "shortcuts bindings keyboard mouse keys"
    },
    {
        "group": "Apps & Keys",
        "id": "default-apps",
        "title": "Default apps",
        "description": "Choose the apps used to open files and links.",
        "keywords": "browser terminal files file manager text editor image viewer video player music mail pdf mime"
    },
    {
        "group": "Accounts & Security",
        "id": "user",
        "title": "Users",
        "description": "Accounts on this PC, your picture and your password.",
        "keywords": "users login account accounts create profile picture display name password change"
    },
    {
        "group": "Accounts & Security",
        "id": "security",
        "title": "Security",
        "description": "Authentication, firewall and security tools.",
        "keywords": "fingerprint fido tpm firewall authentication"
    },
    {
        "group": "System",
        "id": "updates",
        "title": "Updates",
        "description": "System updates and the update channel.",
        "keywords": "packages upgrade stable testing"
    },
    {
        "group": "System",
        "id": "check-pc",
        "title": "Check This PC",
        "description": "Diagnostics and checks for this computer.",
        "keywords": "health troubleshooting"
    },
    {
        "group": "System",
        "id": "about",
        "title": "About",
        "description": "Eitr version and system information.",
        "keywords": "release version codename kernel licence license hardware website repository handbook"
    }
];

function score(label, keywords, query) {
    const text = label.toLocaleLowerCase();
    const needle = query.trim().toLocaleLowerCase();
    const words = needle.split(/\s+/);
    if (text === needle) return 400;
    if (text.startsWith(needle)) return 300;
    if (words.every(word => text.includes(word))) return 200;
    if (words.every(word => (text + " " + keywords.toLocaleLowerCase()).includes(word))) return 100;
    return 0;
}
function filter(query, translate) {
    if (!query.trim()) return pages.map(page => Object.assign({}, page, {destinationId: page.id}));
    const results = pages.map(page => Object.assign({}, page, {
        score: score(translate(page.title), [page.id, translate(page.description), translate(page.keywords)].join(" "), query),
        destinationId: searchDestination(page.id, query, translate)
    }));
    for (const setting of Catalog.settings) {
        const page = entry(setting.page);
        const tab = (tabs[setting.page] || []).find(candidate => candidate.id === setting.tab);
        results.push(Object.assign({}, page, {title: setting.label, settingId: setting.id,
            location: translate(page.title) + (tab ? " › " + translate(tab.label) : ""),
            score: score(translate(setting.label), setting.keywords, query),
            destinationId: setting.page + (setting.tab ? "/" + setting.tab : "") + "#" + setting.id}));
    }
    return results.filter(result => result.score > 0).sort((first, second) => second.score - first.score || translate(first.title).localeCompare(translate(second.title)));
}

var groups = [
    {name: "Overview", rune: "ᚠ"},
    {name: "Devices", rune: "ᚢ"},
    {name: "Desktop", rune: "ᚦ"},
    {name: "Apps & Keys", rune: "ᚨ"},
    {name: "Accounts & Security", rune: "ᚱ"},
    {name: "System", rune: "ᚲ"}
];
var pageRunes = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ", "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ"];
pages.forEach((page, index) => { page.rune = pageRunes[index]; });
function groupFor(page) { return groups.find(group => group.name === page.group) || groups[0]; }
function entry(identifier) { return pages.find(page => page.id === resolve(identifier).page) || pages[0]; }

var tabs = {
    user: [{id: "users", label: "Users", keywords: "profile picture password"}, {id: "manage", label: "Manage", keywords: "account administrator standard remove set password type"}],
    displays: [{id: "displays", label: "Displays", keywords: "monitor resolution brightness rotation scale"}, {id: "nightlight", label: "Night Light", keywords: "night light schedule temperature"}],
    connections: [{id: "wifi", label: "Wi-Fi", keywords: "wifi network backend wireless"}, {id: "bluetooth", label: "Bluetooth", keywords: "bluetooth pairing"}],
    appearance: [{id: "theme", label: "Theme & Wallpaper", keywords: "theme wallpaper palette"}, {id: "fonts", label: "Fonts & Cursor", keywords: "fonts cursor typography"}, {id: "terminal", label: "Terminal", keywords: "terminal opacity blur fire"}],
    assistant: [{id: "general", label: "General", keywords: "default assistant access collaboration work together"}, {id: "assistants", label: "Assistants", keywords: "claude codex copilot gemini grok opencode pi ratatoskr antigravity install open accounts"}, {id: "usage", label: "Usage", keywords: "ai usage limits session weekly refresh"}],
    bar: [{id: "layout", label: "Layout", keywords: "layout position show on screens edge"}, {id: "look", label: "Look", keywords: "appearance blur workspace style media clock"}, {id: "behaviour", label: "Behaviour", keywords: "auto-hide dock reduce motion keep expanded behavior"}],
    security: [{id: "sign-in", label: "Sign-in", keywords: "fingerprint fido security key authentication password-only"}, {id: "protection", label: "Protection", keywords: "firewall tpm disk unlock encryption"}]
};
function resolve(identifier) {
    const parts = String(identifier || "system").split("#")[0].split("/");
    const aliases = {assistants: "assistant", network: "connections", you: "system", "desktop-bar": "bar"};
    const page = aliases[parts[0]] || parts[0];
    const choices = tabs[page] || [];
    return {setting: String(identifier || "").split("#")[1] || "", page: pages.some(entry => entry.id === page) ? page : "system",
        tab: (choices.find(choice => choice.id === parts[1]) || choices[0] || {}).id || ""};
}
function searchDestination(page, query, translate) {
    const candidates = tabs[page] || [];
    const words = query.trim().toLocaleLowerCase().split(/\s+/);
    let match = null;
    let highest = 0;
    for (const tab of candidates) {
        const text = [translate(tab.label), tab.keywords].concat(Catalog.settings.filter(setting => setting.page === page && setting.tab === tab.id).map(setting => translate(setting.label))).join(" ").toLocaleLowerCase();
        const score = words.filter(word => word && text.includes(word)).length;
        if (score > highest) { match = tab; highest = score; }
    }
    return page + (match ? "/" + match.id : "");
}
