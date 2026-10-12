import importlib.util
import unittest
import json
from pathlib import Path
import subprocess
import sys


class NormalizeTitleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("resume_app"), "normalization module is missing"
        )
        from resume_app import normalize_title
        self.normalize_title = normalize_title

    def test_trims_surrounding_ascii_whitespace(self):
        self.assertEqual(self.normalize_title(" \tBuy milk\n "), "Buy milk")

    def test_preserves_internal_whitespace(self):
        self.assertEqual(self.normalize_title("  Buy  milk  "), "Buy  milk")

    def test_preserves_unicode_and_strips_unicode_whitespace(self):
        self.assertEqual(self.normalize_title("\u2003café 🚀\u00a0"), "café 🚀")

    def test_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            self.normalize_title("")

    def test_rejects_ascii_whitespace_title(self):
        with self.assertRaises(ValueError):
            self.normalize_title(" \t\r\n")

    def test_rejects_unicode_whitespace_title(self):
        with self.assertRaises(ValueError):
            self.normalize_title("\u2003\u00a0")


class MakeTaskTests(unittest.TestCase):
    def make_task(self, title):
        import resume_app
        self.assertTrue(hasattr(resume_app, "make_task"), "task creation is missing")
        return resume_app.make_task(title)

    def test_exact_task_fields_and_false_boolean(self):
        task = self.make_task("  Buy milk  ")
        self.assertEqual(task, {"title": "Buy milk", "completed": False})
        self.assertIs(task["completed"], False)

    def test_preserves_internal_whitespace_and_unicode(self):
        for title, expected in [("  Buy  milk  ", "Buy  milk"), ("\u2003café 🚀\u00a0", "café 🚀")]:
            with self.subTest(title=title):
                self.assertEqual(self.make_task(title), {"title": expected, "completed": False})

    def test_rejects_blank_titles(self):
        for title in ["", " \t\r\n", "\u2003\u00a0"]:
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    self.make_task(title)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        app = Path(__file__).resolve().parents[1] / "resume_app.py"
        return subprocess.run([sys.executable, str(app), *args], capture_output=True, text=True)

    def test_valid_titles_emit_exact_json_matching_library(self):
        from resume_app import make_task
        for title, expected in [("-task", "-task"), ("--help", "--help"), ("  Buy milk  ", "Buy milk"), ("  Buy  milk  ", "Buy  milk"), ("\u2003café 🚀\u00a0", "café 🚀")]:
            with self.subTest(title=title):
                result = self.run_cli(title)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(result.stdout.strip(), "CLI task JSON is missing")
                task = json.loads(result.stdout)
                self.assertEqual(task, {"title": expected, "completed": False})
                self.assertIs(task["completed"], False)
                self.assertEqual(task, make_task(title))

    def test_blank_titles_exit_two_without_task_json(self):
        for title in ["", " \t\r\n", "\u2003\u00a0"]:
            with self.subTest(title=title):
                result = self.run_cli(title)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_missing_title_exits_two_without_task_json(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
