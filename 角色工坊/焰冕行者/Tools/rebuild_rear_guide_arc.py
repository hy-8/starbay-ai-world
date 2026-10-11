"""Fit one simple guide arc per selected original posterior fiber; preview first."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
wisps='--surface-wisps' in a
cross='--cross-wisps' in a;assert not cross or wisps
all_rear='--all-rear' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in [version,base,selection])
out=ARCHIVE/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
oldr=r.copy();wisp_ids=[]
sel=ARCHIVE/'Renders'/selection;meta=json.loads((sel/'edit_id_manifest.json').read_text());assert meta['source_sha256']==before
mask=np.zeros(len(sizes),bool);mask[np.load(sel/'local_projected_indices.npz')['selected']]=True
if all_rear:mask[:]=True
raw=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',raw)
mask&=raw&(old[off[1:]-1,1]>.015)&(old[off[1:]-1,2]<1.800)&(old[off[:-1],1]>-.030)
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 protected=np.empty(len(mask),bool);cu.attributes[key].data.foreach_get('value',protected);mask&=~protected
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
stats=[];protected_indices=[]
for i in np.flatnonzero(mask):
 q=old[off[i]:off[i+1]].astype(float)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 keep=np.searchsorted(arc,.008,side='right');protected_indices.extend(range(off[i],off[i]+keep))
 if keep>=len(q)-4 or arc[-1]<.045:continue
 start=keep-1;tail=q[start:];sarc=arc[start:]-arc[start];t=sarc/max(sarc[-1],1e-8)
 # Quadratic Bezier: one guide handle removes alternating S-bends while retaining endpoints.
 w=2*t*(1-t);fixed=(1-t[:,None])**2*tail[0]+t[:,None]**2*tail[-1]
 handle=np.sum(w[:,None]*(tail-fixed),axis=0)/max(np.sum(w*w),1e-10)
 curve=fixed+w[:,None]*handle
 delta=np.zeros_like(q);delta[start:]=(curve-tail)*smooth((sarc-.001)/.025)[:,None]
 if wisps and (int(i)*2654435761%1000)<140:
  # Sparse fine fibers emerge above the fitted layer; keep dense coverage beneath.
  unit=(q-np.array([0,-.035,1.776]))/np.array([.085,.105,.115])
  unit/=np.maximum(np.linalg.norm(unit,axis=1)[:,None],1e-10)
  along=arc/max(arc[-1],1e-8)
  envelope=smooth((arc-.008)/.025)*np.sin(np.pi*along)**1.2
  if cross:
   tangent=np.gradient(q,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
   transverse=np.cross(tangent,unit);transverse/=np.maximum(np.linalg.norm(transverse,axis=1)[:,None],1e-10)
   signed=.008*(2*((int(i)*2246822519%997)/996)-1)
   delta+=(.003*unit+signed*transverse)*envelope[:,None]
  else:delta+=unit*(.006*envelope)[:,None]
  r[off[i]:off[i+1]]=oldr[off[i]:off[i+1]]+(np.minimum(oldr[off[i]:off[i+1]],.000035)-oldr[off[i]:off[i+1]])*smooth((arc-.008)/.020)
  wisp_ids.append(int(i))
 delta[arc<=.008]=0;delta[-1]=0
 # One cap for the entire fiber avoids a pointwise clipped shape.
 cap=min(1.,.024/max(np.linalg.norm(delta,axis=1).max(),1e-10));delta*=cap
 samples=np.vstack([q,(q[:-1]+q[1:])*.5]);steps=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(steps,axis=1)>1e-7
 samples=samples[moving];steps=steps[moving];limits=[min(.0003,gap(v))-1e-6 for v in samples]
 scale=1.
 for trial in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(samples,steps,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale
 stats.append([int(i),cap,scale,float(arc[-1]),float(np.linalg.norm(np.diff(p[off[i]:off[i+1]],axis=0),axis=1).sum())])
assert np.array_equal(p[off[:-1]],old[off[:-1]]) and np.array_equal(p[off[1:]-1],old[off[1:]-1])
assert np.array_equal(p[protected_indices],old[protected_indices]) and np.isfinite(p).all()
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
cu.attributes['radius'].data.foreach_set('value',r)
out.mkdir(parents=True)
np.savez_compressed(out/'local_arc_data.npz',selected=np.flatnonzero(mask),stats=np.array(stats))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflect=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflect@cam.matrix_world@reflect
images={}
for shot in ['04_Back','05_OppositeSide','02_ThreeQuarter']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
st=np.array(stats)
report=dict(source=base,source_sha256=before,selection=selection,source_unchanged=True,selected_fibers=int(mask.sum()),processed_fibers=len(stats),model_saved=False,roots_and_tips_exact=True,root8mm_exact=True,counts_radii_unchanged=True,max_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),clearance_scale_quantiles=np.quantile(st[:,2],[0,.5,1]).tolist(),path_length_change_m_quantiles=np.quantile(st[:,4]-st[:,3],[0,.5,1]).tolist(),images_sha256=images,method='Per original selected posterior fiber: fit quadratic Bezier single handle by least squares after8mm root prefix,25mm onset. Keep original tip position; whole-fiber24mm displacement cap and body clearance backtracking at controls/midpoints. No scalp projection, pruning, noise, shader edits or full-model save. Arc length can change; original hairstyle endpoint lengths are retained. Not continuous collision or art acceptance.')
report.update(all_rear=all_rear,selection_scope='All restored raw fibers with tipY>15mm,tipZ<1.800m,rootY>-30mm excluding accepted fringe/accent; projected region not applied.' if all_rear else 'Intersect local projected IDs with raw rear-reaching fibers;exclude accepted fringe/accent.')
if wisps:
 report.update(surface_wisps=True,wisp_fibers=len(wisp_ids),counts_radii_unchanged=False,counts_unchanged=True,wisp_rule='Deterministic hash14percent of selected fibers. Add6mm outward radial arch with25mm onset after8mm,zero at tip;before whole-curve cap/body guard. Cap selected wisp radii35microns with20mm ramp after8mm;all other radii unchanged.')
 if cross:report.update(cross_wisps=True,wisp_rule='Same sparse14percent and35micron radii. Instead of6mm radial lift,use3mm radial plus deterministic signed0..8mm transverse arch;25mm onset after8mm,zero at tips,before whole-fiber24mm cap/body guard. All unselected fibers unchanged.')
(out/'guide_arc_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GUIDE_ARC_PREVIEW_FINISHED',version,flush=True)
