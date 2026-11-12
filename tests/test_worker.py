import json,tempfile,unittest
from pathlib import Path
from worker import prepare,package
class Tests(unittest.TestCase):
 def job(self):return dict(id='1',title='Research sample',url='https://example.com/job',scope='Compare two products',acceptance_criteria=['Sources for each claim'],ai_allowed=True,payment_verified=True,upfront_cost=0)
 def test_unverified_rejected(self):
  j=self.job();j['payment_verified']=False
  with self.assertRaises(ValueError):prepare(j,Path('/unused'))
 def test_cost_rejected(self):
  j=self.job();j['upfront_cost']=1
  with self.assertRaises(ValueError):prepare(j,Path('/unused'))
 def test_package_requires_review(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t)/'work';prepare(self.job(),w);(w/'deliverable/report.md').write_text('Draft')
   with self.assertRaises(ValueError):package(w)
 def test_manifest_bound_to_contents(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t)/'work';j=self.job();prepare(j,w);f=w/'deliverable/report.md';f.write_text('Draft')
   (w/'review.json').write_text(json.dumps(dict(criteria=j['acceptance_criteria'],all_passed=True,evidence='Human-reviewed source checklist')))
   a=package(w);f.write_text('Changed');b=package(w)
   self.assertNotEqual(a['files'],b['files']);self.assertFalse(b['submitted'])
if __name__=='__main__':unittest.main()
