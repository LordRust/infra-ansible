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
