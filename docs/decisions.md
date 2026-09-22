# Infrastructure decisions

This file records decisions that are useful to retain even when the implementation itself is obvious from the Ansible configuration.

## Selective use of LXC and KVM

Use LXC selectively for lightweight infrastructure where a separate guest kernel is not useful. Keep KVM/QEMU for workloads where kernel isolation, conventional block-device ownership, or container-runtime behavior is more important.

Current policy:

- `infra-admin-01` is an unprivileged Debian 13 LXC container.
- Administration/front-end/utility services are good LXC candidates.
- Development systems remain KVM because Docker/Apptainer and VM-like behavior are useful there.
- MongoDB remains KVM; its application cache dominates memory use and conventional VM isolation is preferable.
- The NFS file server remains KVM for now, keeping the simple `Proxmox -> virtual disk -> guest filesystem -> NFS export` ownership model.

Debian 13 LXC containers use `nesting=1`; Proxmox warns about systemd 257 without it. Containers remain unprivileged unless a specific requirement justifies otherwise.

## Proxmox + Ansible

Use Proxmox for virtualization and Ansible for guest configuration.

Ansible provides the declarative/reproducible machine-state model wanted from systems such as NixOS without requiring a change of guest operating system.

## Treat guests as replaceable

Prefer rebuilding a guest from a documented bootstrap path, for example:

```text
KVM: template -> cloud-init -> Ansible
LXC: template -> pct bootstrap -> Ansible
```

rather than relying on undocumented manual repair.

## Official cloud images

Use official Debian `genericcloud` images for new Proxmox templates.

The original Debian 13 template was installed manually and later converted to cloud-init. That works, but the cloud-image workflow is simpler and more reproducible.

Existing working VMs do not need to be rebuilt solely to change their origin.

## Storage

Use LVM-thin on top of the existing PERC hardware RAID.

Do not put ZFS on top of the hardware RAID controller.

## Networking

During testing:

- guests use private network `10.10.10.0/24`
- Proxmox performs source NAT through `vmbr0`
- selected inbound ports are DNATed to individual VMs

Production hosts are expected to use normal institutional networking rather than this NAT arrangement.

## DNS

Test guests use:

```text
10.212.226.10
10.212.226.11
```

Do not configure `10.10.10.1` as DNS unless a resolver is deliberately installed on the Proxmox host.

KVM cloud-init guests explicitly omit the search domain. LXC may inherit the Proxmox host search domain (`reg.skane.se`); this is acceptable unless it causes a concrete name-resolution problem. Production systems should use the appropriate registered institutional domain.

## Git as source of truth

The Git repository is authoritative for:

- Ansible configuration
- infrastructure documentation
- final decisions

Chat history is useful for exploration and troubleshooting but is not the canonical configuration record.
