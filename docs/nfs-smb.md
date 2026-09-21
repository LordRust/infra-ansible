# NFS and SMB

## General model

Mount network filesystems inside each full VM.

Do not mount NFS/SMB on the Proxmox host merely to expose it into normal KVM guests.

Ansible manages guest mount configuration.

## NFS

Current development mounts:

```yaml
nfs_mounts:
  - path: /fs1
    src: rs-fs1.lunarc.lu.se:/disk

  - path: /fs2
    src: rs-fs2.lunarc.lu.se:/disk

  - path: /fs3
    src: infra-fs-01:/srv/fs3
    opts: rw,_netdev,x-systemd.automount,nofail
```

Example role:

```yaml
- name: Install NFS client
  ansible.builtin.apt:
    name: nfs-common
    state: present

- name: Configure and mount NFS filesystems
  ansible.posix.mount:
    path: "{{ item.path }}"
    src: "{{ item.src }}"
    fstype: "{{ item.fstype | default('nfs4') }}"
    opts: "{{ item.opts | default('vers=4.0') }}"
    state: mounted
  loop: "{{ nfs_mounts }}"
```

Per-mount options can be overridden in `nfs_mounts.yml`:

```yaml
nfs_mounts:
  - path: /fs1
    src: rs-fs1.lunarc.lu.se:/disk
    opts: ro,vers=4.0

  - path: /fs2
    src: rs-fs2.lunarc.lu.se:/disk
    opts: rw,vers=4.0
```

## NFS and NAT

VM traffic is source-NATed by Proxmox.

The NFS servers therefore see the client as:

```text
10.231.229.23
```

rather than as `10.10.10.x`.

The NFS server `/etc/exports` must permit the Proxmox host address as appropriate.

A previous `mount.nfs: Permission denied` problem was caused by server-side export permissions, not by the guest NFS client role.

The locally hosted `/fs3` export is different: traffic between the development
VMs and `infra-fs-01` remains on `10.10.10.0/24` and is not source-NATed.

## Local NFS server

`infra-fs-01` (`10.10.10.16`, VMID 401) mounts its dedicated data disk at
`/srv/fs3` and exports it to the private VM network. Its host variables define:

```yaml
nfs_exports:
  - path: /srv/fs3
    clients: 10.10.10.0/24
    options: rw,sync,no_subtree_check
```

Apply the server configuration with:

```bash
ansible-playbook -i inventory.ini fs-base.yml
```

The normal NFS `root_squash` behavior remains enabled because
`no_root_squash` is not specified. Client access is read/write, while `/fs1`
and `/fs2` retain the client role's read-only default unless they have an
explicit `opts` override.

## SMB/CIFS

Use a separate `smb-client` role.

Suggested variable split:

```text
group_vars/devhosts/
├── smb_mounts.yml
├── smb_credentials.yml
└── vault.yml
```

Example mount definition:

```yaml
smb_mounts:
  - path: /labshare
    src: //fileserver.example.org/labshare
    credential: labshare
    opts: ro,vers=3.0
```

Credential metadata:

```yaml
smb_credentials:
  - name: labshare
    username: jonas
    password: "{{ vault_smb_labshare_password }}"
    domain: MYDOMAIN
```

The actual password belongs in the Vault-encrypted file:

```yaml
vault_smb_labshare_password: "secret"
```

Encrypt it with:

```bash
ansible-vault encrypt group_vars/devhosts/vault.yml
```

## SMB role pattern

Install:

```yaml
- name: Install CIFS client
  ansible.builtin.apt:
    name: cifs-utils
    state: present
```

Store root-only credential files under:

```text
/etc/samba/credentials/
```

and use mount options such as:

```text
credentials=/etc/samba/credentials/labshare
```

Do not place plaintext passwords in `/etc/fstab`, `smb_mounts.yml`, or unencrypted Git content.
