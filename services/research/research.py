"""Free, read-only arXiv research pack builder; all outputs need owner review."""
import argparse,csv,hashlib,json,re,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone,date
NS={'a':'http://www.w3.org/2005/Atom'}
FIELDS=['source','title','authors','date','summary','evidence_quote','review_status']
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): raise ValueError('Redirect refused')
def fetch(query,count):
 if not 1<=count<=50 or not query.strip() or len(query)>500: raise ValueError('Invalid query/count')
 url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode(dict(search_query=query,start=0,max_results=count,sortBy='submittedDate',sortOrder='descending'))
 req=urllib.request.Request(url,headers={'User-Agent':'MicroEarningBotResearch/0.1 read-only pilot'})
 with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as r: data=r.read(2000001)
 if len(data)>2000000: raise ValueError('Oversized feed')
 return data,url
def parse(data):
 if len(data)>2000000 or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): raise ValueError('Unsafe XML')
 root=ET.fromstring(data)
 if root.tag!='{http://www.w3.org/2005/Atom}feed':raise ValueError('Expected Atom')
 rows=[];seen=set();duplicates=0
 for e in root.findall('a:entry',NS):
  def val(t):return ' '.join(e.findtext('a:'+t,'',NS).split())
  u=urllib.parse.urlsplit(val('id'))
  if u.hostname!='arxiv.org' or not re.fullmatch(r'/abs/(?:\d{4}\.\d{4,5}|[a-zA-Z.-]+/\d{7})(?:v\d+)?',u.path):raise ValueError('Invalid paper source')
  source='https://arxiv.org'+u.path;key=re.sub(r'v\d+$','',source)
  if key in seen:duplicates+=1;continue
  seen.add(key);quote=' '.join(val('summary').split()[:20])
  rows.append(dict(source=source,title=val('title'),authors='; '.join(' '.join(a.findtext('a:name','',NS).split()) for a in e.findall('a:author',NS)),date=val('published')[:10],summary='Abstract excerpt: '+quote,evidence_quote=quote,review_status='NEEDS_HUMAN_REVIEW'))
 return rows,duplicates
def quality(rows,expected):
 errors=[];seen=set()
 if len(rows)!=expected:errors.append('Incorrect unique paper count')
 for i,r in enumerate(rows):
  for k in FIELDS:
   if not r.get(k):errors.append(f'Row {i+1}: missing {k}')
  try:date.fromisoformat(r['date'])
  except (ValueError,KeyError):errors.append('Invalid date')
  if r.get('source') in seen:errors.append('Duplicate source')
  seen.add(r.get('source'))
  if r.get('evidence_quote') and r['evidence_quote'] not in r.get('summary',''):errors.append('Unsupported summary')
 return dict(structural_pass=not errors,errors=errors,rows=len(rows),factual_verification=False,delivery_ready=False,owner_approval_required=True)
def safe_cell(s):return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
def build(data,out,expected,provenance):
 rows,n=parse(data);q=quality(rows,expected);q['duplicates_removed']=n
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 with (out/'papers.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows({k:safe_cell(v) for k,v in r.items()} for r in rows)
 (out/'quality.json').write_text(json.dumps(q,indent=2))
 (out/'provenance.json').write_text(json.dumps(dict(retrieved_at=datetime.now(timezone.utc).isoformat(),source=provenance,feed_sha256=hashlib.sha256(data).hexdigest(),method='arXiv Atom, first 20 abstract words; no paid model',submitted=False),indent=2))
 report='# AI research dataset — internal pilot\n\n'+f'{len(rows)} unique papers. Structural checks: {q["structural_pass"]}.\n\n'
 report+='Attributed abstract excerpts only, not independently verified summaries or key findings. No full papers reviewed. Human synthesis, relevance and client criteria checks remain required. Not delivery-ready. No earnings claimed.\n\nThank you to arXiv for use of its open access interoperability.\n\n'
 report+='\n'.join(f'{i}. {r["title"]} ({r["date"]}) — {r["source"]}\n   Evidence: {r["evidence_quote"]}' for i,r in enumerate(rows,1))
 (out/'report.md').write_text(report);return q
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--query',default='cat:cs.AI');p.add_argument('--count',type=int,default=20);p.add_argument('--feed',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 data,url=(a.feed.read_bytes(),'owner-supplied Atom') if a.feed else fetch(a.query,a.count)
 q=build(data,a.out,a.count,url);print(json.dumps(q));raise SystemExit(0 if q['structural_pass'] else 1)
