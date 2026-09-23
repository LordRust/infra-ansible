# Reliable rebuild milestone

Goal: reliably rebuild this playground while preserving Proxmox learning and
hypervisor-independent guest configuration. Runtime acceptance uses a disposable
Debian 13 file server and development VM, not existing data disks.

## Commit checklist

- [x] 1. Streamline agent guidance and record this milestone.
- [x] 2. Add repeatable local validation and tested dependency versions.
- [x] 3. Make development package provisioning self-contained.
- [x] 4. Configure file servers before development clients.
- [x] 5. Strengthen filesystem and NFS validation.
- [ ] 6. Support explicit access revocation while keeping additions additive.
- [ ] 7. Add Proxmox provisioning preflight checks and recovery guidance.
- [ ] 8. Add disposable guest smoke tests and record evidence.

A checked commit means its implementation is present, not that live acceptance
has passed. Record actual validation below; do not infer it from this checklist.

## Validation evidence

- Initial review: all three existing shell scripts passed bash syntax and ShellCheck.
- Commit 1: documentation reviewed against the current implementation; no live changes.

## Deferred

SMB completion, backup automation, production hardening, dedicated MongoDB/LXC
runtime tests, and migration tooling for the larger QEMU/KVM environment.

- Commit 2: all five playbook syntax checks, YAML lint, basic Ansible lint,
  bash syntax, and ShellCheck passed. Six narrowly scoped lint exceptions retain
  existing public names. Inventory graph passed; full variable loading correctly
  stops with a clear error when Vault credentials are missing.

- Commit 3: development syntax check, YAML lint, and basic Ansible lint passed.
  Clean-template installation remains a disposable-guest acceptance check.

- Commit 4: site syntax, YAML and shell checks passed. Stubbed wrapper tests
  verified working-directory independence, argument forwarding, and refusal
  without an explicit inventory. NFS runtime validation is still pending.

- Commit 5: site syntax and lint passed. The local assertion regression test
  exercises existing/blank devices, wrong types/labels, absent labels, and probe
  errors without device access. Real mounting, growth, and reboot/export behavior
  remain pending on disposable guests.
