# Infrastructure decisions

This file records decisions that are useful to retain even when the implementation itself is obvious from the Ansible configuration.

## Full VMs rather than LXC

Use full KVM/QEMU virtual machines for the current workload.

Reasons:

- closer match to future standalone production hosts
- straightforward Docker support
- straightforward Apptainer support
- fewer host-kernel/container namespace interactions
- easier portability of configuration between virtual and physical systems

## Proxmox + Ansible

Use Proxmox for virtualization and Ansible for guest configuration.

Ansible provides the declarative/reproducible machine-state model wanted from systems such as NixOS without requiring a change of guest operating system.

## Treat VMs as replaceable

Prefer rebuilding a guest from:

```text
template -> cloud-init -> Ansible
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

- VMs use private network `10.10.10.0/24`
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

Do not set a search domain for current NAT-only VMs. Production systems should use `lund.skane.se` once they are registered there.

## Git as source of truth

The Git repository is authoritative for:

- Ansible configuration
- infrastructure documentation
- final decisions

Chat history is useful for exploration and troubleshooting but is not the canonical configuration record.
