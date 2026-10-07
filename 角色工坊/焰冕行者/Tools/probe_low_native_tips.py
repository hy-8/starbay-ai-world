"""Read-only aggregate diagnosis of long-tail cut omissions; indices stay local."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3)
edited=np.empty(len(raw),bool);cu.attributes['native_nape_layer_cut'].data.foreach_get('value',edited)
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
rows=[]
for label,mask in [('all_primary',np.ones(len(raw),bool)),('uncut_long_tips',(raw[:,-1,2]<1.665)&(~edited)),('cut_long_tips',(raw[:,-1,2]<1.665)&edited)]:
 z=raw[mask];r=dict(subset=label,fibers=int(mask.sum()))
 if len(z):
  r.update(root_xyz_quantiles_m=np.quantile(z[:,0],[0,.1,.5,.9,1],axis=0).tolist(),point_index3_z_quantiles_m=np.quantile(z[:,3,2],[0,.1,.5,.9,1]).tolist(),point_index11_z_quantiles_m=np.quantile(z[:,11,2],[0,.1,.5,.9,1]).tolist(),tip_xyz_quantiles_m=np.quantile(z[:,-1],[0,.1,.5,.9,1],axis=0).tolist(),in_new_front_frame=int(frame[mask].sum()),roots_below_1_710m=int((z[:,0,2]<1.710).sum()))
 rows.append(r)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
out.mkdir(parents=True);(out/'low_tip_probe.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,point_index_convention='Zero based: index3 is fourth point; index11 is twelfth point',records=rows,scope='Geometric aggregates only, no visibility or collision guarantee'),indent=2),encoding='utf-8')
print('LOW_TIP_PROBE',rows,flush=True)
