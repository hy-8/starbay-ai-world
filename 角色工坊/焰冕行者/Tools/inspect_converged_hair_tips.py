"""Aggregate-only source diagnosis of posterior tip convergence; no model edits."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ARCHIVE/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
cu=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
tips=p[off[1:]-1];mask&=(tips[:,1]>.030)&(p[off[:-1],1]>-.030)
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 flags=np.empty(len(mask),bool);cu.attributes[key].data.foreach_get('value',flags);mask&=~flags
ids=np.flatnonzero(mask);_,labels,counts=np.unique(np.round(tips[ids]/.000010).astype(np.int64),axis=0,return_inverse=True,return_counts=True)
groups=[]
for group in np.flatnonzero(counts>=40):
 selected=ids[labels==group];samples=[];lengths=[]
 for i in selected:
  q=p[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
  samples.append([np.interp(.75*arc[-1],arc,q[:,axis]) for axis in range(3)]);lengths.append(arc[-1])
 samples=np.array(samples);end=tips[selected].astype(float).mean(0)
 groups.append(dict(fibers=len(selected),tip_xyz_m=end.tolist(),tip_spread_max_m=float(np.linalg.norm(tips[selected]-end,axis=1).max()),shaft75_spread_m_quantiles=np.quantile(np.linalg.norm(samples-samples.mean(0),axis=1),[0,.5,1]).tolist(),original_arc_m_quantiles=np.quantile(lengths,[0,.5,1]).tolist(),root_mean_xyz_m=p[off[selected]].mean(0).tolist()))
groups.sort(key=lambda g:g['fibers'],reverse=True)
assert digest(source)==before
out.mkdir(parents=True)
(out/'convergence_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=before,source_unchanged=True,eligible_posterior_fibers=len(ids),converged_fibers=sum(g['fibers'] for g in groups),groups=groups,selection_rule='native_restored_raw_controls AND tipY>30mm AND rootY>-30mm;exclude accepted inner curtain/fringe sweeps/curved accent. Group tips quantized10microns,minimum40 fibers. No depth visibility claim.',geometry_modified=False,model_saved=False),indent=2),encoding='utf-8')
print('CONVERGENCE_DIAGNOSIS',len(ids),len(groups),sum(g['fibers'] for g in groups),flush=True)
