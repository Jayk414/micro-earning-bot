import unittest,tempfile,json
from pathlib import Path
from tracker import update
class TrackerTests(unittest.TestCase):
 def test_update_and_gate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'tracker.json';p.write_text('[{"customer":"Test","status":"sent"}]')
   with self.assertRaises(ValueError):update(p,'Test','paid')
   update(p,'Test','replied','Reply received');self.assertEqual(json.loads(p.read_text())[0]['status'],'replied')
 def test_unknown(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'tracker.json';p.write_text('[]')
   with self.assertRaises(ValueError):update(p,'Missing','sent')
