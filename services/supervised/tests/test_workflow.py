import unittest,tempfile,json
from pathlib import Path
from workflow import prepare,approve,run,package,manifest,read,write,bound
FEED=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2401.12345v1</id><title>Test</title><published>2024-01-01</published><summary>Test abstract.</summary><author><name>Test Author</name></author></entry></feed>'
def job():return dict(id='DEMO',title='Internal demo',url='https://example.invalid/demo',scope='One paper metadata draft',price='0 internal test',deadline='Internal only',query='cat:cs.AI',count=1,criteria=['Source checked'],upfront_cost=0,payment_verified=True,payment_verified_evidence='SIMULATED TEST ONLY',ai_allowed=True,ai_allowed_evidence='SIMULATED',uk_eligible=True,uk_eligible_evidence='SIMULATED')
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.w=Path(self.t.name)/'work';prepare(job(),self.w);self.f=Path(self.t.name)/'feed.xml';self.f.write_bytes(FEED)
 def tearDown(self):self.t.cleanup()
 def ready(self):
  approve(self.w,'application','SIMULATED TEST APPROVAL');write(self.w/'assignment.json',dict(scope_hash=bound(self.w)['scope_hash'],acceptance_reference='SIMULATED CLIENT ACCEPTANCE'));run(self.w,self.f)
 def review(self):write(self.w/'review.json',dict(criteria=job()['criteria'],all_passed=True,factual_review_evidence='SIMULATED TEST REVIEW',files=manifest(self.w)))
 def test_no_approval(self):
  with self.assertRaises(FileNotFoundError):run(self.w,self.f)
 def test_no_assignment(self):
  approve(self.w,'application','TEST')
  with self.assertRaises(FileNotFoundError):run(self.w,self.f)
 def test_scope_change(self):
  approve(self.w,'application','TEST');(self.w/'application.txt').write_text('Changed')
  with self.assertRaises(ValueError):run(self.w,self.f)
 def test_end_to_end_and_stale_delivery(self):
  self.ready();self.review();approve(self.w,'delivery','SIMULATED OWNER DELIVERY APPROVAL');self.assertFalse(package(self.w)['submitted']);(self.w/'draft/report.md').write_text('Changed')
  with self.assertRaises(ValueError):package(self.w)
 def test_no_delivery_approval(self):
  self.ready();self.review()
  with self.assertRaises(FileNotFoundError):package(self.w)
 def test_no_factual_review(self):
  self.ready()
  with self.assertRaises(FileNotFoundError):approve(self.w,'delivery','TEST')
 def test_upfront_cost(self):
  j=job();j['upfront_cost']=1
  with self.assertRaises(ValueError):prepare(j,Path(self.t.name)/'other')
 def test_symlink(self):
  self.ready();(self.w/'draft/secret.txt').symlink_to(self.f)
  with self.assertRaises(ValueError):manifest(self.w)
