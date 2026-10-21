# shellcheck shell=bash

# A subshell keeps cleanup traps local, including when the caller has an EXIT trap.
run_with_spinner() (
    local text="$1" status=0 animator='' output='' columns accent=${EITR_TERMINAL_ACCENT:-} tint=''
    shift
    if [[ ! -t 1 || ! -t 2 || -v NO_COLOR || ${TERM:-dumb} == dumb || ${EITR_NO_SPINNER:-} == 1 ]]; then
        printf '%s\n' "$text" >&2
        "$@"
        return $?
    fi
    output="$(mktemp -d)" || return 1
    mkfifo "$output/tick" || { rm -rf -- "$output"; return 1; }
    local tick
    # Keep both ends open so Bash can pace frames without spawning sleep.
    exec {tick}<>"$output/tick"
    columns="$(tput cols 2>/dev/null)" || columns=80
    [[ "$columns" =~ ^[0-9]+$ ]] && (( columns > 1 )) || columns=80
    if [[ "$accent" =~ ^#[[:xdigit:]]{6}$ ]]; then
        printf -v tint '\033[38;2;%d;%d;%dm' "$((16#${accent:1:2}))" "$((16#${accent:3:2}))" "$((16#${accent:5:2}))"
    fi
    cleanup_spinner() {
        if [[ -n "$animator" ]]; then
            kill "$animator" 2>/dev/null || true
            wait "$animator" 2>/dev/null || true
        fi
        printf '\r\033[2K\033[?25h' >&2
        [[ -z "$output" ]] || rm -rf -- "$output"
    }
    trap cleanup_spinner EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    # Translating starts Python, so only the phrase on screen is translated, inside
    # the animation; the command itself never waits for it.
    spinner_phrase() {
        case "$1" in
        0) eitr_gettext 'consulting the Norns' ;;
        1) eitr_gettext 'asking Huginn and Muninn' ;;
        2) eitr_gettext 'reading the runes' ;;
        3) eitr_gettext 'crossing Bifröst' ;;
        4) eitr_gettext 'waking Yggdrasil' ;;
        5) eitr_gettext 'feeding the ravens' ;;
        6) eitr_gettext 'sharpening the axes' ;;
        7) eitr_gettext 'counting the einherjar' ;;
        8) eitr_gettext 'polishing Mjölnir' ;;
        9) eitr_gettext "listening at Mímir's well" ;;
        10) eitr_gettext 'checking the longships' ;;
        11) eitr_gettext 'untangling fate' ;;
        12) eitr_gettext 'following the northern star' ;;
        13) eitr_gettext 'warming the mead' ;;
        14) eitr_gettext 'greeting the Valkyries' ;;
        15) eitr_gettext 'finding the hidden fjord' ;;
        esac
    }
    (
        trap 'exit 0' TERM INT
        local frame=0 started=$SECONDS phrase='' elapsed suffix line position stop next mix character frame_text colour lead truecolor=0
        local -a runes=(ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ)
        local -a red=(224 232 230 127 111 169) green=(92 147 195 201 168 139) blue=(104 90 106 143 220 214)
        [[ ${COLORTERM:-} == truecolor || ${COLORTERM:-} == 24bit ]] && truecolor=1
        printf '\033[?25l' >&2
        while :; do
            (( frame % 30 != 0 )) || phrase="$(spinner_phrase $((RANDOM % 16)))"
            elapsed=$((SECONDS - started))
            suffix=''
            (( elapsed < 5 )) || suffix=" · ${elapsed}s"
            line="$text · $phrase"
            line="${line:0:columns-3-${#suffix}}"
            # Each frame is built in memory and written once, overwriting the old
            # line: clearing first and printing letter by letter flickers.
            frame_text=''
            lead="$tint"
            for ((character=0; character<${#line} && character<${#text}; character++)); do
                if (( truecolor )); then
                    # The Bifröst rainbow flows along the text, about 7 letters a second.
                    position=$((((character - frame * 2 / 3) * 24 % 1536 + 1536) % 1536))
                    stop=$((position / 256)) next=$(((stop + 1) % 6)) mix=$((position % 256))
                    printf -v colour '\033[38;2;%d;%d;%dm' \
                        "$((red[stop] + (red[next] - red[stop]) * mix / 256))" \
                        "$((green[stop] + (green[next] - green[stop]) * mix / 256))" \
                        "$((blue[stop] + (blue[next] - blue[stop]) * mix / 256))"
                    (( character )) || lead="$colour"
                    frame_text+="$colour${line:character:1}"
                else
                    frame_text+="$tint${line:character:1}"
                fi
            done
            printf '\r%s%s \033[0m%s\033[2m%s%s\033[0m\033[K' "$lead" "${runes[frame % ${#runes[@]}]}" "$frame_text" "${line:character}" "$suffix" >&2
            frame=$((frame + 1))
            read -r -t 0.1 -u "$tick" _ || true
        done
    ) </dev/null &
    animator=$!
    "$@" >"$output/stdout" 2>"$output/stderr" || status=$?
    kill "$animator" 2>/dev/null || true
    wait "$animator" 2>/dev/null || true
    animator=''
    printf '\r\033[2K\033[?25h' >&2
    cat "$output/stdout"
    cat "$output/stderr" >&2
    rm -rf -- "$output"
    output=''
    trap - EXIT
    if (( status == 0 )); then printf '✓ %s\n' "$text" >&2; fi
    return "$status"
)
