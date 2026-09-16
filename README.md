# infra-ansible

Configuration and operational documentation for the Proxmox-based test and development VM environment.

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
- [Ansible conventions](docs/ansible.md)
- [NFS and SMB](docs/nfs-smb.md)
- [MongoDB](docs/services/mongodb.md)

## Operating model

```text
official Debian cloud image
        |
        v
Proxmox template
        |
        v
cloud-init
(machine identity, network, initial SSH access)
        |
        v
Ansible
(users, packages, mounts, services, configuration)
        |
        v
application-specific tooling
(Docker Compose, Apptainer, conda/mamba, etc.)
```

VMs should be treated as reproducible and replaceable. Persistent configuration belongs in this repository rather than being maintained manually inside individual guests.
