"""Zero-cost discovery and evidence-report pipeline. No credentials or write APIs."""
from discovery import scan
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

API = 'https://api.moltjobs.io/v1'
ROOT = Path(__file__).resolve().parent
TARGET = 'eb942e1f-1067-46d1-b1a5-0db0e23f41e1'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirect blocked; source URL must be reviewed')

class Reader:
    def __init__(self):
        self.opener = build_opener(NoRedirect())
    def get(self, url):
        p = urlsplit(url)
        allowed = {'api.moltjobs.io', 'www.blackrock.com', 'www.simcorp.com', 'www.boosted.ai', 'jobbi.org', 'api.github.com'}
        if p.scheme != 'https' or p.hostname not in allowed or p.port not in (None, 443) or p.username or p.password:
            raise ValueError('URL outside read-only allowlist')
        if p.hostname == 'api.moltjobs.io' and not (p.path in ('/v1/jobs', '/v1/stats', '/v1/evals/packs') or re.fullmatch(r'/v1/jobs/[0-9a-f-]{36}/public', p.path)):
            raise ValueError('Endpoint not allowed')
        if p.hostname == 'jobbi.org' and p.path != '/gigs.json':
            raise ValueError('Index endpoint not allowed')
        if p.hostname == 'api.github.com' and not re.fullmatch(r'/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*',p.path):
            raise ValueError('GitHub endpoint not allowed')
        for attempt in range(3):
            try:
                with self.opener.open(Request(url, headers={'User-Agent':'MicroEarningBot/0.1 (read-only research; no bidding)'}), timeout=20) as r:
                    b = r.read(2_000_001)
                    if len(b) > 2_000_000: raise ValueError('Response too large')
                    return b
            except HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == 2: raise
                try: delay = float(e.headers.get('Retry-After', 2 ** attempt))
                except ValueError: delay = 2 ** attempt
                if delay > 15: raise RuntimeError('Retry postponed to next scheduled run') from e
                time.sleep(max(0, delay))
    def json(self, path, **params):
        suffix = '?' + urlencode(params) if params else ''
        return json.loads(self.get(API + path + suffix))

def discover(reader):
    jobs, seen, cursor = [], set(), None
    for page in range(10):
        params = {'status':'OPEN','limit':100}
        if cursor: params['cursor'] = cursor
        payload = reader.json('/jobs', **params)
        data = payload.get('data')
        if not isinstance(data, list): raise ValueError('Unexpected job response')
        for j in data:
            if not isinstance(j,dict) or not j.get('id'): raise ValueError('Invalid job record')
            if j['id'] not in seen:
                seen.add(j['id']); jobs.append(j)
        meta = payload.get('meta') or payload.get('pagination') or {}
        nxt = meta.get('nextCursor') or payload.get('nextCursor')
        if not nxt:
            if len(data) >= 100: raise ValueError('Full page without cursor: completeness unknown')
            return jobs
        if nxt == cursor: raise ValueError('Repeated pagination cursor')
        cursor = nxt
    raise ValueError('Pagination limit reached; scan incomplete')

def assess(j, now=None):
    now = now or datetime.now(timezone.utc)
    reasons = []
    try:
        amount = Decimal(str(j.get('budgetUsdc')))
        if not amount.is_finite() or amount <= 0: raise InvalidOperation
    except (InvalidOperation, TypeError):
        reasons.append('Invalid budget')
    if j.get('status') != 'OPEN': reasons.append('Not open')
    try:
        if datetime.fromisoformat(str(j.get('deadlineAt') or '').replace('Z','+00:00')) <= now: reasons.append('Expired')
    except (KeyError,ValueError,TypeError): reasons.append('Deadline unverified')
    if j.get('purpose') != 'MARKETPLACE': reasons.append('Not independent marketplace work')
    text = (str(j.get('title','')) + ' ' + str(j.get('inputData',''))).lower()
    suitable = any(x in text for x in ('research','software','code','analysis','landing page'))
    if not suitable: reasons.append('Outside initial skills')
    if j.get('funded') is not True or not j.get('escrowTxHash'): reasons.append('Escrow unverified')
    if not j.get('acceptanceCriteria'): reasons.append('Acceptance criteria missing')
    if j.get('requiredPackId'): reasons.append('Certification eligibility unverified')
    return {'id':j['id'], 'title':j.get('title'), 'budgetUsdc':j.get('budgetUsdc'),
            'url':'https://moltjobs.io/open-jobs/'+j['id'], 'candidate':suitable,
            'state':'REVIEW_REQUIRED' if not reasons else 'HOLD', 'reasons':reasons,
            'payment_verified':False, 'approval_required':True}

def digest(b): return hashlib.sha256(b).hexdigest()

def research(reader, out):
    """Bounded source refresh plus deterministic draft, no paid LLM calls."""
    seed = json.loads((ROOT/'data/sources.json').read_text())
    rows, evidence = [], []
    for s in seed:
        try:
            raw = reader.get(s['url'])
            (out/(s['id']+'.html')).write_bytes(raw)
            clean = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', raw.decode('utf-8','replace'), flags=re.S|re.I)
            clean = unescape(re.sub('<[^>]+>', ' ', clean))
            clean = re.sub(r'\s+', ' ', clean)
            terms = s['terms']
            matched = [w for w in terms if w.lower() in clean.lower()]
            evidence.append({'id':s['id'],'url':s['url'],'status':'fetched','sha256':digest(raw),'terms_found':matched,
                             'checked_at':datetime.now(timezone.utc).isoformat()})
            status = 'Page fetched; manual claim review required' if matched else 'No expected terms found; review required'
        except Exception as e:
            evidence.append({'id':s['id'],'url':s['url'],'status':'error','error':type(e).__name__})
            status = 'Refresh unavailable; reviewed seed only'
        rows.append(f"| {s['vendor']} | {s['segment']} | {s['claim']} [{s['id']}]({s['url']}) | {status} |")
    template = (ROOT/'data/report.md').read_text()
    report = template.replace('{{ROWS}}','\n'.join(rows)).replace('{{DATE}}',datetime.now(timezone.utc).isoformat())
    (out/'test-research-report.md').write_text(report)
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2))
    return {'draft_generated':True,'sources_fetched':sum(e['status']=='fetched' for e in evidence),
            'source_count':len(evidence),'automated_claim_verification':False,'delivery_ready':False,
            'limitations':['Curated seed research; no autonomous open-web synthesis','Global coverage incomplete','Human factual and scope review required']}

def run(reader, out):
    out.mkdir(parents=True,exist_ok=True)
    jobs = discover(reader)
    shortlist = sorted((assess(j) for j in jobs),key=lambda j:(j['state']!='REVIEW_REQUIRED',not j['candidate']))
    (out/'opportunities.json').write_text(json.dumps({'asOf':datetime.now(timezone.utc).isoformat(),'jobs':shortlist},indent=2))
    (out/'jobs-snapshot.json').write_text(json.dumps(jobs,indent=2))
    try:
        external = scan(reader)
    except Exception as e:
        external = {'status':'error','error':type(e).__name__,'jobs':[], 'note':'Source unavailable; this does not mean zero jobs'}
    (out/'external-opportunities.json').write_text(json.dumps(external,indent=2))
    quality = research(reader,out)
    (out/'quality.json').write_text(json.dumps(quality,indent=2))
    files = [p for p in out.iterdir() if p.is_file() and p.name!='manifest.json']
    (out/'manifest.json').write_text(json.dumps({p.name:digest(p.read_bytes()) for p in sorted(files)},indent=2))
    print(json.dumps({'jobs':len(jobs),'candidates':sum(j['candidate'] for j in shortlist),'reviewable':sum(j['state']=='REVIEW_REQUIRED' for j in shortlist),'quality':quality},indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'output')
    args=parser.parse_args();run(Reader(),args.out)
