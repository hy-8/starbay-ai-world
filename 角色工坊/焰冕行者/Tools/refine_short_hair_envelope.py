"""Preview restrained crown-height and lateral-volume reduction on accepted groom."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
crown_mm=float(a[a.index('--crown-mm')+1]) if '--crown-mm' in a else 7.
side_mm=float(a[a.index('--side-mm')+1]) if '--side-mm' in a else 9.
include_released='--include-released' in a
surface_envelope='--surface-envelope' in a
save='--save' in a;save_only='--save-only' in a
assert 0<=crown_mm<=15 and 0<=side_mm<=25 and (not save_only or save)
modeldir=ARCHIVE/'Exports'/version
if save:assert not modeldir.exists()
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ARCHIVE/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];assert np.allclose(np.array(ob.matrix_world),np.eye(4))
cu=ob.data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
released=np.empty(len(sizes),bool);cu.attributes['native_released_tip_clusters'].data.foreach_get('value',released)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
stats=[]
for i in range(len(sizes)):
 if released[i] and not include_released:continue
 q=old[off[i]:off[i+1]].astype(float)
 if q[:,2].max()<1.735:continue
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 onset=smooth((arc-.008)/.025)
 crown=smooth((q[:,2]-1.835)/.040)
 side=smooth((np.abs(q[:,0])-.062)/.040)*smooth((q[:,2]-1.735)/.055)*(1-smooth((q[:,2]-1.835)/.040))*smooth((q[:,1]+.060)/.060)
 delta=np.column_stack([-side_mm*.001*np.sign(q[:,0])*side,np.zeros(len(q)),-crown_mm*.001*crown])*onset[:,None]
 if surface_envelope:
  lateral=smooth((np.abs(q[:,0])-.050)/.035)*smooth((q[:,2]-1.735)/.040)*smooth((q[:,1]+.060)/.050)
  for j,v in enumerate(q):
   if lateral[j]*onset[j]<1e-6:continue
   h,n,_,_=bv.find_nearest(Vector(v));clearance=float((Vector(v)-h).dot(n))
   excess=max(0.,clearance-.012)
   surface_delta=-np.array(n)*min(excess,.025)*onset[j]
   delta[j]=delta[j]*(1-lateral[j])+surface_delta*lateral[j]
 if np.linalg.norm(delta,axis=1).max()<1e-7:continue
 qs=np.vstack([q,(q[:-1]+q[1:])*.5]);ds=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(ds,axis=1)>1e-7
 qs=qs[moving];ds=ds[moving];limits=[min(.0003,gap(v))-1e-6 for v in qs];scale=1.
 for attempt in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(qs,ds,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale
 stats.append([i,scale,float(np.linalg.norm(delta*scale,axis=1).max())])
assert np.isfinite(p).all() and np.array_equal(p[off[:-1]],old[off[:-1]])
if not include_released:assert np.array_equal(p[np.repeat(released,sizes)],old[np.repeat(released,sizes)])
assert np.array_equal(p[old[:,2]<=1.735],old[old[:,2]<=1.735])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
out.mkdir(parents=True);np.savez_compressed(out/'local_envelope_stats.npz',stats=np.array(stats))
modelhash=None
if save:
 modeldir.mkdir(parents=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=digest(modeldir/'Ember_Regent.blend')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['02_ThreeQuarter','01_Front','05_OppositeSide','04_Back']:
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
st=np.array(stats);changed=np.linalg.norm(p-old,axis=1)>1e-7
report=dict(source=base,source_sha256=before,source_unchanged=True,model_saved=False,selected_fibers=len(stats),actually_changed_fibers=int(np.count_nonzero(st[:,2]>1e-7)),body_scale_quantiles=np.quantile(st[:,1],[0,.5,1]).tolist(),max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),changed_controls=int(changed.sum()),before_bounds_m=[old.min(0).tolist(),old.max(0).tolist()],after_bounds_m=[p.min(0).tolist(),p.max(0).tolist()],images_sha256=images,method='Primary only;all radii/counts/materials/other objects unchanged. Preserve original roots and first8mm arc with25mm smooth onset;exclude accepted663 released-tip cluster. Crown:down7mm*smooth((Z-1.835)/0.040). Sides:inX9mm*sign(X)*smooth((absX-.062)/.040)*smooth((Z-1.735)/.055)*(1-smooth((Z-1.835)/.040))*smooth((Y+.060)/.060). All controlsZ<=1.735 exact;frontal pointsY<=-.060 belowZ1.835 exact. Upper frontal geometry may lower,part roots and lower fringe preserved;not all accepted fringe geometry claimed identical. Whole-fiber body-gap backtracking at controls/midpoints;not continuous collision or art acceptance.')
report.update(model_saved=save,model_sha256=modelhash,crown_mm=crown_mm,side_mm=side_mm,include_released=include_released)
report['surface_envelope']=surface_envelope
report['method']=report['method'].replace('down7mm',f'down{crown_mm:g}mm').replace('inX9mm',f'inX{side_mm:g}mm')
if include_released:report['method']=report['method'].replace('exclude accepted663 released-tip cluster','include previously released-tip cluster to keep the crown envelope coherent')
if surface_envelope:report['method']+=' For lateral controls, continuously blend analytic delta with closest-body-normal movement toward12mm clearance, at most25mm, weighted by absX50..85mm,Z1.735..1.775,Y-60..-10mm and root onset. This changes Y and may raise individual Z values; frontal/lower controls and roots remain protected.'
manifest=json.dumps(report,indent=2)
(out/'envelope_manifest.json').write_text(manifest,encoding='utf-8')
if save:(modeldir/'envelope_manifest.json').write_text(manifest,encoding='utf-8')
print('CROWN_SIDE_ENVELOPE_PREVIEW',version,len(stats),flush=True)
