import json
import unittest
from datetime import datetime,timezone
from unittest.mock import Mock
from discovery import issue_path,screen,scan
NOW=datetime(2026,11,10,tzinfo=timezone.utc)
class DiscoveryTests(unittest.TestCase):
 def item(self,**kw):
  d={'id':'algora:1','title':'Python bug fix','url':'https://github.com/test/project/issues/1','date_published':'2026-11-01T00:00:00Z','_jobbi':{'source':'algora','lane':'agent','claims_open':True,'reward':{'amount':25,'currency':'USD'},'payment_state':'escrowed'}};d.update(kw);return d
 def feed(self,items):return {'items':items,'_jobbi':{'generated':'2026-11-09T23:00:00Z'}}
 def test_no_index_payment_trust(self):
  r=screen(self.item(),NOW);self.assertFalse(r['payment_verified']);self.assertEqual(r['state'],'HOLD');self.assertTrue(r['candidate'])
 def test_stale_original_date(self):self.assertFalse(screen(self.item(date_published='2024-01-01T00:00:00Z'),NOW)['candidate'])
 def test_index_refresh_does_not_renew_job(self):
  i=self.item(date_published='2024-01-01T00:00:00Z',date_modified='2026-11-10T00:00:00Z');self.assertFalse(screen(i,NOW)['candidate'])
 def test_unknown_price(self):
  i=self.item();i['_jobbi']['reward']['amount']=None;self.assertFalse(screen(i,NOW)['candidate'])
 def test_bond(self):
  i=self.item();i['_jobbi']['extra']={'claim_bond_usdc':1};self.assertFalse(screen(i,NOW)['candidate'])
 def test_closed_original(self):
  r=Mock();r.get.side_effect=[json.dumps(self.feed([self.item()])),json.dumps({'html_url':self.item()['url'],'state':'closed'})]
  x=scan(r,NOW);self.assertEqual(x['candidates'],0);self.assertEqual(x['originals_checked'],1)
 def test_bad_feed_fails(self):
  r=Mock();r.get.return_value='{}'
  with self.assertRaises(ValueError):scan(r,NOW)
 def test_stale_feed_fails(self):
  r=Mock();d=self.feed([]);d['_jobbi']['generated']='2020-01-01T00:00:00Z';r.get.return_value=json.dumps(d)
  with self.assertRaises(ValueError):scan(r,NOW)
 def test_no_arbitrary_fetch(self):
  i=self.item(url='https://evil.example/steal');r=Mock();r.get.return_value=json.dumps(self.feed([i]));scan(r,NOW);self.assertEqual(r.get.call_count,1)
 def test_duplicate(self):
  r=Mock();r.get.side_effect=[json.dumps(self.feed([self.item(),self.item()])),json.dumps({'html_url':self.item()['url'],'state':'open'})];self.assertEqual(scan(r,NOW)['records'],1)
 def test_paths(self):
  self.assertEqual(issue_path('https://github.com/a/b/issues/1'),'/repos/a/b/issues/1')
  for u in ['http://github.com/a/b/issues/1','https://github.com.evil/a/b/issues/1','https://github.com/a/b/issues/1?redirect=evil','https://github.com/a/b/pulls/1']:
   self.assertIsNone(issue_path(u))
