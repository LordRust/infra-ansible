#!/usr/bin/env bash
set -euo pipefail

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

if [[ ! -r "$ssh_key" ]]; then
    echo "SSH public key not found: $ssh_key" >&2
    exit 1
fi

qm clone "$templateid" "$vmid" --name "$vmname" --full
qm set "$vmid" --ipconfig0 "ip=10.10.10.${vmip}/24,gw=10.10.10.1"
qm set "$vmid" --nameserver "10.212.226.10 10.212.226.11"
qm set "$vmid" --searchdomain ""
qm set "$vmid" --ciuser ansible
qm set "$vmid" --sshkey "$ssh_key"
