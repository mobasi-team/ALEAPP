import os
import sys
import unittest


ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.html_security import (
    TrustedHtml,
    escape_attr,
    escape_text,
    sanitize_html_fragment,
    sanitize_url,
    trust_html,
)


class TestHtmlSecurity(unittest.TestCase):
    def test_escape_text_escapes_html_sensitive_chars(self):
        self.assertEqual(escape_text('<tag attr="x">'), '&lt;tag attr=&quot;x&quot;&gt;')
        self.assertEqual(escape_text(None), '')

    def test_escape_attr_escapes_quotes_and_angle_brackets(self):
        self.assertEqual(
            escape_attr('" onclick="alert(1)'),
            '&quot; onclick=&quot;alert(1)',
        )

    def test_sanitize_url_blocks_javascript_and_non_media_data(self):
        self.assertEqual(sanitize_url('javascript:alert(1)'), '#')
        self.assertEqual(sanitize_url('data:text/html;base64,PHNjcmlwdA=='), '#')

    def test_sanitize_url_allows_media_data_when_enabled(self):
        self.assertEqual(
            sanitize_url('data:image/png;base64,AAAA', allow_data_media=True),
            'data:image/png;base64,AAAA',
        )

    def test_sanitize_html_fragment_strips_scripts_and_unsafe_attrs(self):
        dirty = '<p onclick="evil()">ok</p><script>alert(1)</script><a href="javascript:1">x</a>'
        clean = sanitize_html_fragment(dirty)
        self.assertIn('<p>ok</p>', clean)
        self.assertNotIn('script', clean.lower())
        self.assertNotIn('onclick', clean.lower())
        self.assertNotIn('javascript:', clean.lower())

    def test_trusted_html_wrapper(self):
        trusted = trust_html('<b>safe</b>')
        self.assertIsInstance(trusted, TrustedHtml)
        self.assertEqual(str(trusted), '<b>safe</b>')


if __name__ == '__main__':
    unittest.main()
