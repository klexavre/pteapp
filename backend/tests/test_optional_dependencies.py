import os
import subprocess
import sys
import unittest


class OptionalDependencyImportTests(unittest.TestCase):
    def test_server_imports_without_whisper_or_torch(self):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        code = """
import os
import sys
sys.path.insert(0, os.getcwd())
import server
print('server-import-ok')
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("server-import-ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
