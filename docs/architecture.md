# Architecture

## Scope

This environment is a Proxmox VE testbed on a Dell PowerEdge T620. It is used to develop a reproducible guest configuration model before similar roles are deployed to production systems.

KVM/QEMU remains the default for development, database, and storage workloads. LXC is used selectively for lightweight infrastructure; `infra-admin-01` is an unprivileged Debian 13 LXC container.

## Host

Proxmox host:

- Hostname: `mtcmdpgm02`
- External address: `10.231.229.23/24`
- External bridge: `vmbr0`
- Private VM bridge: `vmbr1`
- Private VM network: `10.10.10.0/24`
- Private gateway: `10.10.10.1`

The physical network limits the number of DHCP addresses available per switch port, so test guests are placed behind NAT.

## Guest organization

Use Proxmox IDs to indicate the machine class. The numeric namespace is shared by KVM VMs and LXC containers:

| VMID range | Purpose |
|---:|---|
| 100-199 | Templates |
| 200-299 | Administration and management guests |
| 300-399 | Development VMs |
| 400-499 | Infrastructure/services; reserved |
| 500-599 | Database VMs |
| 600-999 | Reserved for future classes |

For normal guest instances, start at `x01` within each class so the final two
digits correspond to the instance number. For example, `201` is admin guest 01,
`301` is development VM 01, and `501` is database VM 01.

Templates are an exception and are allocated sequentially from VMID 100.

Target organization for the current machines:

| ID | Name | Address | Type | Purpose |
|---:|---|---|---|---|
| 201 | `infra-admin-01` | `10.10.10.10` | LXC | Ansible control host |
| 202 | `infra-admin-02` | `10.10.10.11` | KVM | Ansible control host |
| 301 | `dev01` | `10.10.10.101` | KVM | Development VM |
| 302 | `dev02` | `10.10.10.102` | KVM | Development VM |
| 303 | `dev03` | `10.10.10.103` | KVM | Development VM |
| 401 | `infra-fs-01` | `10.10.10.16` | KVM | NFS file server for `/fs3` |
| 501 | `mongodb01` | `10.10.10.32` | KVM | MongoDB test VM |

Existing guests may temporarily retain older IDs or addresses while they are
being rebuilt, migrated, or retired. New and rebuilt guests should follow the
allocation above.

VMID 100 is the older manually-created Debian 13 template and should eventually be retired after the cloud-image replacement has been validated.

VMID 101 is the Debian 12 cloud-init template used for `mongodb01`.

VMID 102 is the validated Debian 13 `genericcloud` template for new Debian 13 guests.

## Configuration boundaries

### Proxmox

Responsible for:

- VM hardware and LXC container definitions
- virtual disks and LXC root filesystems
- bridges
- NAT and inbound port forwarding
- templates and cloning
- cloud-init data for KVM guests
- initial LXC bootstrap through `pct`

### cloud-init

Responsible for initial bootstrap of KVM guests only:

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

Test guests use the institutional resolvers directly:

```text
10.212.226.10
10.212.226.11
```

`10.10.10.1` is the private guest gateway and is **not** a DNS resolver.

KVM cloud-init guests explicitly omit a DNS search domain during the NAT/testing phase. LXC containers may inherit the Proxmox host search domain (`reg.skane.se`); this is acceptable unless it creates an observed resolution problem.

Production hosts should use the appropriate registered institutional DNS domain.
