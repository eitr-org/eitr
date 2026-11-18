"""Exclusion lists and layout-manifest classification rules for Eitr backups."""
from pathlib import PurePosixPath

from eitr_backup import BackupError
from eitr_i18n import tr

GPG_ARCHIVE_REL = ".gnupg/gpg-secret-keys.asc"
IWD_SUFFIXES = (".psk", ".8021x", ".open")
NM_SUFFIXES = (".nmconnection",)

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


# Short-lived cloud session caches skipped from cloud_accounts backups:
# - AWS: ~/.aws/sso/cache/**, ~/.aws/cli/cache/** (and under ~/.config/aws)
# - gcloud: ~/.config/gcloud/access_tokens.db*, ~/.config/gcloud/credentials.db*,
#   ~/.config/gcloud/legacy_credentials/**, ~/.config/gcloud/logs/**
# - Azure: ~/.azure/msal_token_cache*, ~/.azure/accessTokens.json,
#   ~/.azure/msal_http_cache*, ~/.azure/{logs,telemetry,commands}/** (and under ~/.config/azure)
# - Kubernetes: ~/.kube/cache/**, ~/.kube/http-cache/**
CLOUD_SKIPPED_CACHES = (
    ".aws/sso/cache", ".aws/cli/cache", ".config/aws/sso/cache", ".config/aws/cli/cache",
    ".config/gcloud/access_tokens.db*", ".config/gcloud/credentials.db*",
    ".config/gcloud/legacy_credentials", ".config/gcloud/logs",
    ".azure/msal_token_cache*", ".azure/accessTokens.json", ".azure/msal_http_cache*",
    ".azure/logs", ".azure/telemetry", ".azure/commands",
    ".config/azure/msal_token_cache*", ".config/azure/accessTokens.json", ".config/azure/msal_http_cache*",
    ".config/azure/logs", ".config/azure/telemetry", ".config/azure/commands",
    ".kube/cache", ".kube/http-cache",
)


def is_skipped_cloud_cache(home_rel):
    rel = home_rel.strip("/")
    if rel.startswith(".config/eitr/cloud-accounts/"):
        parts = PurePosixPath(rel).parts
        if len(parts) > 5 and is_skipped_cloud_cache("/".join(parts[5:])):
            return True
    for prefix in (".aws/", ".config/aws/"):
        if rel.startswith(prefix):
            sub = rel.removeprefix(prefix)
            if sub in ("sso/cache", "cli/cache") or sub.startswith(("sso/cache/", "cli/cache/")):
                return True
    if rel.startswith(".config/gcloud/"):
        head = PurePosixPath(rel.removeprefix(".config/gcloud/")).parts[0]
        if head in ("logs", "legacy_credentials") or head.startswith(("access_tokens.db", "credentials.db")):
            return True
    for prefix in (".azure/", ".config/azure/"):
        if rel.startswith(prefix):
            parts = PurePosixPath(rel.removeprefix(prefix)).parts
            if parts[0] in ("logs", "telemetry", "commands", "accessTokens.json"):
                return True
            if parts[0].startswith(("msal_token_cache", "msal_http_cache")) or parts[-1].startswith(("msal_token_cache", "msal_http_cache")):
                return True
    if rel.startswith(".kube/") and PurePosixPath(rel.removeprefix(".kube/")).parts[0] in ("cache", "http-cache"):
        return True
    return False


def validate_wifi_profile_name(backend, name):
    if backend not in ("iwd", "networkmanager"):
        raise BackupError(tr("Unsupported WiFi backend in backup: {backend}", backend=str(backend)))
    if not isinstance(name, str) or not name or len(name.encode("utf-8")) > 255:
        raise BackupError(tr("Unsafe WiFi profile filename rejected: {name}", name=str(name)))
    if "/" in name or "\\" in name or "\x00" in name or name in (".", "..") or ".." in name or name.startswith("."):
        raise BackupError(tr("Unsafe WiFi profile filename rejected: {name}", name=name))
    suffixes = IWD_SUFFIXES if backend == "iwd" else NM_SUFFIXES
    matched = next((suf for suf in suffixes if name.endswith(suf)), None)
    if not matched or len(name) <= len(matched):
        raise BackupError(tr("Unsupported WiFi profile filename rejected: {name}", name=name))
    return name


def validate_secret_archive_member(category, home_rel):
    parts = PurePosixPath(home_rel).parts
    if any(is_excluded_file_name(part) for part in parts) or any(is_excluded_dir_name(part) for part in parts[:-1]):
        raise BackupError(tr("Excluded cache or lock path rejected: {path}", path=home_rel))
    if category == "wifi_networks":
        if len(parts) != 2:
            raise BackupError(tr("Unexpected WiFi archive path rejected: {path}", path=home_rel))
        validate_wifi_profile_name(parts[0], parts[1])
        return "file", category, home_rel
    if category == "git_accounts":
        if home_rel in (".gitconfig", ".config/eitr/git-accounts.json", GPG_ARCHIVE_REL):
            return "file", category, home_rel
        if home_rel.startswith(".config/eitr/git-accounts/") and not home_rel.startswith(".config/eitr/git-accounts/cli/"):
            return "file", category, home_rel
        if home_rel.startswith(".ssh/") and len(parts) == 2:
            return "file", category, home_rel
        if not home_rel.startswith((".cache/", ".local/share/Trash/", ".local/share/keyrings/", ".mozilla/", ".zen/", ".floorp/")):
            if not (home_rel.startswith(".config/") and is_browser_dir(parts[1])) and (home_rel.endswith(".gitconfig") or ".ssh/" in home_rel):
                return "file", category, home_rel
        raise BackupError(tr("Unexpected Git accounts path rejected: {path}", path=home_rel))
    if category == "cloud_accounts":
        if is_skipped_cloud_cache(home_rel):
            raise BackupError(tr("Short-lived cloud login cache rejected from backup: {path}", path=home_rel))
        allowed_roots = (".aws/", ".config/aws/", ".config/gcloud/", ".azure/", ".config/azure/", ".kube/", ".config/eitr/cloud-accounts/")
        if home_rel in (".config/eitr/cloud-contexts.json", ".config/eitr/cloud-navigation.json") or home_rel.startswith(allowed_roots):
            return "file", category, home_rel
        raise BackupError(tr("Unexpected cloud accounts path rejected: {path}", path=home_rel))
    raise BackupError(tr("Unknown backup category rejected: {category}", category=category))
