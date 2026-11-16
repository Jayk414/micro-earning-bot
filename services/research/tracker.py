"""Private local proposal tracker. No email or payment actions."""
import argparse,json
from pathlib import Path
STATES=['sent','replied','scope_agreed','in_progress','owner_review','delivered','paid','declined']
def update(path,name,status,note=''):
 if status not in STATES:raise ValueError('Invalid status')
 p=Path(path);data=json.loads(p.read_text());matches=[r for r in data if r['customer']==name]
 if len(matches)!=1:raise ValueError('Customer must match exactly one entry')
 r=matches[0]
 if status in ['scope_agreed','in_progress','owner_review','delivered','paid'] and not note.strip():raise ValueError('Record scope/approval/payment evidence in note')
 r['status']=status;r['note']=note
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(p)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');p.add_argument('customer');p.add_argument('status',choices=STATES);p.add_argument('--note',default='');a=p.parse_args();update(a.file,a.customer,a.status,a.note)
