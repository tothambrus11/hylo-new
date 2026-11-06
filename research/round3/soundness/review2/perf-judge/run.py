#!/usr/bin/env python3
# usage: run.py CONFIG file [--cap N] [--to S]
import sys, os, subprocess, time, resource, re
B='/home/user/hylo-new/research/exp/bin/eq2-e965a058dfd0/tc-bench'
FIX='occurs,fixsubst,eqsolve,extorder'
FULL=FIX+',symindex,coesrc,traitindex,memberskip,unify,index,absmodel,typevec'
args=sys.argv[1:]
cfg=args.pop(0); cfg={'base':'','fix':FIX,'full':FULL}.get(cfg,cfg)
env=dict(os.environ); env['HYLO_TC_EXPERIMENTS']=cfg
to=int(os.environ.get('TO','120'))
if 'CAP' in os.environ: env['HYLO_TC_MAXDEPTH']=os.environ['CAP']
t=time.time()
p=subprocess.run(['timeout',str(to),B,'--count']+args,env=env,capture_output=True,text=True)
w=time.time()-t
ru=resource.getrusage(resource.RUSAGE_CHILDREN)
out=p.stdout+p.stderr
keep=[]
for l in out.splitlines():
    if l.startswith('counters.user'):
        cs=dict(x.split('=') for x in l.split()[1:])
        keep.append(' '.join(f'{k}={v}' for k,v in cs.items() if k.startswith(('summon.matches','summon.subgoals','eqsolve','summon.depthEx','absmodel','index.','coerced'))))
    elif l.startswith(('diagnostics','type.user')) or 'error' in l:
        keep.append(l.strip()[:200])
print('\n'.join(keep[:8]))
print(f'exit={p.returncode} wall={w:.1f}s maxrss={ru.ru_maxrss//1024}MB')
