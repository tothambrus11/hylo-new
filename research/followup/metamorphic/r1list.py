import json,collections,sys
cfg=sys.argv[1] if len(sys.argv)>1 else 'FULL'
by=collections.defaultdict(lambda: collections.Counter()); errs={}; base={}
seen=set()
for l in open('data/rows-%s.jsonl'%cfg):
    r=json.loads(l)
    if r['rel']!='r1': continue
    k=(r['file'],r['vid'])
    if k in seen: continue
    seen.add(k)
    f=r['file']
    by[f][r['verdict']]+=1; base[f]=r['base_verdict']
    if r.get('violation'): errs.setdefault(f,set()).update((r.get('errors',[]) if r['verdict']!='accept' else r.get('base_errors',[]))[:3])
n=0
for f,c in sorted(by.items()):
    if len(c)>1 or list(c)[0]!=base[f]:
        n+=1; print(f.split('/')[-1],'orig:',base[f],dict(c),sorted(errs.get(f,[]))[:3])
print(len(by),"programs,",n,"order-dependent,",len(seen),"variants")
