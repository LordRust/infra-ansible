"""Run the role's access assertions without changing accounts or key files."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[2]
KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestFixture comment"


class AccessPolicy(unittest.TestCase):
    def test_policy(self):
        cases = [
            ("additive", "base", {"managed_users": [{"name": "test", "ssh_keys": [KEY]}]}, True),
            ("revoked", "base", {"managed_users": [{"name": "test", "revoked_ssh_keys": [KEY]}]}, True),
            ("contradiction", "base", {"managed_users": [{"name": "test", "ssh_keys": [KEY],
              "revoked_ssh_keys": [KEY.replace("comment", "different-comment")]}]}, False),
            ("invalid key", "base", {"managed_users": [{"name": "test", "revoked_ssh_keys": ["invalid"]}]}, False),
            ("no keys", "base", {"managed_users": [{"name": "test"}]}, True),
            ("docker revoke", "docker", {"docker_users": ["keep"], "docker_revoked_users": ["remove"]}, True),
            ("docker conflict", "docker", {"docker_users": ["same"], "docker_revoked_users": ["same"]}, False),
        ]
        for name, role, variables, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                playbook = Path(tmp) / "policy.yml"
                playbook.write_text(yaml.safe_dump([{
                    "name": "Validate access policy without changing accounts",
                    "hosts": "localhost", "gather_facts": False, "vars": variables,
                    "tasks": [{"ansible.builtin.import_tasks": str(
                        REPO / f"roles/{role}/tasks/validate_access.yml")}],
                }]))
                result = subprocess.run(
                    ["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook), "--check"],
                    env=dict(os.environ, ANSIBLE_LOCAL_TEMP=str(Path(tmp) / "ansible")),
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode == 0, expected, result.stdout + result.stderr)
                if not expected:
                    self.assertIn('"evaluated_to": false', result.stdout)


if __name__ == "__main__":
    unittest.main()
