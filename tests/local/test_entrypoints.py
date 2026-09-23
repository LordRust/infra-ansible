"""Check controller argument forwarding and smoke refusal before any SSH call."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


class Entrypoints(unittest.TestCase):
    def test_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "ansible-playbook"
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "$PWD" "$@"\n')
            stub.chmod(0o755)
            env = dict(os.environ, PATH=tmp + ":" + os.environ["PATH"])
            script = str(REPO / "scripts/run_all_ansible.sh")
            result = subprocess.run([script, "-i", "tests/smoke/inventory.yml", "--limit", "smoke-dev-01"],
                                    cwd=tmp, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [str(REPO), "site.yml", "-i",
                             "tests/smoke/inventory.yml", "--limit", "smoke-dev-01"])
            result = subprocess.run([script, "--check"], env=env, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)

    def test_unconfirmed_smoke_never_connects(self):
        for name in ("provision", "verify", "access", "data"):
            with self.subTest(playbook=name), tempfile.TemporaryDirectory() as tmp:
                sentinel = Path(tmp) / "ssh-called"
                stub = Path(tmp) / "ssh"
                stub.write_text(f'#!/bin/sh\ntouch "{sentinel}"\nexit 99\n')
                stub.chmod(0o755)
                env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(Path(tmp) / "ansible"),
                           ANSIBLE_ROLES_PATH=str(REPO / "roles"), ANSIBLE_SSH_EXECUTABLE=str(stub))
                result = subprocess.run([
                    "ansible-playbook", "-i", str(REPO / "tests/smoke/inventory.example.yml"),
                    str(REPO / f"tests/smoke/{name}.yml"), "--check",
                ], env=env, text=True, capture_output=True, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Copy inventory.example.yml", result.stdout, result.stdout + result.stderr)
                self.assertFalse(sentinel.exists(), "An unconfirmed smoke test tried to connect")


if __name__ == "__main__":
    unittest.main()
