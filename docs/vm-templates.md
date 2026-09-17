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

The Proxmox 100-series is reserved for VM templates.

- VMID 100 — older manually-created Debian 13 template; retain temporarily
- VMID 101 — Debian 12 cloud-init template
- VMID 102 — Debian 13 `genericcloud` cloud-init template; validated for new Debian 13 guests

Retire VMID 100 after any remaining users of the older template have been migrated or are no longer needed.

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

Explicitly suppress the Proxmox host's DNS search domain on these NAT-only VMs:

```bash
qm set 101 --searchdomain ''
```

If `searchdomain` is left unset, Proxmox generates cloud-init network data
using the host search domain (`reg.skane.se`). Setting it to an empty string
results in no `search:` entry in the generated cloud-init network
configuration. `qm config` will show an explicit empty value as
`searchdomain:`; this is expected.

Then convert:

```bash
qm template 101
```

There is normally no need to boot the generic template before conversion.

## Clone configuration

Example for a second admin VM using the Debian 13 template:

```bash
qm clone 102 202 --name infra-admin-02 --full

qm set 202 \
    --ipconfig0 ip=10.10.10.11/24,gw=10.10.10.1

qm set 202 --nameserver "10.212.226.10 10.212.226.11"
qm set 202 --ciuser jonas
qm set 202 --sshkey /path/to/id_ed25519.pub
```

The empty `searchdomain` should normally be inherited from the template.
Verify that the generated network data has no `search:` entry rather than
relying on an unset VM option.

Before first boot, verify generated cloud-init content:

```bash
qm cloudinit dump 202 user
qm cloudinit dump 202 network
```

Then:

```bash
qm start 202
```

SSH can briefly return `Connection refused` while the guest is still
completing its first boot. Once cloud-init and `ssh.service` have finished
starting, key-based login should work normally.

## First-boot rule

Set at least the following **before first boot**:

- IP address and gateway
- DNS servers
- cloud-init user
- SSH public key

Cloud-init user/key setup is generally once-per-instance. Adding the key only after the guest has already completed first boot may not update the user's `authorized_keys` automatically.

A console password is not required for normal deployment; the Debian generic
cloud image is intended to be accessed using the cloud-init-provisioned SSH key.

## Existing manually-created guests

Do not rebuild a healthy existing guest solely because it came from the older manual template.

Use the cloud-image template for new systems and let Ansible keep guest configuration reproducible.
