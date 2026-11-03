"""Delete the retired hidden built-in themes list; every built-in theme shows again."""
from eitr_paths import state

state('eitr/hidden-themes.json').unlink(missing_ok=True)
