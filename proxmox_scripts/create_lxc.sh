#!/usr/bin/env bash
set -euo pipefail

if (( $# != 3 )); then
    echo "Usage: $0 <vmid> <ip-last-octet> <hostname>" >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
templateid=debian-13-standard_13.6-1_amd64.tar.zst
ssh_key="${script_dir}/ansible_id_ed25519.pub"
vmid=$1
vmip=$2
vmname=$3

if [[ ! -r "$ssh_key" ]]; then
    echo "SSH public key not found: $ssh_key" >&2
    exit 1
fi

pct create "$vmid" "local:vztmpl/${templateid}" \
    --hostname "$vmname" \
    --ostype debian \
    --unprivileged 1 \
    --cores 2 \
    --memory 2048 \
    --swap 512 \
    --rootfs raid-lvm:8 \
    --net0 "name=eth0,bridge=vmbr1,ip=10.10.10.${vmip}/24,gw=10.10.10.1" \
    --nameserver "10.212.226.10 10.212.226.11" \
    --onboot 1 \
    --features nesting=1 \
    --start 1

# LXC does not use the VM cloud-init --ciuser/--sshkey bootstrap. Create the
# same dedicated automation account directly from the Proxmox host instead.
pct exec "$vmid" -- apt-get update
pct exec "$vmid" -- apt-get install -y openssh-server python3 sudo
pct exec "$vmid" -- useradd -m -s /bin/bash ansible
pct exec "$vmid" -- install -d -m 0700 -o ansible -g ansible /home/ansible/.ssh
pct push "$vmid" "$ssh_key" /home/ansible/.ssh/authorized_keys
pct exec "$vmid" -- chown ansible:ansible /home/ansible/.ssh/authorized_keys
pct exec "$vmid" -- chmod 0600 /home/ansible/.ssh/authorized_keys
pct exec "$vmid" -- usermod -aG sudo ansible
pct exec "$vmid" -- sh -c 'printf "%s\n" "ansible ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ansible'
pct exec "$vmid" -- chmod 0440 /etc/sudoers.d/ansible
pct exec "$vmid" -- visudo -cf /etc/sudoers.d/ansible
pct exec "$vmid" -- systemctl enable --now ssh
