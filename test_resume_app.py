import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


class NormalizeTitleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("resume_app"), "normalization module is missing")
        self.app = importlib.import_module("resume_app")
        self.assertTrue(callable(getattr(self.app, "normalize_title", None)))

    def test_trims_boundary_whitespace(self):
        for title, expected in [("  Buy milk  ", "Buy milk"), ("Buy milk", "Buy milk"),
                                ("\t\n Buy milk\r ", "Buy milk"),
                                ("\u2003Café ☕\u00a0", "Café ☕")]:
            with self.subTest(title=title):
                self.assertEqual(self.app.normalize_title(title), expected)

    def test_preserves_remaining_characters(self):
        for title, expected in [("  MiXeD  interior\tspace  ", "MiXeD  interior\tspace"),
                                ("  Café ☕  ", "Café ☕"),
                                ("  Cafe\u0301  ", "Cafe\u0301")]:
            with self.subTest(title=title):
                self.assertEqual(self.app.normalize_title(title), expected)

    def test_rejects_empty_titles(self):
        for title in ["", " \t\n ", "\u2003\u00a0"]:
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    self.app.normalize_title(title)


class MakeTaskTests(unittest.TestCase):
    def setUp(self):
        self.app = importlib.import_module("resume_app")
        self.assertTrue(callable(getattr(self.app, "make_task", None)), "make_task is missing")

    def test_exact_task_shape(self):
        for title, expected in [("  Buy milk  ", "Buy milk"),
                                ("\u2003Café ☕\u00a0", "Café ☕"),
                                ("  Cafe\u0301  ", "Cafe\u0301"),
                                (" MiXeD  interior\tspace ", "MiXeD  interior\tspace")]:
            with self.subTest(title=title):
                task = self.app.make_task(title)
                self.assertEqual(task, {"title": expected, "completed": False})
                self.assertEqual(set(task), {"title", "completed"})
                self.assertIs(task["completed"], False)

    def test_rejects_empty_titles(self):
        for title in ["", " \t\n ", "\u2003\u00a0"]:
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    self.app.make_task(title)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(Path(__file__).with_name("resume_app.py")), *args],
                              capture_output=True, text=True)

    def test_valid_titles(self):
        for title, expected in [("  Buy milk  ", "Buy milk"),
                                ("-buy", "-buy"), ("--help", "--help"),
                                ("--", "--"),
                                ("\u2003Café ☕\u00a0", "Café ☕"),
                                ("  Cafe\u0301  ", "Cafe\u0301"),
                                (" MiXeD  interior\tspace ", "MiXeD  interior\tspace")]:
            with self.subTest(title=title):
                result = self.run_cli(title)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.endswith("\n"), "JSON output needs a newline")
                task = json.loads(result.stdout)
                self.assertEqual(task, {"title": expected, "completed": False})
                self.assertIs(task["completed"], False)
                self.assertEqual(task, importlib.import_module("resume_app").make_task(title))

    def test_invalid_arguments(self):
        for args in [(), ("",), (" \t\n ",), ("\u2003\u00a0",), ("one", "two")]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
