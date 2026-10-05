"""Approximate point-depth crown attribution, actual camera and saved shafts."""
import bpy,json,sys,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version
if out.exists():raise RuntimeError('Fresh visibility probe')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/base/'Ember_Regent.blend'),use_scripts=False)
camera=bpy.data.objects['03_Side'];M=np.array(camera.matrix_world.inverted());proj=np.array(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=960,y=1120,scale_x=1,scale_y=1))
# Opposite side using reflected world and local handedness correction.
ref=np.diag([-1,1,1,1]);M=ref@M@ref
objects=[];coords=[];owners=[];curveids=[]
for oid,ob in enumerate([o for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render]):
 data=ob.data;p=np.empty((len(data.points),3),np.float32);data.attributes['position'].data.foreach_get('vector',p.ravel())
 p=(np.c_[p,np.ones(len(p))]@np.array(ob.matrix_world).T)[:,:3]
 coords.append(p);owners.append(np.full(len(p),oid));curveids.append(np.repeat(np.arange(len(data.curves)),[c.points_length for c in data.curves]));objects.append(ob)
p=np.vstack(coords);oid=np.concatenate(owners);cid=np.concatenate(curveids)
local=np.c_[p,np.ones(len(p))]@M.T;clip=local@proj.T;ndc=clip[:,:3]/clip[:,3,None];depth=-local[:,2]
W,H=480,560;xx=np.floor((ndc[:,0]*.5+.5)*W).astype(int);yy=np.floor((ndc[:,1]*.5+.5)*H).astype(int)
valid=(xx>=0)&(xx<W)&(yy>=0)&(yy<H)&(depth>0)
indices=np.flatnonzero(valid);pixel=yy[indices]*W+xx[indices];z=np.full(W*H,np.inf);np.minimum.at(z,pixel,depth[indices])
visible=indices[depth[indices]<z[pixel]+.0007]
# Actual upper/back crown region; no face/bottom fibers.
crown=visible[(p[visible,2]>1.810)&(p[visible,1]>-.012)]
records=[]
for index,ob in enumerate(objects):
 ids=np.unique(cid[crown[oid[crown]==index]])
 cu=ob.data;pp=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',pp.ravel())
 starts=np.array([c.first_point_index for c in cu.curves]);roots=pp[starts[ids]];tips=pp[(starts+np.array([c.points_length for c in cu.curves])-1)[ids]]
 records.append(dict(object=ob.name,visible_crown_shafts=len(ids),root_xyz_quantiles_m=np.quantile(roots,[0,.25,.5,.75,1],axis=0).tolist() if len(ids) else [],tip_xyz_quantiles_m=np.quantile(tips,[0,.25,.5,.75,1],axis=0).tolist() if len(ids) else []))
out.mkdir(parents=True)
(out/'visible_crown_probe.json').write_text(json.dumps(dict(source=base,method='480x560 point depth, .7mm tolerance; actual opposite camera, crown z>1.810/y>-.012',records=records,scope='Approximate point attribution, not continuous-ray occlusion or artistic proof'),indent=2),encoding='utf-8')
np.savez_compressed(out/'local_visible_crown_indices.npz',**{str(i):np.unique(cid[crown[oid[crown]==i]]) for i in range(len(objects))})
print('VISIBLE_CROWN_PROBE',records,flush=True)
