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

## Current VMs

| VMID | Name | Address | Purpose |
|---:|---|---|---|
| 200 | `devvm01` | `10.10.10.11` | Development VM |
| 201 | `infra-admin-01` | `10.10.10.10` | Ansible control host |
| 202 | `mongodb01` | `10.10.10.12` | MongoDB test VM |

VMID 100 is the older manually-created Debian 13 template and should eventually be retired after the cloud-image replacement has been validated.

VMID 101 is the Debian 12 cloud-init template used for `mongodb01`.

A Debian 13 genericcloud template should be created for future Debian 13 guests.

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

- initial user
- SSH public key
- static address
- gateway
- DNS servers
- hostname/instance identity

### Ansible

Responsible for persistent guest configuration:

- users and groups
- packages
- external package repositories
- NFS/SMB mounts
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
