"""Offline loader regressions; no embedding or chat service is used.

Run: python -m unittest discover -s Basic_RAG -p test_document_loading.py -v
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


MODULE = Path(__file__).resolve().with_name('retriever.py')
KNOWLEDGE = MODULE.with_name('knowledge')


def run_loader(cwd, module=MODULE):
    code = (
        'import importlib.util, json; '
        f'spec=importlib.util.spec_from_file_location("loader", {str(module)!r}); '
        'm=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); '
        'print(json.dumps(m.load_documents()))'
    )
    return subprocess.run([sys.executable, '-c', code], cwd=cwd,
                          capture_output=True, text=True, check=False)


class DocumentLoadingTests(unittest.TestCase):
    def expected_documents(self):
        return {p.name: p.read_text(encoding='utf-8')
                for p in KNOWLEDGE.glob('*.txt')}

    def assert_documents(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.expected_documents())
        self.assertTrue(json.loads(result.stdout))

    def test_project_root(self):
        self.assert_documents(run_loader(MODULE.parent.parent))

    def test_module_directory(self):
        self.assert_documents(run_loader(MODULE.parent))

    def test_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assert_documents(run_loader(folder))

    def test_working_directory_cannot_substitute_documents(self):
        with tempfile.TemporaryDirectory() as folder:
            decoy = Path(folder) / 'knowledge'
            decoy.mkdir()
            (decoy / 'decoy.txt').write_text('Unrelated corpus', encoding='utf-8')
            self.assert_documents(run_loader(folder))

    def copied_loader(self, folder):
        module = Path(folder) / 'retriever.py'
        shutil.copyfile(MODULE, module)
        return module

    def test_missing_knowledge_directory_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_loader(folder, self.copied_loader(folder))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('FileNotFoundError', result.stderr)
            self.assertIn('knowledge', result.stderr)

    def test_empty_knowledge_directory_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            module = self.copied_loader(folder)
            module.with_name('knowledge').mkdir()
            result = run_loader(folder, module)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ValueError', result.stderr)
            self.assertIn('No .txt documents', result.stderr)

    def test_utf8_content_and_text_filter_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            module = self.copied_loader(folder)
            knowledge = module.with_name('knowledge')
            knowledge.mkdir()
            content = 'caff\u00e8, \u03a9, \u4f60\u597d\n'
            (knowledge / 'sample.txt').write_text(content, encoding='utf-8')
            (knowledge / 'ignore.md').write_text('excluded', encoding='utf-8')
            result = run_loader(folder, module)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {'sample.txt': content})


if __name__ == '__main__':
    unittest.main()
