import tempfile
import unittest
from pathlib import Path
from site_check import audit, render

class Checks(unittest.TestCase):
    def test_findings_and_safe_render(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'index.html').write_text('<html><a href="missing.html">Go</a><img src="x"><h1>Hello</h1></html>')
            r = audit(d)
            self.assertTrue(any('absent' in f['issue'] for f in r['findings']))
            self.assertTrue(any('alt' in f['issue'] for f in r['findings']))
            r['findings'][0]['issue'] = '<script>alert(1)</script>'
            self.assertNotIn('<script>', render(r))
    def test_routes_and_external_links(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'about').mkdir(); Path(d,'about/index.html').write_text('<h1>About</h1>')
            Path(d,'index.html').write_text('<a href="/about/">About</a><a href="https://example.com">External</a>')
            self.assertFalse(any('absent' in f['issue'] for f in audit(d)['findings']))
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'index.html').symlink_to('/etc/hosts')
            with self.assertRaises(ValueError): audit(d)
    def test_escape_and_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): audit(d)
            Path(d,'index.html').write_text('<a href="../secret">x</a>')
            self.assertTrue(any('leaves' in f['issue'] for f in audit(d)['findings']))
if __name__ == '__main__': unittest.main()
