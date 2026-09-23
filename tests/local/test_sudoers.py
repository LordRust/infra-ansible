"""Validate the base role's rendered sudoers content for empty and populated lists."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from jinja2 import Environment
import yaml


ROLE_TASKS = Path(__file__).resolve().parents[2] / "roles/base/tasks/main.yml"


class SudoersContent(unittest.TestCase):
    def test_empty_and_populated_users(self):
        tasks = yaml.safe_load(ROLE_TASKS.read_text())
        task = next(task for task in tasks if task["name"] == "Configure passwordless sudo users")
        template = Environment().from_string(task["ansible.builtin.copy"]["content"])

        for users in ([], ["smoke-user"]):
            with self.subTest(users=users), tempfile.TemporaryDirectory() as tmp:
                content = template.render(sudo_users=users)
                self.assertTrue(content.strip(), "Ansible copy needs nonempty content")
                self.assertEqual("NOPASSWD" in content, bool(users))
                target = Path(tmp) / "sudoers"
                target.write_text(content)
                result = subprocess.run(["/usr/sbin/visudo", "-cf", str(target)],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
