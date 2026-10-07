"""Read-only aggregate crown ownership, with safe empty subsets."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a):raise ValueError(a)
out=ROOT/'Exports'/version
if out.exists():raise RuntimeError('Fresh probe required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
cu=bpy.data.objects['Bystedt layercut derivative • native root reflow'].data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());p=p.reshape(-1,65,3)
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
back=np.empty(len(cu.curves),bool);cu.attributes['native_back_resection'].data.foreach_get('value',back)
height=p[:,:,2].max(axis=1);peak=p[:,:,2].argmax(axis=1)
def quant(x):return np.quantile(x,[0,.1,.5,.9,1]).tolist() if len(x) else []
records=[]
for name,selection in [('frontal',front>=0),('nonfrontal_posterior_edited',(front<0)&back),('nonfrontal_untouched',(front<0)&~back)]:
 rows=[]
 for threshold in [1.865,1.875,1.878,1.880,1.882]:
  m=selection&(height>threshold);idx=peak[m]
  rows.append(dict(threshold_z_m=threshold,shafts=int(m.sum()),peak_fraction_quantiles=quant(idx/64),root_y_quantiles_m=quant(p[m,0,1]),peak_in_first_four=int((idx<4).sum())))
 records.append(dict(selection=name,shafts=int(selection.sum()),peak_z_quantiles_m=quant(height[selection]),records=rows))
group=np.load(ROOT/'Exports'/probe/'local_flow_groups.npz');ids=group['ids'];labels=group['labels'];assert np.array_equal(ids,np.flatnonzero(front<0))
groups=[]
for g in np.unique(labels):
 m=ids[labels==g];q=p[m];h=height[m];pk=peak[m]
 if (h>1.875).sum()<20:continue
 groups.append(dict(group=int(g),shafts=len(m),above_1875=int((h>1.875).sum()),previously_edited=int(back[m].sum()),root_mean_m=q[:,0].mean(axis=0).tolist(),tip_mean_m=q[:,-1].mean(axis=0).tolist(),peak_mean_m=q[np.arange(len(q)),pk].mean(axis=0).tolist(),peak_fraction_quantiles=quant(pk/64)))
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
summary=dict(source=base,source_sha256=digest,source_unchanged=True,records=records,high_nonfrontal_families=groups,scope='Geometric ownership and aggregate peaks, not visibility or art acceptance; no raw geometry/indices.')
out.mkdir(parents=True);(out/'ownership_probe.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('CROWN_OWNERSHIP',json.dumps(summary),flush=True)
