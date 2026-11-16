import unittest
from research import parse,quality,safe_cell

def feed(s):return ('<feed xmlns="http://www.w3.org/2005/Atom">'+s+'</feed>').encode()
def entry(id='2401.12345v1'):return f'<entry><id>http://arxiv.org/abs/{id}</id><title>Title</title><published>2024-01-02</published><summary>Abstract evidence here.</summary><author><name>Author</name></author></entry>'
class Tests(unittest.TestCase):
 def test_valid(self):
  r,n=parse(feed(entry()));self.assertTrue(quality(r,1)['structural_pass']);self.assertFalse(quality(r,1)['delivery_ready'])
 def test_duplicates(self):
  r,n=parse(feed(entry()+entry('2401.12345v2')));self.assertEqual(n,1);self.assertFalse(quality(r,2)['structural_pass'])
 def test_missing(self):
  r,n=parse(feed(entry().replace('<title>Title</title>','')));self.assertFalse(quality(r,1)['structural_pass'])
 def test_xml(self):
  with self.assertRaises(ValueError):parse(b'<!DOCTYPE x><feed/>')
 def test_source(self):
  with self.assertRaises(ValueError):parse(feed(entry('../secret')))
 def test_evidence(self):
  r,n=parse(feed(entry()));r[0]['summary']='Invented';self.assertFalse(quality(r,1)['structural_pass'])
 def test_formula(self):self.assertEqual(safe_cell('=1+1'),"'=1+1")
