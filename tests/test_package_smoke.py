import pathlib
import tomllib
import unittest

import Aria
from Aria.Windows import FileSystem


class PackageSmokeTests(unittest.TestCase):
   def test_import_has_main_entrypoint(self):
      self.assertTrue(callable(Aria.Main))

   def test_windows_filesystem_exports_expected_paths(self):
      self.assertEqual(FileSystem.PythonExtension, ".py")
      self.assertTrue(FileSystem.Desktop.endswith("\\"))
      self.assertTrue(FileSystem.Documents.endswith("\\"))

   def test_pyproject_declares_console_script(self):
      pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
      data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
      self.assertEqual(data["project"]["scripts"]["aria"], "Aria:Main")
      self.assertGreaterEqual(data["project"]["requires-python"], ">=3.9")


if __name__ == "__main__":
   unittest.main()
