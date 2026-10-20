# shellcheck shell=bash

_eitr_i18n_owner="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/eitr_i18n.py"

eitr_gettext() {
    command python3 "$_eitr_i18n_owner" -- "$@"
}

eitr_ngettext() {
    local singular="$1" plural="$2" count="$3"
    command python3 "$_eitr_i18n_owner" --plural "$plural" --count "$count" -- "$singular"
}
