"""The installer's Language step: the languages on offer, the AI-translation note and the locale each one installs."""
import os

from eitr_i18n import languages, mark, translator, use_locale
from eitr_input_methods import PRESETS as INPUT_METHOD_PRESETS, preset_for_locale
from eitr_language import LOCALES
from eitr_textwidth import wrap_text

# Set by the graphical installer terminal (distro/archinstall/eitr-installer-launch).
# The Linux console cannot draw Japanese, Chinese or Korean, so without it those
# languages are listed by English name and the wizard stays in English.
GRAPHICAL_VARIABLE = "EITR_INSTALLER_GRAPHICAL"
CONSOLE_NAMES = {"ja": "Japanese", "zh_CN": "Chinese (Simplified)", "ko": "Korean"}
TRANSLATION_NOTE = mark("Eitr's translations were made with AI and may have small mistakes. Corrections are always welcome.")


def graphical_terminal(environment=None):
    return (os.environ if environment is None else environment).get(GRAPHICAL_VARIABLE) == "1"


def language_options(graphical):
    """(label, language) rows: English first, then the others in languages.json order."""
    supported = languages()
    order = ["en", *(key for key in supported if key != "en")]
    return [(supported[key]["nativeName"] if graphical or key not in CONSOLE_NAMES else CONSOLE_NAMES[key], key)
            for key in order if key in LOCALES]


def drawable_language(key, graphical):
    """The language the wizard itself may be shown in after picking key."""
    return key if graphical or key not in CONSOLE_NAMES else "en"


def language_note(key, graphical, width):
    """The note for the highlighted language, translated into it where the screen can draw it."""
    if key == "en":
        return []
    return wrap_text(translator(drawable_language(key, graphical)).gettext(TRANSLATION_NOTE), width)


def select_language(wizard, title, current, graphical):
    """Ask for the language, then show the rest of the wizard in it; returns (language, system locale)."""
    options = language_options(graphical)
    wizard.choice_index = next((index for index, (_, key) in enumerate(options) if key == current), 0)
    try:
        key = wizard.choose(title, options,
                            details=lambda highlighted: language_note(highlighted, graphical, wizard.body_width))
    finally:
        wizard.choice_index = 0
    use_locale(drawable_language(key, graphical))
    return key, LOCALES[key]


def select_input_method(wizard, key, graphical):
    """When a CJK language is chosen, offer its optional fcitx5 input method."""
    preset_id = preset_for_locale(key)
    if not preset_id:
        return ""
    preset = INPUT_METHOD_PRESETS[preset_id]
    active = translator(drawable_language(key, graphical))
    label = active.gettext(preset["label"])
    options = [
        (active.gettext(mark("Install {label} (recommended for typing)")).format(label=label), preset_id),
        (active.gettext(mark("Skip for now")), ""),
    ]
    note = wrap_text(
        active.gettext(mark("Installs fcitx5 and {label}. Ctrl + Space toggles input; you can also install this later from Install > Input Methods.")).format(label=label),
        wizard.body_width,
    )
    return wizard.choose(active.gettext(mark("Input method")), options, details=lambda highlighted: note)
