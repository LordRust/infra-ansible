# Disposable Proxmox rebuild exercise

This is a manual, two-VM smoke test, not a new test framework. It exercises the
real provisioning helpers and Ansible roles without external NFS or SMB secrets.
The thin smoke playbook repeats only the role ordering; it uses separate inventory
groups so real `devhosts` variables and Vault are not loaded. Run all controller
commands below from the repository root. Never combine this inventory with the
real inventory.

## 1. Reserve and create the guests on Proxmox

The example uses template 102, IDs 901/902, addresses 10.10.10.201/202, and names
`smoke-fs-01` / `smoke-dev-01`. These are candidates, not verified reservations.
Inspect `qm list`, `pct list`, `qm config 102`, `pvesm status`, repository inventory,
and any manually configured guest addresses first. Both guests and their data
must be disposable. Copy the whole repository checkout to Proxmox.

After verifying those identifiers and capacity, on Proxmox as root:

```bash
set -euo pipefail
proxmox_scripts/create_vm.sh 102 901 201 smoke-fs-01
proxmox_scripts/create_vm.sh 102 902 202 smoke-dev-01
qm config 901
qm config 902
```

Verify `scsi1` is unused on each newly created guest before attaching disks.
The example allocates 2 GiB data disks; the development VM uses 4 GiB RAM and a
24 GiB OS disk for Docker, R and RStudio. Confirm the template root disk is on
`scsi0` and no larger than 24 GiB before the resize (never shrink).

```bash
qm set 901 --scsi1 raid-lvm:2,discard=on
qm set 902 --scsi1 raid-lvm:2,discard=on
qm set 902 --memory 4096
qm disk resize 902 scsi0 24G
qm cloudinit dump 901 user
qm cloudinit dump 901 network
qm cloudinit dump 902 user
qm cloudinit dump 902 network
qm start 901
qm start 902
```

The helpers use the repository bootstrap public key. The controller must have
its matching private key or agent identity; never copy the private key into Git.
Wait for cloud-init to finish. In each guest inspect `lsblk -f` and
`ls -l /dev/disk/by-id/` to confirm the 2 GiB `scsi1` disk identity.

## 2. Configure the controller fixture

Use an existing controller on the private network if this workstation cannot
reach the guests. Install the tools/collections described in `ansible.md` there.

```bash
cp tests/smoke/inventory.example.yml tests/smoke/inventory.yml
export ANSIBLE_ROLES_PATH="$PWD/roles"
```

Edit the ignored `inventory.yml` to match the verified IDs, addresses and devices,
then set `smoke_confirmed: true`. The smoke playbooks otherwise refuse to connect.
Use `--private-key /absolute/path/to/key` on Ansible commands if the default SSH
identity/agent is not appropriate. Add that option consistently to every command.
The fixture UID/GID 25001 is for disposable guests only.

Verify SSH host fingerprints through the Proxmox console before enrollment:

```bash
ansible-playbook -i tests/smoke/inventory.yml admin-local.yml
```

The enrollment playbook uses keyscan, which does not independently authenticate
host keys. Existing entries for reused test addresses need deliberate review.

## 3. Provision, verify, and rerun

```bash
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/provision.yml
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/verify.yml
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/data.yml
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/provision.yml
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/data.yml
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/provision.yml --check --limit smoke-fs-01,smoke-dev-01
```

Acceptance: fresh provisioning and verification succeed; the immediate second
provisioning has no unexplained changes; the second data run does not rewrite
its existing marker. `/smoke-fs` must mount the temporary server by its inventory
address, and the unprivileged fixture identity must be able to write there.
Investigate any package-version availability or platform compatibility failure;
syntax checks do not validate remote downloads.

`verify.yml` checks disk labels, NFS source, Docker/Apptainer/R commands, active
Docker/RStudio services, and RStudio's loopback listener. It does not test RStudio
human password authentication. Guest roles retain the real application pins.
First-run check mode is not a substitute for step 3; see `ansible.md` for limits.

Optionally reboot these two verified disposable VMs, then repeat verification
and the data test to exercise mount/service persistence. The verify playbook
accesses the NFS path as `smoke-user` before checking it to trigger the
configured automount; client root is squashed by the export.

## 4. Negative storage and export checks

Local checks already test synthetic wrong-type, wrong-label, missing-label, and
probe-error results. On the disposable file server, additionally exercise the
real role guard with an intentionally wrong requested label:

```bash
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/provision.yml \
  --limit smoke-fs-01 \
  -e '{"local_filesystems":[{"device":"/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1","label":"wrong-label","path":"/srv/smoke-data","fstype":"ext4"}]}'
```

Expected: failure at label validation before resizing. Repeat with `label` set
to `smoke-fs` and `fstype` set to `xfs`; expect type validation failure. Do not
change the actual on-disk label/type. Run the normal data test afterward to verify
the marker survives.

To exercise the export mount guard, stop client use and unmount `/smoke-fs` on
**smoke-dev-01**. On **smoke-fs-01** only:

```bash
sudo exportfs -ua
sudo umount /srv/smoke-data
sudo exportfs -ra
sudo exportfs -v
```

Expected: `/srv/smoke-data` is not exported while unmounted (an exportfs diagnostic
is acceptable). Inspect the export list, not just the exit status. Restore the
server with `sudo mount /srv/smoke-data` and `sudo exportfs -ra`, then rerun normal
provisioning and data verification. Never use `exportfs -ua` on a real file server
for this exercise. The test does not automatically unmount or stop anything.

## 5. Access revocation

After normal provisioning:

```bash
ansible-playbook -i tests/smoke/inventory.yml tests/smoke/access.yml --limit smoke-dev-01
```

This installs disposable public fixture keys, adds an unrelated supplementary
group, then runs the real base/Docker roles to revoke one key and Docker access.
Assertions verify the retained managed key, unmanaged key, unrelated group, and
unchanged bootstrap authorized-keys checksum. No fixture private keys are stored.
The scenario intentionally changes state on every run. It is not an idempotence
test and refuses check mode. A later normal provisioning run grants Docker
membership again according to the smoke inventory.

## 6. Record results and clean up explicitly

Record the Git revision, template/guest IDs, controller tool versions, pass/fail
results, second-run recap, and any unexplained changes in `rebuild-milestone.md`.
Do not record credentials or decrypted inventory dumps.

Before cleanup, inspect `qm config 901` and `qm config 902` again, confirm names,
attached disks, and that the data is disposable. Only if the example IDs still
match the intended test guests, stop and destroy them explicitly:

```bash
qm stop 901
qm destroy 901
qm stop 902
qm destroy 902
```

Adjust IDs if different ones were reserved. There is deliberately no teardown
script. Do not remove any shared template. Retire corresponding test host-key
entries on the controller only after confirming the addresses were released.
