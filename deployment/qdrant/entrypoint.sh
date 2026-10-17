#!/bin/bash
# No API key in argv/environment. Only an exact, private authentication overlay.
set -euo pipefail
fail() { printf '%s\n' 'C21-Q: authentication configuration rejected' >&2; exit 1; }
check_auth() {
    local auth_file=$1 owner mode admin_key readonly_key
    local -a auth_lines
    [[ -f "$auth_file" && ! -L "$auth_file" && -r "$auth_file" ]] || fail
    owner=$(stat -c '%u' -- "$auth_file") || fail
    mode=$(stat -c '%a' -- "$auth_file") || fail
    [[ "$owner" == "$EUID" && ( "$mode" == 400 || "$mode" == 600 ) ]] || fail
    [[ $(stat -c '%s' -- "$auth_file") -le 256 ]] || fail
    mapfile -t -n 4 auth_lines < "$auth_file"
    [[ ${#auth_lines[@]} -ge 2 && ${#auth_lines[@]} -le 3 ]] || fail
    [[ "${auth_lines[0]}" == 'service:' ]] || fail
    local admin_re='^  api_key: "([0-9a-f]{64})"$'
    local readonly_re='^  read_only_api_key: "([0-9a-f]{64})"$'
    [[ "${auth_lines[1]}" =~ $admin_re ]] || fail
    admin_key=${BASH_REMATCH[1]}
    [[ "$admin_key" != "$(printf '%064d' 0)" ]] || fail
    if [[ ${#auth_lines[@]} == 3 ]]; then
        [[ "${auth_lines[2]}" =~ $readonly_re ]] || fail
        readonly_key=${BASH_REMATCH[1]}
        [[ "$readonly_key" != "$admin_key" && "$readonly_key" != "$(printf '%064d' 0)" ]] || fail
    fi
}
# Do not permit higher-priority environment values to override reviewed files.
for variable in "${!QDRANT__@}"; do fail; done
if [[ $# == 2 && "$1" == --check-auth ]]; then
    check_auth "$2"
    exit 0
fi
[[ $# == 0 ]] || fail
check_auth /run/secrets/qdrant-auth.yaml
exec /qdrant/qdrant --config-path /run/secrets/qdrant-auth.yaml
