# Proxmox creation scripts

Run these scripts on the Proxmox host. They assume the current private network and storage layout:

- bridge: `vmbr1`
- network: `10.10.10.0/24`
- gateway: `10.10.10.1`
- DNS: `10.212.226.10`, `10.212.226.11`
- VM/LXC storage: `raid-lvm`

The public bootstrap key is read from `ansible_id_ed25519.pub` in this directory. The private key is not stored in the repository.

## KVM VM

```bash
./create_vm.sh <template-vmid> <vmid> <ip-last-octet> <hostname>
```

Example:

```bash
./create_vm.sh 102 301 101 dev01
```

The script clones the cloud-init template and sets the static address, DNS, empty search domain, `ansible` cloud-init user, and SSH public key. Configure all per-VM cloud-init values before first boot.

## LXC

```bash
./create_lxc.sh <vmid> <ip-last-octet> <hostname>
```

Example for the primary administration container:

```bash
./create_lxc.sh 201 10 infra-admin-01
```

The LXC script creates an unprivileged Debian 13 container with 2 cores, 2 GiB RAM, 512 MiB swap, and an 8 GiB root filesystem. `nesting=1` is enabled for Debian 13/systemd 257.

LXC does not use the QEMU cloud-init `--ciuser`/`--sshkey` path. The script therefore creates the `ansible` account directly with `pct`, installs its public key, and grants passwordless sudo for automation.

Proxmox IDs are shared between QEMU VMs and LXC containers. An ID must be free before creating either guest type.

## Controller-side deployment

The former `run_all_ansible.sh` helper has moved to `scripts/`. Run it on the
Ansible controller, not the Proxmox host; see [Ansible](../docs/ansible.md).
