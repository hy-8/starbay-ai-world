import bpy,numpy as np,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'Exports/nativeframeprobe36'
if out.exists():raise RuntimeError('Fresh frame probe required')
source=ROOT/'Exports/nativepartunder26/Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
cu=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float)
g=np.load(ROOT/'Exports/nativeflowprobe30/local_flow_groups.npz');rows=[]
for label in np.unique(g['labels']):
 ids=g['ids'][g['labels']==label];old=raw[ids];center=old.mean(axis=0)
 if len(ids)<40 or center[0,1]<-.005 or center[-1,1]<.020:continue
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 normal=center-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9);across=np.cross(tangent,normal)
 wide=np.sum((old-center[None])*across[None],axis=2);width=float(np.median(np.quantile(wide,.95,axis=0)[16:49]-np.quantile(wide,.05,axis=0)[16:49]))
 if width<.010:continue
 dots=np.sum(across[1:]*across[:-1],axis=1);angles=np.rad2deg(np.arccos(np.clip(dots,-1,1)))
 trans=np.zeros_like(across);prev=across[0].copy()
 for j in range(65):
  prev-=tangent[j]*np.dot(prev,tangent[j]);prev/=max(np.linalg.norm(prev),1e-9);trans[j]=prev
 nd=np.sum(trans[1:]*trans[:-1],axis=1)
 rows.append(dict(group=int(label),source_flips=int((dots<0).sum()),source_turns_over60deg=int((angles>60).sum()),source_max_angle_deg=float(angles.max()),transport_flips=int((nd<0).sum()),transport_max_angle_deg=float(np.rad2deg(np.arccos(np.clip(nd,-1,1))).max())))
summary=dict(source='nativepartunder26',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),families=len(rows),source_frame_flips=sum(r['source_flips'] for r in rows),source_turns_over60deg=sum(r['source_turns_over60deg'] for r in rows),transport_frame_flips=sum(r['transport_flips'] for r in rows),records=rows,scope='Frame smoothness probe only; not art or segment collision acceptance')
out.mkdir(parents=True);(out/'frame_probe.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('FRAME_PROBE',json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)
