import unittest
from datetime import datetime,timezone
from unittest.mock import Mock
from bot import Reader, assess, discover

class BotTests(unittest.TestCase):
 def job(self,**kw):
  d=dict(id='test',title='Research software',budgetUsdc='180',status='OPEN',purpose='MARKETPLACE',deadlineAt='2099-01-01T00:00:00Z',funded=True,escrowTxHash='0xabc',acceptanceCriteria='Report');d.update(kw);return d
 def test_unfunded_blocks(self):self.assertIn('Escrow unverified',assess(self.job(funded=False))['reasons'])
 def test_missing_hash_blocks(self):self.assertIn('Escrow unverified',assess(self.job(escrowTxHash=None))['reasons'])
 def test_missing_criteria_blocks(self):self.assertIn('Acceptance criteria missing',assess(self.job(acceptanceCriteria=None))['reasons'])
 def test_expired(self):self.assertIn('Expired',assess(self.job(deadlineAt='2020-01-01T00:00:00Z'))['reasons'])
 def test_null_deadline(self):self.assertIn('Deadline unverified',assess(self.job(deadlineAt=None))['reasons'])
 def test_naive_deadline(self):self.assertIn('Deadline unverified',assess(self.job(deadlineAt='2099-01-01'))['reasons'])
 def test_nan_budget(self):self.assertIn('Invalid budget',assess(self.job(budgetUsdc='NaN'))['reasons'])
 def test_review_is_not_payment_proof(self):
  a=assess(self.job());self.assertEqual(a['state'],'REVIEW_REQUIRED');self.assertFalse(a['payment_verified']);self.assertTrue(a['approval_required'])
 def test_no_write_endpoints(self):
  r=Reader()
  for u in ['https://api.moltjobs.io/v1/jobs/test/bids','http://api.moltjobs.io/v1/jobs','https://localhost/','https://api.moltjobs.io.evil.com/v1/jobs','https://api.moltjobs.io:8080/v1/jobs']:
   with self.assertRaises(ValueError):r.get(u)
 def test_pagination(self):
  r=Mock();r.json.side_effect=[{'data':[self.job()], 'meta':{'nextCursor':'next'}},{'data':[self.job(),self.job(id='two')]}]
  self.assertEqual(len(discover(r)),2);self.assertEqual(r.json.call_args.kwargs['cursor'],'next')
 def test_bad_shape(self):
  r=Mock();r.json.return_value={'data':{}}
  with self.assertRaises(ValueError):discover(r)
 def test_full_page_fails_closed(self):
  r=Mock();r.json.return_value={'data':[self.job(id=str(i)) for i in range(100)]}
  with self.assertRaises(ValueError):discover(r)

if __name__=='__main__':unittest.main()
