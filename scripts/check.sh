#!/usr/bin/env bash
# Local validation only. Forward Vault options to inventory and syntax checks.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_dir"
for tool in ansible-inventory ansible-playbook ansible-lint yamllint shellcheck python3; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool (see docs/ansible.md)" >&2; exit 1; }
done
check_tmp=$(mktemp -d)
trap 'rm -rf -- "$check_tmp"' EXIT
export ANSIBLE_LOCAL_TEMP="$check_tmp/ansible"
export ANSIBLE_INVENTORY_UNPARSED_FAILED=true
export ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=true

# --list loads variables, unlike --graph alone. Never print the resolved secrets.
if ! ansible-inventory -i inventory.ini "$@" --list > "$check_tmp/inventory.json"; then
    echo 'Inventory loading failed. If Vault is locked, pass --ask-vault-pass or --vault-id NAME@PATH.' >&2
    exit 1
fi
ansible-inventory -i inventory.ini "$@" --graph
for playbook in ./*.yml; do
    [[ "$playbook" == ./requirements.yml ]] && continue
    ansible-playbook -i inventory.ini "$playbook" --syntax-check "$@"
done
yamllint .
ansible-lint --offline
while IFS= read -r -d '' script; do
    bash -n "$script"
    shellcheck "$script"
done < <(find scripts proxmox_scripts -type f -name '*.sh' -print0)
python3 -m unittest discover -s tests/local -v
echo 'Local validation passed; no managed hosts were contacted.'
