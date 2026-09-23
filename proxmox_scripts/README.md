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

## Preflight and partial failures

Keep the whole repository checkout on the Proxmox host: the helpers use the
shared `preflight.py`, repository inventory, and public key. Run as root with
Python 3 and standard Proxmox/OpenSSH/coreutils tools available. Positional
arguments have not changed. Both helpers verify argument formats, the public
key, bridge, active storage, templates, and cluster-wide VMID/name availability
before creation. VM clones explicitly target `raid-lvm`.

An inventory reservation is allowed only when its hostname and address match
the requested guest. Existing IP assignments in Proxmox VM/LXC configuration
are rejected regardless of hostname. These checks cannot detect static addresses
configured manually inside a guest, unmanaged machines, or allocation races.
Do not provision the same identifiers concurrently. Inspect pool capacity before
large clones; positive free space does not guarantee enough space for a clone.

The LXC script waits up to roughly 120 seconds for guest systemd readiness before
bootstrap (individual probes are limited to five seconds). It does not retry APT
or delete a container on failure. KVM provisioning still stops before first boot.

If creation/bootstrap fails, inspect `qm config/status VMID` or
`pct config/status VMID` as appropriate. The error reports the exact VMID/name.
Do not rerun the creation helper against the partial guest: preflight will refuse
its occupied ID. For a VM, inspect and complete the remaining `qm set` operations,
then verify cloud-init data before starting. For LXC, inspect networking/APT, then
complete the failed bootstrap steps with `pct exec`; if the account already exists,
skip `useradd` and verify it instead. Validate sudoers and SSH access before Ansible.
Destroying a confirmed disposable partial guest is a separate explicit action;
never automate destruction as error recovery.

CLI references: [Proxmox API](https://pve.proxmox.com/wiki/Proxmox_VE_API)
and [storage CLI](https://pve.proxmox.com/pve-docs/pvesm.1.html).
