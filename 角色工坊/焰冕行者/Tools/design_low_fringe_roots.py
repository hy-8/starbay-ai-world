"""Original guide experiment: separate brow growth from overlying crown growth.

Trims the guide's upper path; the actual root is attached to the body by the
authoring tool. Does not use image projection or read licensed hair geometry.
"""
import json,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
folder=root/'Source/HairReconstruction'
target=folder/sys.argv[1]
if target.exists() or target.parent!=folder or target.suffix!='.json':raise RuntimeError('Fresh original JSON required')
records=json.loads((folder/'concert_fringe_control14.json').read_text(encoding='utf-8'))
rng=np.random.default_rng(100446)
result=[]
for record in records:
 p=np.array(record['control_points_m'],float);u=np.linspace(0,1,len(p));name=record['name']
 if 'segmented crown' not in name:
  # Remove the long upper ribbon of brow/temple locks. Let the independently
  # authored short crown govern the crown instead of burying it under bangs.
  start=rng.uniform(.17,.25) if 'forehead' in name else rng.uniform(.10,.18)
  q=np.linspace(start,1,9)
  p=np.stack([np.interp(q,u,p[:,j]) for j in range(3)],axis=1)
  name+=' / lower scalp origin'
 else:
  # Lower the barrel-like rise slightly, retaining independent lateral tips.
  p[:,2]-=.0035*np.sin(np.pi*u)**1.3
  name+=' / reduced crown lift'
 result.append({'name':name,'control_points_m':np.round(p,6).tolist()})
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('LOWER_FRINGE_DESIGN',len(result),str(target))
