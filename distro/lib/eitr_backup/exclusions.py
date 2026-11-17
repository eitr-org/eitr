"""Exclusion lists and layout-manifest classification rules for Eitr backups."""

BROWSER_DIRS = frozenset({
    "brave", "bravesoftware", "chromium", "chromium-beta", "chromium-dev",
    "epiphany", "falkon", "firefox", "floorp", "google-chrome",
    "google-chrome-beta", "google-chrome-canary", "google-chrome-unstable",
    "librewolf", "microsoft-edge", "microsoft-edge-beta", "microsoft-edge-dev",
    "midori", "mozilla", "netsurf", "opera", "opera-developer", "opera-gx",
    "thorium", "tor-browser", "torbrowser", "ungoogled-chromium", "vivaldi",
    "vivaldi-snapshot", "waterfox", "zen", "zen-browser",
})

SECRET_CONFIG_DIRS = frozenset({
    "aws", "azure", "gcloud", "gh", "git", "glab-cli", "gnupg", "yubico",
})

MACHINE_SETUP_PATHS = (
    "hypr/local.lua",
    "hypr/primary-display",
    "hypr/preferred-outputs",
)

PHASE4_EITR_CONFIG_EXCLUSIONS = frozenset({
    "eitr/git-accounts.json",
    "eitr/git-accounts",
    "eitr/cloud-contexts.json",
    "eitr/cloud-navigation.json",
    "eitr/cloud-accounts",
})

RUNTIME_EITR_CONFIG_ITEMS = (
    "eitr/appearance.json",
    "eitr/calendars",
    "eitr/cursor.json",
    "eitr/font.json",
    "eitr/lighting.json",
    "eitr/monitoring.json",
    "eitr/settings-app.json",
    "eitr/sounds.json",
    "eitr/style.json",
    "eitr/terminal.json",
    "environment.d/90-eitr-language.conf",
    "kitty/local.conf",
    "lockscreen/selected",
)

CACHE_DIR_EXACT = frozenset({
    "__pycache__", ".cache", ".trash", "cache", "caches", "cache_data",
    "cacheddata", "cachedextensions", "cachedextensionvsixs", "code cache",
    "crashpad", "dawngraphitecache", "dawnwebgpucache", "gpucache",
    "grshadercache", "shadercache", "trash",
})

LOCK_FILE_NAMES = frozenset({
    ".parentlock", "lock", "lockfile",
    "singletoncookie", "singletonlock", "singletonsocket",
})

EXCLUDED_FILE_SUFFIXES = (".lck", ".lock", ".pid", ".pyc", ".pyo", ".sock", ".socket")

NEVER_HOME_PREFIXES = (
    ".aws", ".azure", ".cache", ".floorp", ".gitconfig", ".gnupg",
    ".iceauthority", ".kube", ".librewolf", ".local/share/Trash",
    ".local/share/keyrings", ".local/state/eitr/layout-backups",
    ".local/state/eitr/restore-backups", ".local/state/eitr/restore-tmp",
    ".mozilla", ".ssh", ".waterfox", ".xauthority", ".zen",
)


def is_browser_dir(name):
    return name.casefold() in BROWSER_DIRS


def is_secret_config_dir(name):
    return name.casefold() in SECRET_CONFIG_DIRS


def is_excluded_dir_name(name, *, app_settings=False):
    folded = name.casefold()
    if folded in CACHE_DIR_EXACT:
        return True
    if app_settings and "cache" in folded:
        return True
    return False


def is_excluded_file_name(name):
    folded = name.casefold()
    return folded in LOCK_FILE_NAMES or folded.endswith(EXCLUDED_FILE_SUFFIXES)


def is_never_home_path(home_rel):
    folded = home_rel.casefold()
    for prefix in NEVER_HOME_PREFIXES:
        prefix_folded = prefix.casefold()
        if folded == prefix_folded or folded.startswith(prefix_folded + "/"):
            return True
    if folded.startswith(".config/"):
        cfg_parts = home_rel.removeprefix(".config/").split("/")
        top = cfg_parts[0]
        if is_browser_dir(top) or is_secret_config_dir(top):
            return True
        cfg_rel = "/".join(cfg_parts)
        for item in PHASE4_EITR_CONFIG_EXCLUSIONS:
            if cfg_rel == item or cfg_rel.startswith(item + "/"):
                return True
    return False


def classify_manifest_path(layout, config_rel=None, home_rel=None):
    """Return layout-manifest class ('C', 'D', 'G', 'P') or None when unclassified."""
    candidates = []
    if config_rel:
        candidates.append(config_rel)
    if home_rel and not home_rel.startswith(".config/"):
        candidates.append("HOME_FILES/" + home_rel)
    if home_rel and home_rel.startswith(".config/lockscreen/"):
        candidates.append("HOME_FILES/" + home_rel)
    for candidate in candidates:
        try:
            return layout.classify(candidate)["class"]
        except ValueError:
            continue
    return None


def is_shipped_or_generated(layout, home_rel):
    if home_rel.startswith(".config/"):
        cfg_rel = home_rel.removeprefix(".config/")
        return classify_manifest_path(layout, config_rel=cfg_rel, home_rel=home_rel) in {"C", "D", "G"}
    return classify_manifest_path(layout, home_rel=home_rel) in {"C", "D", "G"}


def eitr_owned_config_dirs(layout):
    dirs = {
        "btop", "cava", "eitr", "elephant", "environment.d", "fastfetch",
        "ghostty", "gtk-3.0", "gtk-4.0", "hypr", "kitty", "Kvantum",
        "lockscreen", "nvim", "qt5ct", "qt6ct", "quickshell", "swayosd",
        "systemd", "theme", "walker", "xdg-desktop-portal",
    }
    ignored_heads = {
        "*", "**", "distro", "HOME_FILES", "tools", "website", "docs",
        "branding", "i18n", "themes", "LICENSE", "*.md", ".gitattributes",
        ".gitignore", ".shellcheckrc",
    }
    for rule in layout.rules:
        head = rule["pattern"].split("/", 1)[0]
        if head not in ignored_heads and "/" in rule["pattern"]:
            dirs.add(head)
    return dirs
