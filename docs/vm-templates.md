# VM templates and cloud-init

## Preferred workflow

Use official Debian `genericcloud` images for new templates.

The workflow is:

```text
official Debian genericcloud image
        |
        v
empty Proxmox VM
        |
        v
import cloud disk
        |
        v
attach cloud-init drive
        |
        v
convert to template
        |
        v
clone
        |
        v
set per-VM cloud-init values
        |
        v
first boot
```

The template itself should remain generic.

## Current templates

- VMID 100 — older manually-created Debian 13 template; retain temporarily
- VMID 101 — Debian 12 cloud-init template

Create a new Debian 13 genericcloud template for future Debian 13 guests, then retire VMID 100 after validation.

## Example template creation

Example using VMID 101 and `raid-lvm`:

```bash
qm create 101 \
    --name debian-12-cloudinit \
    --memory 2048 \
    --cores 2 \
    --net0 virtio,bridge=vmbr1 \
    --ostype l26 \
    --scsihw virtio-scsi-pci

qm importdisk 101 \
    /root/debian-12-genericcloud-amd64.qcow2 \
    raid-lvm
```

Inspect the imported disk name:

```bash
qm config 101
```

Attach it, using the exact volume shown by `qm config`:

```bash
qm set 101 --scsi0 raid-lvm:vm-101-disk-0,discard=on
qm set 101 --ide2 raid-lvm:cloudinit
qm set 101 --boot order=scsi0
qm set 101 --serial0 socket --vga serial0
qm resize 101 scsi0 16G
```

Then convert:

```bash
qm template 101
```

There is normally no need to boot the generic template before conversion.

## Clone configuration

Example:

```bash
qm clone 101 202 --name mongodb01 --full

qm set 202 \
    --ipconfig0 ip=10.10.10.12/24,gw=10.10.10.1

qm set 202 --nameserver "10.212.226.10 10.212.226.11"
qm set 202 --ciuser jonas
qm set 202 --sshkey /path/to/id_ed25519.pub
```

Do not configure a search domain for the current NAT-only test VMs.

Before first boot, verify generated cloud-init content:

```bash
qm cloudinit dump 202 user
qm cloudinit dump 202 network
```

Then:

```bash
qm start 202
```

## First-boot rule

Set at least the following **before first boot**:

- IP address and gateway
- DNS servers
- cloud-init user
- SSH public key

Cloud-init user/key setup is generally once-per-instance. Adding the key only after the guest has already completed first boot may not update the user's `authorized_keys` automatically.

## Existing manually-created guests

Do not rebuild a healthy existing guest solely because it came from the older manual template.

Use the cloud-image template for new systems and let Ansible keep guest configuration reproducible.
