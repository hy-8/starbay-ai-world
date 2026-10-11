"""Release measured near-identical posterior tips using their own shaft spread."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
target_median=float(a[a.index('--target-median')+1]) if '--target-median' in a else None
stagger='--stagger-tips' in a
save='--save' in a;save_only='--save-only' in a
assert not save_only or save
assert target_median is None or 0<target_median<=.004
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:3])
out=ARCHIVE/'Renders'/version;assert not out.exists()
modeldir=ARCHIVE/'Exports'/version
if save:assert not modeldir.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
sel=ARCHIVE/'Renders'/selection;meta=json.loads((sel/'edit_id_manifest.json').read_text());assert meta['source_sha256']==before
ids=np.load(sel/'local_projected_indices.npz')['selected']
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 flags=np.empty(len(sizes),bool);cu.attributes[key].data.foreach_get('value',flags);assert not flags[ids].any()
tip=old[off[ids+1]-1];keys=np.round(tip/.000010).astype(np.int64)
unique,labels,counts=np.unique(keys,axis=0,return_inverse=True,return_counts=True)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
groups=[];edited=[];scales=[];cuts=[]
for group in np.flatnonzero(counts>=40):
 members=ids[labels==group];paths=[];arcs=[];samples=[]
 for i in members:
  q=old[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
  paths.append(q);arcs.append(arc);samples.append([np.interp(.75*arc[-1],arc,q[:,axis]) for axis in range(3)])
 samples=np.array(samples);center=samples.mean(0);end=tip[labels==group].mean(0)
 tangent=end-center;tangent/=max(np.linalg.norm(tangent),1e-10)
 spread=samples-center;spread-=np.outer(spread@tangent,tangent)
 if target_median:spread*=target_median/max(np.median(np.linalg.norm(spread,axis=1)),1e-8)
 spread*=np.minimum(1,.008/np.maximum(np.linalg.norm(spread,axis=1),1e-10))[:,None]
 for i,q,arc,target in zip(members,paths,arcs,spread):
  t=arc/max(arc[-1],1e-8);delta=smooth((t-.60)/.40)[:,None]*target
  if stagger:
   # Only this short upper-layer shared-tip cluster: stagger its endpoints
   # on the existing path; preserve the first 60% rather than pruning the cut.
   fraction=((int(i)*2654435761)%4294967296)/4294967296
   cut=min(.002+.014*fraction,.20*arc[-1])
   mapped=arc-cut*smooth((t-.60)/.40)
   assert np.all(np.diff(mapped)>=0)
   shifted=np.column_stack([np.interp(mapped,arc,q[:,axis]) for axis in range(3)])
   delta=shifted-q+delta;cuts.append(cut)
  delta[arc<=.008]=0
  qs=np.vstack([q,(q[:-1]+q[1:])*.5]);ds=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(ds,axis=1)>1e-7
  qs=qs[moving];ds=ds[moving];limits=[min(.0003,gap(v))-1e-6 for v in qs];scale=1.
  for attempt in range(7):
   if all(gap(v+d*scale)>=g for v,d,g in zip(qs,ds,limits)):break
   scale*=.5
  else:scale=0.
  p[off[i]:off[i+1]]=q+delta*scale;edited.append(int(i));scales.append(scale)
 groups.append(dict(fibers=len(members),original_tip_xyz_m=end.tolist(),original_tip_spread_m=float(np.linalg.norm(tip[labels==group]-end,axis=1).max()),target_tip_spread_m_quantiles=np.quantile(np.linalg.norm(spread,axis=1),[0,.5,1]).tolist()))
assert len(edited)>0 and np.isfinite(p).all() and np.array_equal(p[off[:-1]],old[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
out.mkdir(parents=True);np.savez_compressed(out/'local_released_indices.npz',selected=np.array(edited))
modelhash=None
if save:
 assert 'native_released_tip_clusters' not in cu.attributes
 mask=np.zeros(len(sizes),bool);mask[edited]=True
 cu.attributes.new('native_released_tip_clusters','BOOLEAN','CURVE').data.foreach_set('value',mask)
 modeldir.mkdir(parents=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=digest(modeldir/'Ember_Regent.blend')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']:
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
report=dict(source=base,source_sha256=before,source_unchanged=True,selection=selection,model_saved=False,selected_fibers=len(edited),groups=groups,scale_quantiles=np.quantile(scales,[0,.5,1]).tolist(),max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),images_sha256=images,method='Group inspected fibers by original tips quantized10microns;only groups>=40. Take each own75percent-arc offset from group mean,project perpendicular to mean terminal direction,cap8mm. Add that offset with smooth60..100percent arc ramp;retain original first60percent and root8mm. Whole-curve sampled body-gap backtracking. Counts/radii/all other strands untouched;tips intentionally separate. Static preview,not continuous collision or art acceptance.')
report['target_median_before_cap_m']=target_median
if stagger:
 report.update(stagger_tips=True,requested_local_cut_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist())
 report['method']+=' Only selected shared-tip cluster: remap final40percent along original arc with smooth2..16mm endpoint staggering capped20percent of original arc; first60percent and root8mm exact. Stable strand-ID hash chooses cut, radii/counts retained. Whole-curve body guard may reduce requested cut. Outer lower-layer haircut untouched.'
if target_median:report['method']+=' Before8mm cap,scale projected measured spread to the requested median radius;no added random direction.'
(out/'tip_release_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if save:
 report.update(model_saved=True,model_sha256=modelhash,model_path=str(modeldir/'Ember_Regent.blend'))
 text=json.dumps(report,indent=2)
 (modeldir/'tip_release_manifest.json').write_text(text,encoding='utf-8')
 (out/'tip_release_manifest.json').write_text(text,encoding='utf-8')
print('TIP_RELEASE_PREVIEW_FINISHED',version,len(edited),flush=True)
