"""Supervised research orchestration. No application or delivery transport exists."""
import argparse,hashlib,json
from pathlib import Path
from research import fetch,build

def hash_bytes(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True))
def snapshot(w):
 paths=[w/'job.json',w/'application.txt']
 return hash_bytes(b''.join(p.name.encode()+b'\0'+p.read_bytes()+b'\0' for p in paths))
def bound(w):
 s=read(w/'state.json')
 if s['scope_hash']!=snapshot(w):raise ValueError('Scope/application changed; approval invalid')
 return s

def prepare(job,w):
 for k in ['id','title','url','scope','price','deadline','query']:
  if not isinstance(job.get(k),str) or not job[k].strip():raise ValueError('Missing '+k)
 if type(job.get('upfront_cost')) not in (int,float) or job['upfront_cost']!=0:raise ValueError('Zero upfront cost required')
 for k in ['payment_verified','ai_allowed','uk_eligible']:
  if job.get(k) is not True or not job.get(k+'_evidence'):raise ValueError('Evidence required: '+k)
 if not isinstance(job.get('criteria'),list) or not job['criteria'] or any(not isinstance(x,str) or not x.strip() for x in job['criteria']):raise ValueError('Criteria required')
 if type(job.get('count')) is not int or not 1<=job['count']<=50:raise ValueError('Count 1–50 required')
 w.mkdir(parents=True,exist_ok=False);write(w/'job.json',job)
 (w/'application.txt').write_text(f"APPLICATION DRAFT — NOT SENT\n{job['title']}\nScope: {job['scope']}\nPrice: {job['price']}\nDeadline: {job['deadline']}\nAI-assisted research with human factual review.\nCriteria: "+'; '.join(job['criteria']))
 write(w/'state.json',dict(stage='AWAITING_APPLICATION_APPROVAL',scope_hash=snapshot(w),submitted=False))

def approve(w,kind,reference):
 # Local operator attestation only; this cannot authenticate a ChatGPT owner.
 if not reference.strip():raise ValueError('Record the specific owner approval reference')
 s=bound(w)
 if kind=='application':target=s['scope_hash']
 elif kind=='delivery':
  target=package_hash(w)
  if not (w/'review.json').exists():raise ValueError('Review missing')
 else:raise ValueError('Unknown approval kind')
 write(w/(kind+'-approval.json'),dict(target_hash=target,owner_approval_reference=reference,attestation_only=True))

def require_approval(w,kind,target):
 a=read(w/(kind+'-approval.json'))
 if a.get('target_hash')!=target or not a.get('owner_approval_reference'):raise ValueError('Missing/stale specific approval')

def run(w,feed=None):
 s=bound(w);require_approval(w,'application',s['scope_hash']);j=read(w/'job.json')
 # Assignment is separate from permission to apply. No speculative client work.
 accepted=read(w/'assignment.json')
 if accepted.get('scope_hash')!=s['scope_hash'] or not accepted.get('acceptance_reference'):raise ValueError('Client acceptance of exact scope required')
 if (w/'draft').exists():raise ValueError('Draft already exists; create fresh workspace to rerun')
 if feed is None:data,url=fetch(j['query'],j['count'])
 else:data,url=Path(feed).read_bytes(),'supplied Atom feed (test/offline)'
 q=build(data,w/'draft',j['count'],url)
 s['stage']='NEEDS_FACTUAL_REVIEW';s['structural_pass']=q['structural_pass'];write(w/'state.json',s)
 return q

def manifest(w):
 root=w/'draft';files={}
 if root.is_symlink():raise ValueError('Unsafe root')
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError('Symlink refused')
  if p.is_file():
   if not p.resolve().is_relative_to(root.resolve()) or p.name.startswith('.env') or p.suffix in ['.pem','.key']:raise ValueError('Unsafe file')
   files[p.relative_to(root).as_posix()]=hash_bytes(p.read_bytes())
 if not files:raise ValueError('Empty package')
 return files

def package_hash(w):
 s=bound(w)
 if s.get('stage')!='NEEDS_FACTUAL_REVIEW' or not s.get('structural_pass'):raise ValueError('Successful research run required')
 require_approval(w,'application',s['scope_hash'])
 m=manifest(w);r=read(w/'review.json');j=read(w/'job.json')
 if r.get('criteria')!=j['criteria'] or r.get('all_passed') is not True or not r.get('factual_review_evidence'):raise ValueError('Exact criteria and factual evidence review required')
 if r.get('files')!=m:raise ValueError('Review stale; bind review to current file hashes')
 return hash_bytes(json.dumps(dict(scope=s['scope_hash'],files=m,review=r),sort_keys=True).encode())

def package(w):
 h=package_hash(w);require_approval(w,'delivery',h)
 result=dict(status='APPROVED_FOR_MANUAL_DELIVERY',files=manifest(w),package_hash=h,submitted=False,approval_is_operator_attestation=True)
 write(w/'delivery-manifest.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
 a=s.add_parser('prepare');a.add_argument('job',type=Path);a.add_argument('workspace',type=Path)
 a=s.add_parser('approve');a.add_argument('workspace',type=Path);a.add_argument('kind',choices=['application','delivery']);a.add_argument('--reference',required=True)
 a=s.add_parser('run');a.add_argument('workspace',type=Path);a.add_argument('--feed',type=Path)
 for command in ['manifest','package']:
  a=s.add_parser(command);a.add_argument('workspace',type=Path)
 a=p.parse_args()
 if a.cmd=='prepare':prepare(read(a.job),a.workspace)
 elif a.cmd=='approve':approve(a.workspace,a.kind,a.reference)
 elif a.cmd=='run':print(json.dumps(run(a.workspace,a.feed),indent=2))
 elif a.cmd=='manifest':print(json.dumps(manifest(a.workspace),indent=2))
 else:print(json.dumps(package(a.workspace),indent=2))
