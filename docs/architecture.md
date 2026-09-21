# Architecture

## Scope

This environment is a Proxmox VE testbed on a Dell PowerEdge T620. It is used to develop a reproducible VM configuration model before similar roles are deployed to production systems.

The preferred guest type is a full KVM/QEMU VM.

## Host

Proxmox host:

- Hostname: `mtcmdpgm02`
- External address: `10.231.229.23/24`
- External bridge: `vmbr0`
- Private VM bridge: `vmbr1`
- Private VM network: `10.10.10.0/24`
- Private gateway: `10.10.10.1`

The physical network limits the number of DHCP addresses available per switch port, so test VMs are placed behind NAT.

## VM organization

Use Proxmox VMIDs to indicate the machine class:

| VMID range | Purpose |
|---:|---|
| 100-199 | Templates |
| 200-299 | Administration and management VMs |
| 300-399 | Development VMs |
| 400-499 | Infrastructure/services; reserved |
| 500-599 | Database VMs |
| 600-999 | Reserved for future classes |

For normal VM instances, start at `x01` within each class so the final two
digits correspond to the instance number. For example, `201` is admin VM 01,
`301` is development VM 01, and `501` is database VM 01.

Templates are an exception and are allocated sequentially from VMID 100.

Target organization for the current machines:

| VMID | Name | Address | Purpose |
|---:|---|---|---|
| 201 | `infra-admin-01` | `10.10.10.10` | Ansible control host |
| 202 | `infra-admin-02` | `10.10.10.11` | Ansible control host |
| 301 | `dev01` | `10.10.10.101` | Development VM |
| 302 | `dev02` | `10.10.10.102` | Development VM |
| 303 | `dev03` | `10.10.10.103` | Development VM |
| 401 | `infra-fs-01` | `10.10.10.16` | NFS file server for `/fs3` |
| 501 | `mongodb01` | `10.10.10.32` | MongoDB test VM |

Existing VMs may temporarily retain older VMIDs or addresses while they are
being rebuilt, migrated, or retired. New and rebuilt VMs should follow the
allocation above.

VMID 100 is the older manually-created Debian 13 template and should eventually be retired after the cloud-image replacement has been validated.

VMID 101 is the Debian 12 cloud-init template used for `mongodb01`.

VMID 102 is the validated Debian 13 `genericcloud` template for new Debian 13 guests.

## Configuration boundaries

### Proxmox

Responsible for:

- VM hardware
- virtual disks
- bridges
- NAT and inbound port forwarding
- templates and cloning
- cloud-init data

### cloud-init

Responsible for initial bootstrap only:

- bootstrap administration user (`ansible`)
- SSH public key
- static address
- gateway
- DNS servers
- hostname/instance identity

### Ansible

Responsible for persistent guest configuration:

- human users and groups, including stable UID/GID values for NFS
- packages
- external package repositories
- local filesystems on attached virtual disks
- NFS/SMB mounts
- NFS exports
- Docker
- Apptainer
- service configuration

### Application tooling

Application-level environments remain outside the base OS configuration where appropriate:

- Docker Compose
- Apptainer images
- conda/mamba environments
- application-specific configuration repositories

## DNS

Test VMs use the institutional resolvers directly:

```text
10.212.226.10
10.212.226.11
```

`10.10.10.1` is the VM gateway and is **not** a DNS resolver.

No DNS search domain is configured during the NAT/testing phase because the private VMs are not registered in institutional DNS.

Production hosts are expected to be registered under `lund.skane.se`.
