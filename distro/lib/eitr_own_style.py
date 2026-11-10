"""The user's own wallpapers, themes and lockscreens.

They live only on this computer, under $XDG_DATA_HOME/eitr/{wallpapers,themes,lockscreens}
(eitr_paths.own). Package updates, layout adoption and the theme generators never
write there, and nothing here uploads or shares them. Pictures come from a local
file or an https address; each is decoded before a copy is kept.
"""

# Keep existing callers on this interface; each helper has one implementation owner.
from eitr_own_pictures import (
    MAX_BYTES,
    MAX_PIXELS,
    MIN_SIDE,
    TIMEOUT,
    FORMATS,
    SUFFIXES,
    HEX,
    clean_name,
    slug,
    check_source,
    _HttpsOnly,
    download,
    picture_format,
    copy_image_hint,
    _PageImage,
    page_image,
    read_source,
    store_picture,
    source_stem,
    pictures_in,
    wallpapers,
    same_picture,
    add_wallpaper,
    own_wallpaper,
)
from eitr_own_palette import (
    KEY_ORDER,
    _module,
    palette_tools,
    _hex,
    hls,
    to_hls,
    mix,
    analyse,
    suggested_mode,
    _contrasting,
    brighter,
    generate_palette,
    render_colors,
)
from eitr_own_themes import (
    MARKER,
    DEFAULT_THEME,
    EDITABLE,
    YARU,
    KVANTUM,
    theme_builder,
    nearest,
    reference_integration,
    write_preview,
    write_theme_files,
    base_themes,
    own_themes,
    theme_dir,
    free_theme_name,
    create_theme,
    theme_colors,
    set_theme_color,
    delete_theme,
    fallback_theme,
)
from eitr_own_lockscreens import (
    LOCK_DESIGNS,
    LOCK_PREFIX,
    own_lockscreens,
    lockscreen,
    create_lockscreen,
    delete_lockscreen,
)
