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
- [x] 6. Support explicit access revocation while keeping additions additive.
- [x] 7. Add Proxmox provisioning preflight checks and recovery guidance.
- [x] 8. Add disposable guest smoke tests and record available evidence.
- [ ] Runtime acceptance on two disposable Proxmox guests.

A checked commit means its implementation is present, not that live acceptance
has passed. Record actual validation below; do not infer it from this checklist.

## Validation evidence

- Initial review: all three existing shell scripts passed bash syntax and ShellCheck.
- Commit 1: documentation reviewed against the current implementation; no live changes.

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

- Commit 6: syntax and lint passed. Seven local policy cases exercised the
  actual assertions, including same-key/different-comment conflicts and Docker
  grant/revoke overlap. Actual guest membership/key removal remains pending.

- Commit 7: shell syntax, ShellCheck, Python compilation, and six local
  preflight tests passed (multiple malformed-input/collision cases). No Proxmox
  mutation was attempted. Read-only SSH to `pgm2` failed authentication, so actual
  Proxmox CLI responses and guest creation have not been runtime-validated.

- Commit 8: `scripts/check.sh --fixtures-only` passed with ansible-core 2.19.11,
  pinned collections, YAML lint, basic Ansible lint (six documented naming
  exceptions), shell checks, all ten local tests, and syntax checks for all
  top-level and four smoke playbooks. The smoke refusal test exercised all four
  playbooks with an SSH sentinel and confirmed no connection before confirmation.
- Real inventory variable loading remains unvalidated: the development Vault
  password source was not available. The full check reports this explicitly.
- Live acceptance remains unperformed: root SSH through the configured `pgm2`
  alias returned `Permission denied (publickey,password)`. No guest was created,
  configured, stopped, or destroyed. Run `docs/disposable-rebuild.md` from a
  controller with access and record the actual guest/template IDs and recaps here.
- Follow-up: the first disposable server run exposed empty `sudo_users` rendering
  as an invalid `copy` task. The base role now renders a comment-only sudoers
  file in that case. A local regression test checks empty and populated lists
  with `visudo`; the full fixture validation suite passed with 11 tests.

## Local commit map

| Step | Commit | Subject |
|---|---|---|
| 1 | `24a52f5` | Streamline agent guidance and record rebuild milestone |
| 2 | `ad419e3` | Add repeatable local validation |
| 3 | `69cd83b` | Make development package provisioning self-contained |
| 4 | `9969b3e` | Configure file servers before development clients |
| 5 | `9e297eb` | Strengthen filesystem and NFS validation |
| 6 | `3c48d38` | Support explicit access revocation |
| 7 | `b51c383` | Add Proxmox provisioning preflight checks |
| 8 | This document's smoke-test commit | Document and verify disposable guest rebuilds |

## Deferred

SMB completion, backup automation, production hardening, dedicated MongoDB/LXC
runtime tests, and migration tooling for the larger QEMU/KVM environment.
