import json,collections,re,sys
sys.path.insert(0,'.')
from reduce_all import signature
c=collections.Counter(); ex={}
seen=set()
skip=set(sys.argv[1:])
for l in open('data/rows-FULL.jsonl'):
    r=json.loads(l)
    k=(r['file'],r['rel'],r['vid'])
    if k in seen: continue
    seen.add(k)
    c[(r['rel'],'rows')]+=1
    if r.get('invalid'): c[(r['rel'],'invalid')]+=1; print("INVALID",r['file'],r['vid'],r['errors'] if 'errors' in r else '')
    if r.get('violation') and r['rel'] not in skip:
        s=signature(r); c[s]+=1; ex.setdefault(s,(r['file'].split('/')[-1],r['vid']))
for k,v in sorted(c.items(),key=str): print(v,k,ex.get(k,''))
