# Ansible

## Control host

`infra-admin-01` is the Ansible control host.

Repository:

```text
~/infra-ansible
```

Normal execution:

```bash
ansible-playbook -i inventory.ini dev-base.yml
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
[devhosts]
devvm01 ansible_host=10.10.10.11

[mongodb]
mongodb01 ansible_host=10.10.10.12

[all:vars]
ansible_user=jonas
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
├── dev-base.yml
├── group_vars/
│   ├── all/
│   ├── devhosts/
│   └── mongodb/
├── host_vars/
└── roles/
    ├── base/
    ├── docker/
    ├── apptainer/
    ├── nfs-client/
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

Example:

```yaml
dev_users:
  - jonas
  - jakob

apptainer_version: "1.5.3"
```

Keep environment-specific values in variables rather than hard-coding them inside reusable roles.

## Base role

The base role should contain generic machine configuration such as:

- `git`
- `tmux`
- `htop`
- `curl`
- `ca-certificates`
- `sudo`
- common users/groups
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
