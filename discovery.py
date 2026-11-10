"""Read-only multi-board discovery. Index claims never establish payment."""
import json
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

FEED = 'https://jobbi.org/gigs.json?lane=agent&limit=1000'

def stamp(s):
    value = datetime.fromisoformat(str(s or '').replace('Z', '+00:00'))
    if value.tzinfo is None: raise ValueError('Timezone missing')
    return value

def issue_path(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'github.com' or p.port not in (None,443) or p.username or p.password or p.query or p.fragment:
        return None
    if not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*',p.path): return None
    return '/repos' + p.path

def screen(item, now):
    if not isinstance(item,dict) or not isinstance(item.get('_jobbi'),dict): raise ValueError('Invalid item')
    j=item['_jobbi']; reward=j.get('reward')
    if not isinstance(reward,dict) or not isinstance(item.get('id'),str): raise ValueError('Missing identity or reward')
    reasons=['Original listing terms, funding and payout eligibility require review']
    eligible=True
    if j.get('lane') not in ('agent','mixed') or j.get('claims_open') is not True:
        reasons.append('Not open to agents according to index');eligible=False
    try:
        amount=Decimal(str(reward.get('amount')))
        if not amount.is_finite() or amount<=0 or reward.get('currency') not in ('USD','USDC','GBP','EUR'):
            raise InvalidOperation
    except (InvalidOperation,TypeError): reasons.append('Positive supported reward unverified');eligible=False
    try:
        if stamp(item.get('date_published')) < now-timedelta(days=90):
            reasons.append('Published over 90 days ago; renewed availability needs confirmation');eligible=False
    except (ValueError,TypeError): reasons.append('Publication date unverified');eligible=False
    expires=j.get('expires')
    if expires:
        try:
            if stamp(expires)<=now: reasons.append('Expired');eligible=False
        except (ValueError,TypeError): reasons.append('Expiry malformed');eligible=False
    text=(str(item.get('title',''))+' '+str(item.get('content_text',''))+' '+str(item.get('tags',[]))).lower()
    if not any(t in text for t in ('python','research','documentation','test','typescript','bug','code','software')):
        reasons.append('Outside initial skills');eligible=False
    extra=j.get('extra') or {}
    if not isinstance(extra,dict):raise ValueError('Invalid extra metadata')
    if any(extra.get(k) not in (None,0,'0',False,'') for k in ('claim_bond_usdc','bond_usdc','entry_fee','fee_usdc')):
        reasons.append('Possible upfront fee or bond');eligible=False
    p=urlsplit(str(item.get('url','')))
    if p.scheme!='https' or not p.hostname or p.username or p.password:
        reasons.append('Unsafe listing URL');eligible=False
    return {'id':item['id'],'title':str(item.get('title',''))[:500], 'url':item.get('url'),
            'board':j.get('source_name') or j.get('source'),'discovered_via':'Jobbi',
            'index_payment_claim':j.get('payment_state'),'reward':reward,
            'candidate':eligible,'state':'HOLD','reasons':reasons,'original_checked':False,
            'payment_verified':False,'approval_required':True}

def scan(reader, now=None):
    now=now or datetime.now(timezone.utc)
    feed=json.loads(reader.get(FEED))
    if not isinstance(feed,dict) or not isinstance(feed.get('items'),list):raise ValueError('Unexpected feed')
    meta=feed.get('_jobbi')
    if not isinstance(meta,dict):raise ValueError('Missing index metadata')
    age=now-stamp(meta.get('generated'))
    if age>timedelta(hours=24) or age<timedelta(minutes=-5):raise ValueError('Stale or future feed timestamp')
    if len(feed['items'])>=1000:raise ValueError('Feed may be truncated')
    results=[];seen=set()
    for i in feed['items']:
        r=screen(i,now)
        if r['id'] not in seen:seen.add(r['id']);results.append(r)
    # Check at most four candidate GitHub issues. Never follow arbitrary listing URLs.
    checked=0
    for r in results:
        if not r['candidate'] or checked>=4:continue
        path=issue_path(str(r.get('url','')))
        if not path:continue
        checked+=1
        try:
            issue=json.loads(reader.get('https://api.github.com'+path))
            if not isinstance(issue,dict) or issue.get('html_url')!=r['url']:raise ValueError('Unexpected issue')
            r['original_checked']=True;r['original_state']=issue.get('state')
            if issue.get('state')!='open' or issue.get('pull_request'):
                r['candidate']=False;r['reasons'].append('Original issue is closed or is a pull request')
            if issue.get('assignees'):r['reasons'].append('Original issue already has assignees')
            r['reasons'].append('Repository AI policy, recent discussion and reward confirmation still need review')
        except Exception as e:r['original_error']=type(e).__name__
    return {'status':'ok','index':'https://jobbi.org','generated':meta['generated'],
            'scope':'Up to 1000 agent-lane records; not all global paid work',
            'records':len(results),'candidates':sum(r['candidate'] for r in results),
            'originals_checked':sum(r['original_checked'] for r in results),'jobs':results}
