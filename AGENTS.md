# Working in infra-ansible

## Orientation

This repository contains one Proxmox learning environment: provisioning helpers,
Ansible guest configuration, and operating documentation. Keep these together;
keep guest roles independent of the hypervisor for a future QEMU/KVM environment.

Start with `README.md`, `docs/architecture.md`, `docs/decisions.md`, and
`docs/ansible.md`. Read the relevant topic under `docs/` and
`proxmox_scripts/README.md` before changing that behavior.

Code defines configured behavior; documentation records intent and procedures;
live inspection establishes deployed state. Report discrepancies rather than
silently selecting one. Inventory addresses live in `inventory.ini`, shared
human identities in `group_vars/all/users.yml`, and host exceptions in `host_vars/`.
Do not rely on remembered chat state. Milestone progress lives in
`docs/rebuild-milestone.md`, not here.

## Ownership and conventions

- Proxmox owns guests, virtual disks, networking, templates, and initial bootstrap.
  Use `qm` for KVM and `pct` for LXC.
- Bootstrap creates the automation account, key, networking, and provisioning sudo.
- Ansible owns persistent guest configuration. Prefer modules, reusable roles,
  variables for environment values, and idempotent behavior.
- Human UID/GID values must remain consistent for NFS. The bootstrap account is
  separate. Human SSH keys are additive; use explicit revocations to remove access.
- Manage human sudo through `sudo_users` and a validated sudoers file. Docker
  membership is root-equivalent and must be granted deliberately.
- Use official Docker packages and the explicitly chosen upstream Apptainer version.
- Proxmox attaches data disks; Ansible manages their filesystems. Verify persistent
  device identifiers, never force-format mismatched filesystems, and preserve
  mounted-filesystem guards on NFS exports.
- Never commit plaintext secrets, private keys, or Vault passwords. The public
  bootstrap key and encrypted Vault files are intentional.

## Workflow and validation

At task start inspect `git status`, `git branch --show-current`, and
`git log -1 --oneline`, then read the relevant implementation before editing.
Keep changes scoped and update operating documentation with behavior changes.

Default validation is local and does not contact managed infrastructure. Use
`scripts/check.sh` once available; otherwise run applicable inventory/syntax,
YAML/Ansible lint, `bash -n`, and ShellCheck checks. Do not install dependencies
silently as part of a check.

Check-mode playbooks contact live machines and can execute probes and lookups.
Run them only within the task's authorized live-target scope, with an explicit
inventory and host limit. Check mode cannot prove first-run package installation,
mounting, downloads, or service startup. Use disposable guests for rebuild tests.

Before live mutation, verify guest names, VMIDs, addresses, storage, devices,
bridges, and mount points. Inspect before changing. Do not destroy/recreate a
working guest for stylistic consistency. Never guess about deployed state.

## Git and completion

Unless explicitly requested, do not commit, push, merge, or rewrite history.
When a task explicitly requests a commit sequence, make scoped local commits;
publication remains under human control. Build patches against the current checkout.

Before finishing inspect the complete diff, diff statistics, and Git status.
Summarize changes, checks actually run, unavailable checks, and remaining gaps.
Do not imply runtime success from static validation or dump sensitive values.
Keep runbooks about current behavior; record milestone evidence separately.
