#!/usr/bin/env bash
# Run on the controller. SSH host-key enrollment is a separate bootstrap step.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
# Supply an alternative inventory explicitly; do not combine it with live hosts.
if (( $# == 0 )); then
    echo "Usage: $0 -i <inventory> [--ask-vault-pass] [Ansible options...]" >&2
    exit 2
fi
has_inventory=false
for arg in "$@"; do
    case "$arg" in -i|--inventory|--inventory-file|-i?*|--inventory=*|--inventory-file=*) has_inventory=true ;; esac
done
if [[ "$has_inventory" != true ]]; then
    echo 'An explicit -i <inventory> is required.' >&2
    exit 2
fi
exec ansible-playbook site.yml "$@"
