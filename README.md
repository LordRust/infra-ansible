# infra-ansible

Configuration and operational documentation for the Proxmox-based test and development guest environment.

The repository has two purposes:

1. **Ansible configuration** defines the desired state of guest systems.
2. **`docs/`** records the infrastructure design, operating procedures, and decisions behind that configuration.

The documentation should describe the **current known-good state**. Troubleshooting history and failed experiments belong in chat/issues, not in the runbook.

## Documentation

- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Proxmox host](docs/proxmox-host.md)
- [Networking](docs/networking.md)
- [Storage](docs/storage.md)
- [VM templates and cloud-init](docs/vm-templates.md)
- [LXC containers](docs/lxc.md)
- [Ansible conventions](docs/ansible.md)
- [NFS and SMB](docs/nfs-smb.md)
- [MongoDB](docs/services/mongodb.md)

## Operating model

```text
Debian image/template
        |
        v
Proxmox VM or LXC
        |
        v
bootstrap
(cloud-init for VMs; pct setup for LXC)
        |
        v
Ansible
(users, packages, mounts, services, configuration)
        |
        v
application-specific tooling
(Docker Compose, Apptainer, conda/mamba, etc.)
```

Guests should be treated as reproducible and replaceable. Persistent configuration belongs in this repository rather than being maintained manually inside individual guests.

## Deployment and validation

On a controller without lint tools, validate the real inventory and playbook
syntax as described in [Ansible](docs/ansible.md). `scripts/check.sh` adds lint
and local tests when those tools are installed. After bootstrap and SSH host-key
enrollment, use
`scripts/run_all_ansible.sh -i inventory.ini --ask-vault-pass` on the controller.
Proxmox provisioning helpers remain in `proxmox_scripts/`; they belong to this
same environment but run on the hypervisor. See [Ansible](docs/ansible.md) and
[rebuild milestone](docs/rebuild-milestone.md).

With lint tools but without Vault credentials, `scripts/check.sh --fixtures-only`
runs the secret-free local checks. Runtime acceptance is described in the
[disposable Proxmox rebuild exercise](docs/disposable-rebuild.md).
