# LXC containers

## Use in this environment

LXC is used selectively for lightweight infrastructure. `infra-admin-01` is the first production-style test of this model:

| ID | Name | Address | Configuration |
|---:|---|---|---|
| 201 | `infra-admin-01` | `10.10.10.10` | unprivileged Debian 13 LXC, 2 cores, 2 GiB RAM, 512 MiB swap, 8 GiB rootfs |

KVM remains preferred for development VMs, MongoDB, and the NFS file server for now.

## Debian template

List and download the current Debian 13 standard LXC template on the Proxmox host:

```bash
pveam update
pveam available | grep debian-13
pveam download local debian-13-standard_13.6-1_amd64.tar.zst
pveam list local
```

The exact template version can be updated in `proxmox_scripts/create_lxc.sh` when Debian publishes a newer standard template.

## Create a container

The repository script creates the container and its `ansible` bootstrap account:

```bash
cd /path/to/infra-ansible/proxmox_scripts
./create_lxc.sh 201 10 infra-admin-01
```

The resulting network configuration is on `vmbr1` with gateway `10.10.10.1` and the institutional DNS servers. LXC may inherit the Proxmox host search domain (`reg.skane.se`) in `/etc/resolv.conf`; this is harmless unless a concrete short-name resolution problem is observed.

Debian 13 uses systemd 257. Proxmox may warn that nesting is required; the creation script enables:

```text
features: nesting=1
```

Keep containers unprivileged. Do not enable additional LXC features unless a workload requires them.

## Bootstrap account

Unlike QEMU cloud-init guests, LXC containers do not use:

```text
qm set ... --ciuser ansible --sshkey ...
```

`create_lxc.sh` instead uses `pct` to create `ansible`, install the repository's public bootstrap key, install Python/SSH/sudo, and configure passwordless sudo. The normal inventory setting therefore remains:

```ini
[all:vars]
ansible_user=ansible
```

Human users such as `jonas` and `jakob` are still managed by the Ansible `base` role.

## Controller setup

For an administration LXC, install the controller tools after first login:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y ansible git tmux vim curl rsync jq
```

Then clone `infra-ansible`, install collection requirements, and populate local SSH host keys:

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory.ini admin-local.yml
```

The local playbook derives addresses from `inventory.ini`; there is no separate hard-coded list of `10.10.10.x` hosts to maintain.

Minimal Debian LXC templates may emit Perl locale warnings if `LANG=en_US.UTF-8` is set without that locale being generated. This does not affect Ansible or APT operation. Generate the locale only if desired.

## `pct` versus `qm`

Use `pct` for LXC and `qm` for QEMU/KVM:

```bash
pct status 201
pct config 201
pct enter 201
pct stop 201
pct start 201
pct destroy 201
```

Container configuration is stored under `/etc/pve/lxc/<id>.conf`; QEMU VM configuration is under `/etc/pve/qemu-server/<id>.conf`.
