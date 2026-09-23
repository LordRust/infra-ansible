#!/usr/bin/env bash
set -Eeuo pipefail

if (( $# != 4 )); then
    echo "Usage: $0 <template-vmid> <vmid> <ip-last-octet> <hostname>" >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ssh_key="${script_dir}/ansible_id_ed25519.pub"
templateid=$1
vmid=$2
vmip=$3
vmname=$4

command -v python3 >/dev/null || { echo 'python3 is required for preflight' >&2; exit 1; }
python3 "$script_dir/preflight.py" vm "$templateid" "$vmid" "$vmip" "$vmname" "$ssh_key"

# Creation itself can fail after allocating resources. Never clean up implicitly.
provisioning_failed() {
    local status=$?
    echo "Provisioning failed for vm $vmid ($vmname). It may be partially created." >&2
    echo "Inspect with: qm status $vmid; qm config $vmid" >&2
    echo 'See proxmox_scripts/README.md for recovery. No resources were destroyed.' >&2
    exit "$status"
}
trap provisioning_failed ERR

qm clone "$templateid" "$vmid" --name "$vmname" --full --storage raid-lvm
qm set "$vmid" --ipconfig0 "ip=10.10.10.${vmip}/24,gw=10.10.10.1"
qm set "$vmid" --nameserver "10.212.226.10 10.212.226.11"
qm set "$vmid" --searchdomain ""
qm set "$vmid" --ciuser ansible
qm set "$vmid" --sshkey "$ssh_key"
qm set "$vmid" --cpu host

echo "VM $vmid is configured but not started. Verify cloud-init data and disks before first boot."
