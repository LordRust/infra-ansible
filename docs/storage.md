# Storage

## Physical/logical layout

The Proxmox host uses hardware RAID through a Dell PERC H710.

Relevant logical disks:

- `/dev/sda` — approximately 500 GB, Proxmox/system disk
- `/dev/sdb` — approximately 10.4 TB, large RAID logical disk for VM storage

## VM storage

The large RAID logical disk was configured as LVM-thin:

```bash
pvcreate /dev/sdb1
vgcreate vg_raid /dev/sdb1
lvcreate -l 95%VG -T vg_raid/data
```

Proxmox storage configuration:

```ini
lvmthin: raid-lvm
        thinpool data
        vgname vg_raid
        content images,rootdir
```

Verify with:

```bash
pvesm status
```

Use `raid-lvm` for VM disks and cloud-init drives.

## LVM-thin note

The thin pool was created with an 8 MiB chunk size and emitted a warning that smaller chunks and/or disabled zeroing could improve thin-provisioning behavior.

The current pool is usable for this environment and was retained rather than recreated during initial testing.

If storage is rebuilt later, revisit the chunk-size/zeroing choice deliberately.

## Guest disks

For ordinary guests:

- keep the OS layout simple
- ext4 is sufficient unless a guest has a specific requirement
- avoid adding LVM inside a VM unless the guest actually needs it

For data-heavy services such as MongoDB, consider a separate virtual data disk rather than making the generic template root disk large.

## Current data disks

| VMID | Guest | Proxmox disk | Initial size | Guest filesystem |
|---:|---|---|---:|---|
| 301 | `dev01` | `scsi1` | 100 GiB | ext4, label `local`, mounted at `/local` |
| 401 | `infra-fs-01` | `scsi1` | 1000 GiB | ext4, label `fs3`, mounted at `/srv/fs3` |

`infra-fs-01` exports `/srv/fs3` over NFS; development VMs mount that export
at `/fs3`. Do not attach the same ordinary ext4 virtual disk read/write to
multiple VMs.

## Creating and attaching a data disk

Create virtual disks through Proxmox rather than creating thin LVs manually.
First verify the storage ID and the next free controller slot:

```bash
pvesm status
qm config 301
```

For example, the existing data disks were attached on `scsi1` from the
`raid-lvm` thin pool:

```bash
qm set 301 --scsi1 raid-lvm:100,discard=on
qm set 401 --scsi1 raid-lvm:1000,discard=on
```

The size is the thin volume's logical size in GiB. Physical pool space is
consumed as blocks are written, but free data and metadata space in the thin
pool must still be monitored.

After attaching a disk, identify it inside the guest before configuring
Ansible:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
ls -l /dev/disk/by-id/
```

For these `scsi1` disks the expected persistent path is:

```text
/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1
```

Confirm that it resolves to the disk of the expected size on each VM. Record
the verified path, filesystem label, and mount point in that VM's `host_vars`
file. The `local-filesystem` role can format a blank disk as ext4, assigns its
label, adds the label-based `/etc/fstab` entry, and mounts it. It refuses to
replace a filesystem of another type. An existing filesystem with the wrong
label must be corrected manually and deliberately rather than being relabeled
automatically.

## Growing a data disk

Virtual disks and ext4 filesystems can grow online. They are not shrunk by
this procedure. Check the current configuration and pool capacity first:

```bash
qm config 301
pvesm status
lvs -a -o lv_name,lv_size,data_percent,metadata_percent vg_raid
```

Set a new absolute disk size or add a relative amount. Examples:

```bash
qm disk resize 301 scsi1 200G
qm disk resize 401 scsi1 +500G
```

Then rerun the appropriate guest playbook:

```bash
ansible-playbook -i inventory.ini dev-base.yml --limit dev01
ansible-playbook -i inventory.ini fs-base.yml --limit infra-fs-01
```

The `local-filesystem` role uses `resizefs: true`, so ext4 grows to fill the
larger virtual device. Verify the result in the guest with:

```bash
lsblk
df -h /local
df -h /srv/fs3
```

Only the relevant `df` command exists on each guest. NFS clients require no
mount change when the filesystem backing `/fs3` grows.
