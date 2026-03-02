import os
import tempfile
import unittest

from scripts.tools import audit_raw_html_sinks


class TestAuditXssSinks(unittest.TestCase):
    def test_audit_flags_unsafe_patterns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_path = os.path.join(tmpdir, 'bad_sink.py')
            js_path = os.path.join(tmpdir, 'bad_sink.js')

            with open(py_path, 'w', encoding='utf8') as f:
                f.write('report.write_raw_html("<b>unsafe</b>")\n')
            with open(js_path, 'w', encoding='utf8') as f:
                f.write('target.innerHTML = attackerControlled;\n')

            findings = audit_raw_html_sinks.audit_paths([py_path, js_path])
            messages = '\n'.join(f['message'] for f in findings)
            self.assertIn('write_raw_html', messages)
            self.assertIn('innerHTML', messages)

    def test_repo_sinks_are_clean(self):
        repo_scripts = '/Users/js/consulting_work/side_projects/ALEAPP/scripts'
        findings = audit_raw_html_sinks.audit_paths([repo_scripts])
        self.assertEqual(findings, [])


if __name__ == '__main__':
    unittest.main()
