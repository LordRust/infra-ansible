# Ansible

## Control host

`infra-admin-01` and `infra-admin-02` are administration hosts. `infra-admin-01` is an unprivileged Debian 13 LXC container; `infra-admin-02` remains a KVM VM.

The bootstrap account used by Ansible on managed guests is `ansible`. KVM guests receive this account and its SSH key through cloud-init. LXC guests receive the equivalent bootstrap setup directly through `pct`; see [LXC containers](lxc.md).

Repository:

```text
~/infra-ansible
```

### Rebuilding an Ansible controller

After the Proxmox-side guest bootstrap has created the `ansible` account and human access has been established, install the small set of controller tools manually:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y ansible git tmux vim curl rsync jq
```

Clone the repository, install its Ansible collection requirements, and populate the invoking user's SSH `known_hosts` from the inventory:

```bash
git clone git@github.com:LordRust/infra-ansible.git
cd infra-ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory.ini admin-local.yml
```

`admin-local.yml` runs only on the controller itself. It scans the `ansible_host` addresses in `inventory.ini` with `ssh-keyscan` and updates `~/.ssh/known_hosts` idempotently. This avoids an interactive first-connection prompt when Ansible contacts a newly provisioned host. `ssh-keyscan` is a trust-on-first-use convenience; it does not independently authenticate the host key.

Normal execution:

```bash
ansible-playbook -i inventory.ini dev-base.yml
ansible-playbook -i inventory.ini db-base.yml
ansible-playbook -i inventory.ini fs-base.yml
```

Useful checks:

```bash
ansible-inventory -i inventory.ini --graph
ansible-playbook -i inventory.ini dev-base.yml --syntax-check
ansible-playbook -i inventory.ini dev-base.yml --check
```

Re-running playbooks after changes is normal. Tasks should be idempotent: already-correct state should report `ok` rather than continually changing the host.

## Inventory model

Group machines by function.

Example:

```ini
[adminhosts]
infra-admin-01 ansible_host=10.10.10.10
infra-admin-02 ansible_host=10.10.10.11

[devhosts]
dev01 ansible_host=10.10.10.101
dev02 ansible_host=10.10.10.102
dev03 ansible_host=10.10.10.103

[dbhosts]
mongodb01 ansible_host=10.10.10.32

[fileservers]
infra-fs-01 ansible_host=10.10.10.16

[all:vars]
ansible_user=ansible
ansible_python_interpreter=/usr/bin/python3
```

Prefer functional groups over large amounts of one-off host logic.

## Repository layout

Current direction:

```text
infra-ansible/
├── README.md
├── docs/
├── inventory.ini
├── admin-base.yml
├── admin-local.yml
├── dev-base.yml
├── db-base.yml
├── fs-base.yml
├── requirements.yml
├── proxmox_scripts/
├── group_vars/
│   ├── all/
│   │   └── users.yml
│   └── devhosts/
├── host_vars/
└── roles/
    ├── base/
    ├── docker/
    ├── apptainer/
    ├── mongodb/
    ├── local-filesystem/
    ├── nfs-client/
    ├── nfs-server/
    └── smb-client/
```

Only create a role/group when it represents a useful functional boundary.

## Variables

Files below a group directory are loaded for that group:

```text
group_vars/devhosts/
├── devhosts.yml
├── nfs_mounts.yml
└── smb_mounts.yml
```

Development-only variables remain under `group_vars/devhosts/`, for example:

```yaml
docker_users:
  - jonas
  - jakob

sudo_users:
  - jonas

apptainer_version: "1.5.3"
```

Human users shared across machine classes are defined in
`group_vars/all/users.yml`. Their UID and GID values must match the
authoritative NFS environment.

Keep environment-specific values in variables rather than hard-coding them inside reusable roles.

Install the collections used by the roles with:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Attached filesystems

The `local-filesystem` role manages filesystems on virtual disks that Proxmox
has already attached to a guest. Host variables supply the persistent device
path, filesystem label, type, and mount point. For example:

```yaml
local_filesystems:
  - device: /dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1
    label: local
    path: /local
    fstype: ext4
    opts: defaults
```

The role refuses a device containing a different filesystem type, never sets
`force: true`, mounts by filesystem label, and grows an ext4 filesystem when
the virtual disk has been enlarged. Confirm the `by-id` path in the guest
before the first run; do not assume `/dev/sdb` is stable.

The `nfs-server` role manages `/etc/exports.d/ansible.exports`. It removes a
matching legacy entry from `/etc/exports` when adopting a manually configured
export. It also requires every exported path to be a mounted filesystem,
preventing an accidental export of the empty directory beneath a missing
data-disk mount.

## Bootstrap and human accounts

The local `ansible` account is used for provisioning and recovery. Cloud-init creates it on KVM guests; the LXC creation script creates the same account directly with `pct`. It is deliberately separate from normal human accounts and does not need to share the NFS numeric identity scheme.

The `base` role creates human accounts such as `jonas` and `jakob`. Their
numeric UID/GID values are defined centrally in `group_vars/all/users.yml`;
NFS ownership is numeric, so these values must remain consistent across all
NFS clients.

### Passwordless sudo

The `base` role grants passwordless sudo to the users listed in `sudo_users`.
It writes the complete list to `/etc/sudoers.d/ansible-sudo-users` and validates
the generated file with `visudo` before replacing the active configuration.

To grant sudo on every development machine, set the group variable in
`group_vars/devhosts/devhosts.yml`:

```yaml
sudo_users:
  - jonas
```

To use a different list on one machine, define it in that machine's host
variables. Host variables replace the group list rather than extending it, so
include every user who should retain sudo on that host:

```yaml
# host_vars/dev01.yml
sudo_users:
  - jonas
  - jakob
```

Removing a user from the effective list removes that user's rule the next time
the applicable playbook runs. An empty list leaves the managed sudoers file
empty and grants no passwordless sudo through this mechanism.

## Base role

The base role should contain generic machine configuration such as:

- `git`
- `tmux`
- `htop`
- `curl`
- `ca-certificates`
- `sudo`
- common users/groups with stable UID/GID values
- optionally `qemu-guest-agent`

## Docker

Do not install Debian's `docker.io` package as the long-term Docker configuration.

The Docker role should:

1. remove conflicting distro packages where needed
2. install Docker's signing key
3. configure Docker's official APT repository
4. install:
   - `docker-ce`
   - `docker-ce-cli`
   - `containerd.io`
   - `docker-buildx-plugin`
   - `docker-compose-plugin`
5. enable/start Docker
6. add selected trusted users to the `docker` group

Membership in the `docker` group is effectively root-equivalent and should be granted deliberately.

## Apptainer

Use the upstream pre-built Debian package rather than assuming an `apptainer` package exists in the normal Debian repository.

Pin the chosen version in group variables, for example:

```yaml
apptainer_version: "1.5.3"
```

The role downloads and installs the matching upstream `.deb`.

## Secrets

Keep plaintext credentials out of Git.

For SMB and similar secrets, store the actual secret in an Ansible Vault-encrypted variable file.

The encrypted Vault file may be committed. Do not commit the Vault password or an unencrypted equivalent.

## Git workflow

The repository is the source of truth.

Keep Git operations under human control:

```bash
git diff
git add ...
git commit
git push
```

Chat/Codex may propose changes, but changes should be reviewed before they are committed.
