#!/usr/bin/env bash
# Eitr repository checks: one entry point for local runs and CI.
#
#   bash tools/check.sh                 # run every stage
#   bash tools/check.sh shellcheck qml  # run only the named stages
#   bash tools/check.sh --list          # list stages
#
# Files are discovered with `git ls-files`, so new tests, scripts, QML, and
# data files are checked without editing this script. Run as a normal user:
# installer tests refuse root. On non-Arch hosts, see README.md > Checks for
# the Docker one-liner.
#
# Environment:
#   QMLLINT           Path to the Qt 6 qmllint (default /usr/lib/qt6/bin/qmllint).

set -uo pipefail

repo_root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || {
  printf 'check.sh: not inside a Git checkout\n' >&2
  exit 2
}
cd "$repo_root" || exit 2
export PYTHONPATH="$repo_root/distro/lib${PYTHONPATH:+:$PYTHONPATH}"
export EITR_CODE_ROOT="$repo_root"
export EITR_LIBRARY_ROOT="$repo_root/distro/lib"
# Ordinary assertions use the English source. Locale tests override this locally.
export LC_ALL=C.UTF-8
# Tests that replace HOME must not inherit the owner's explicit config root.
unset XDG_CONFIG_HOME XDG_CACHE_HOME XDG_STATE_HOME XDG_DATA_HOME

all_stages=(python-tests node-tests syntax shellcheck qml whitespace data)
qmllint_bin="${QMLLINT:-/usr/lib/qt6/bin/qmllint}"

scratch="$(mktemp -d "${TMPDIR:-/tmp}/eitr-check.XXXXXX")" || exit 2
trap 'rm -rf "$scratch"' EXIT
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$scratch/pycache"

if [[ -t 1 ]]; then
  bold=$'\e[1m' red=$'\e[31m' green=$'\e[32m' reset=$'\e[0m'
else
  bold='' red='' green='' reset=''
fi

declare -a summary=()
failed=0

# --- file discovery --------------------------------------------------------

# Tracked files that still exist in the working tree, NUL-separated.
tracked_files() {
  local file
  while IFS= read -r -d '' file; do
    [[ -f "$file" && ! -L "$file" ]] && printf '%s\0' "$file"
  done < <(git ls-files -z -- "$@")
}

# Prints the interpreter named by a file's shebang (bash, sh, python3, ...).
shebang_interpreter() {
  local line
  IFS= read -r line < "$1" 2>/dev/null || return 1
  [[ "$line" == '#!'* ]] || return 1
  line="${line#'#!'}"
  read -r -a words <<< "$line"
  local interpreter="${words[0]##*/}"
  if [[ "$interpreter" == env ]]; then
    local word
    for word in "${words[@]:1}"; do
      [[ "$word" == -* ]] && continue
      interpreter="$word"
      break
    done
  fi
  printf '%s\n' "$interpreter"
}

# Shell scripts (bash/sh) by extension or shebang. zsh files are excluded
# because bash and shellcheck cannot parse zsh syntax.
discover_shell_scripts() {
  local file interpreter
  shell_scripts=()
  while IFS= read -r -d '' file; do
    case "$file" in
      *.sh|*.bash) shell_scripts+=("$file"); continue ;;
    esac
    # Only extensionless files can be scripts identified by shebang.
    [[ "${file##*/}" == *.* ]] && continue
    interpreter="$(shebang_interpreter "$file")" || continue
    case "$interpreter" in
      bash|sh|dash) shell_scripts+=("$file") ;;
    esac
  done < <(tracked_files)
}

discover_python_files() {
  local file interpreter
  python_files=()
  while IFS= read -r -d '' file; do
    case "$file" in
      *.py) python_files+=("$file"); continue ;;
    esac
    [[ "${file##*/}" == *.* ]] && continue
    interpreter="$(shebang_interpreter "$file")" || continue
    [[ "$interpreter" == python* ]] && python_files+=("$file")
  done < <(tracked_files)
}

collect() {
  # collect <array-name> <pathspec>...
  local -n target="$1"
  shift
  target=()
  local file
  while IFS= read -r -d '' file; do target+=("$file"); done < <(tracked_files "$@")
}

# --- stages ----------------------------------------------------------------

stage_python_tests() {
  local test_files dir status=0
  collect test_files ':(glob)**/tests/test_*.py'
  local -A dirs=()
  for file in "${test_files[@]}"; do dirs["${file%/*}"]=1; done
  if ((${#dirs[@]} == 0)); then echo 'no Python test suites found'; return 0; fi
  for dir in $(printf '%s\n' "${!dirs[@]}" | sort); do
    printf -- '--- %s\n' "$dir"
    # Tests stay out of a live desktop session: its XDG directories and its
    # notification bus.
    env -u XDG_CONFIG_HOME -u XDG_STATE_HOME -u XDG_DATA_HOME -u XDG_CACHE_HOME \
      DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent \
      python3 -m unittest discover -s "$dir" -p 'test_*.py' || status=1
  done
  return "$status"
}

stage_node_tests() {
  local test_files status=0
  collect test_files ':(glob)**/tests/test_*.js'
  if ((${#test_files[@]} == 0)); then echo 'no node tests found'; return 0; fi
  for file in "${test_files[@]}"; do
    printf -- '--- %s\n' "$file"
    node "$file" || status=1
  done
  return "$status"
}

stage_syntax() {
  local status=0 file lua_files
  discover_shell_scripts
  discover_python_files
  collect lua_files '*.lua'
  for file in "${shell_scripts[@]}"; do
    bash -n "$file" || { echo "bash -n failed: $file"; status=1; }
  done
  python3 - "${python_files[@]}" <<'PY' || status=1
import py_compile, sys
failed = False
for path in sys.argv[1:]:
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as error:
        print(error.msg, file=sys.stderr)
        failed = True
sys.exit(1 if failed else 0)
PY
  for file in "${lua_files[@]}"; do
    luac -p "$file" || status=1
  done
  rm -f luac.out
  echo "checked ${#shell_scripts[@]} shell, ${#python_files[@]} Python, ${#lua_files[@]} Lua files"
  return "$status"
}

stage_shellcheck() {
  discover_shell_scripts
  # Severity gate: warnings and errors fail; info/style findings are not
  # reported. Repo-wide disables live in .shellcheckrc with reasons.
  # Batches bound peak memory, which matters on small or emulated hosts.
  printf '%s\0' "${shell_scripts[@]}" |
    xargs -0 -n 10 shellcheck --severity=warning --external-sources --format=gcc
  local status=$?
  echo "shellcheck checked ${#shell_scripts[@]} scripts"
  return "$status"
}

stage_qml() {
  local qml_files
  collect qml_files '*.qml'
  if [[ ! -x "$qmllint_bin" ]]; then
    echo "Qt 6 qmllint not found at $qmllint_bin (install qt6-declarative)"
    return 1
  fi
  # Quickshell's QML modules are not installed in CI, so categories that need
  # resolved types (imports, unqualified ids, properties of Quickshell types)
  # are disabled. Syntax errors and resolution-independent structural mistakes
  # are errors and fail the stage; any other findings print as advisory.
  local -a resolution_dependent=(import unqualified missing-property
    unresolved-type missing-type required incompatible-type)
  local -a structural=(syntax syntax.duplicate-ids duplicated-name
    duplicate-import alias-cycle inheritance-cycle unterminated-case
    var-used-before-declaration eval with)
  local -a options=(--ignore-settings --max-warnings -1)
  local category
  for category in "${resolution_dependent[@]}"; do options+=("--$category" disable); done
  for category in "${structural[@]}"; do options+=("--$category" error); done
  "$qmllint_bin" "${options[@]}" "${qml_files[@]}"
  local status=$?
  echo "qmllint checked ${#qml_files[@]} QML files"
  return "$status"
}

stage_whitespace() {
  # Diff the empty tree against the working tree: every tracked file,
  # including uncommitted edits. Imported upstream files opt out through the
  # `-whitespace` attribute in .gitattributes.
  local empty_tree
  empty_tree="$(git hash-object -t tree /dev/null)" || return 1
  git diff --check "$empty_tree" --
}

stage_data() {
  local data_files
  collect data_files '*.json' '*.toml'
  python3 - "${data_files[@]}" <<'PY'
import json, sys, tomllib
failed = False
for path in sys.argv[1:]:
    try:
        with open(path, "rb") as handle:
            if path.endswith(".toml"):
                tomllib.load(handle)
            else:
                json.loads(handle.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        print(f"{path}: {error}", file=sys.stderr)
        failed = True
print(f"parsed {len(sys.argv) - 1} JSON/TOML files")
sys.exit(1 if failed else 0)
PY
}

# --- driver ----------------------------------------------------------------

run_stage() {
  local name="$1" function="stage_${1//-/_}" start status
  printf '\n%s==> %s%s\n' "$bold" "$name" "$reset"
  start=$SECONDS
  "$function"
  status=$?
  local elapsed=$((SECONDS - start))
  if ((status == 0)); then
    summary+=("${green}PASS${reset}  $name (${elapsed}s)")
  else
    summary+=("${red}FAIL${reset}  $name (${elapsed}s)")
    failed=1
  fi
}

if [[ "${1:-}" == --list ]]; then
  printf '%s\n' "${all_stages[@]}"
  exit 0
fi
if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '2,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
  exit 0
fi

stages=("$@")
((${#stages[@]})) || stages=("${all_stages[@]}")
for stage in "${stages[@]}"; do
  if ! declare -F "stage_${stage//-/_}" > /dev/null; then
    printf 'check.sh: unknown stage "%s" (try --list)\n' "$stage" >&2
    exit 2
  fi
done

if ((EUID == 0)) && [[ " ${stages[*]} " == *' python-tests '* ]]; then
  printf '%scheck.sh: run as a normal user; installer tests refuse root.%s\n' "$red" "$reset" >&2
  exit 2
fi

for stage in "${stages[@]}"; do run_stage "$stage"; done

printf '\n%sSummary%s\n' "$bold" "$reset"
printf '  %s\n' "${summary[@]}"
if ((failed)); then
  printf '%sChecks failed.%s\n' "$red" "$reset"
  exit 1
fi
printf '%sAll checks passed.%s\n' "$green" "$reset"
