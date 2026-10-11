"""Arc-distance low-pass study on existing rear fibers, without scalp retransport."""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
pilot='--pilot' in a;side_envelope='--side-envelope' in a
rear_sweep='--rear-sweep' in a
terminal_sweep='--terminal-sweep' in a;assert not terminal_sweep or rear_sweep
selection=a[a.index('--selection')+1] if '--selection' in a else None
if selection:assert re.fullmatch('[A-Za-z0-9_-]+',selection) and not side_envelope
assert not rear_sweep or not (side_envelope or selection)
save='--save-archive' in a;save_only='--save-only' in a
assert not save_only or save
assert not save or selection
modeldir=ARCHIVE/'Exports'/version
assert not save or not modeldir.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';out=ARCHIVE/'Renders'/version
assert not out.exists()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
roots=p[off[:-1]];tips=p[off[1:]-1]
mask&=(tips[:,1]>.015)&(tips[:,2]<1.800)&(roots[:,1]>-.030)
if pilot:mask&=roots[:,0]<-.005
if side_envelope:
 hit=(old[:,0]<-.050)&(old[:,1]>.010)&(old[:,2]>1.770)&(old[:,2]<1.870)
 mask=np.add.reduceat(hit.astype(np.int32),off[:-1])>0
if selection:
 sel=ARCHIVE/'Renders'/selection;sm=json.loads((sel/'edit_id_manifest.json').read_text());assert sm['source_sha256']==before
 selected=np.load(sel/'local_projected_indices.npz')['selected'];mask=np.zeros(len(sizes),bool);mask[selected]=True
 for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
  protected=np.empty(len(sizes),bool);cu.attributes[key].data.foreach_get('value',protected);assert not protected[mask].any()
ids=np.flatnonzero(mask)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
scales=[]
for i in ids:
 q=old[off[i]:off[i+1]].astype(float)
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];t=arc/max(arc[-1],1e-8)
 # Fit a quadratic locally with Gaussian arc weights: preserves linear/quadratic flow
 # while suppressing tight directional reversals; no resampling of stored topology.
 if rear_sweep:
  # Preserve radial volume while changing the flow direction of posterior midshafts.
  theta=.22*smooth((arc-.008)/.025)*np.sin(np.pi*t)**1.1*smooth((1.855-q[:,2])/.025)*smooth((q[:,1]-.015)/.025)
  if terminal_sweep:theta=.14*smooth((arc-.008)/.060)*smooth((q[:,1]-.015)/.025)
  x=q[:,0];y=q[:,1]+.035
  swept=q.copy();swept[:,0]=x*np.cos(theta)-y*np.sin(theta);swept[:,1]=x*np.sin(theta)+y*np.cos(theta)-.035
  delta=swept-q
 elif side_envelope:
  envelope=smooth((arc-.008)/.025)*smooth((-q[:,0]-.050)/.030)*smooth((q[:,1]-.010)/.035)*smooth((q[:,2]-1.770)/.025)*smooth((1.870-q[:,2])/.025)
  delta=envelope[:,None]*np.array([.012,-.004,-.004])
 else:
  result=[]
  for j in range(len(q)):
   x=(arc-arc[j])/(.030 if selection else .018);w=np.exp(-.5*x*x);design=np.column_stack([np.ones(len(x)),x,x*x])
   coef=np.linalg.lstsq(design*np.sqrt(w[:,None]),q*np.sqrt(w[:,None]),rcond=None)[0]
   result.append(coef[0])
  delta=np.array(result)-q
  envelope=smooth((arc-.008)/.025)*(1-smooth((t-.88)/.10))*smooth((1.850-q[:,2])/.025)*smooth((q[:,1]-.015)/.025)
  if selection:envelope=smooth((arc-.008)/.025)
  delta*=envelope[:,None]
 cap=.024 if rear_sweep else .012
 mag=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,cap/np.maximum(mag,1e-10))[:,None]
 delta[0]=0
 if not side_envelope and not selection and not terminal_sweep:delta[-1]=0
 samples=np.vstack([q,(q[:-1]+q[1:])*.5]);steps=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(steps,axis=1)>1e-7
 samples=samples[moving];steps=steps[moving];limits=[min(.0003,gap(v))-1e-6 for v in samples]
 scale=1.
 for trial in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(samples,steps,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale;scales.append(scale)
assert np.isfinite(p).all() and np.array_equal(old[off[:-1]],p[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
modelhash=None
if save:
 assert 'native_projected_bend_relaxation' not in cu.attributes
 cu.attributes.new('native_projected_bend_relaxation','BOOLEAN','CURVE').data.foreach_set('value',mask)
 modeldir.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=digest(modeldir/'Ember_Regent.blend')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
out.mkdir(parents=True);images={}
for shot in (['04_Back','05_OppositeSide'] if pilot else ['04_Back','05_OppositeSide','03_Side','02_ThreeQuarter']):
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
m=dict(source=base,source_sha256=before,source_unchanged=True,pilot=pilot,model_saved=False,selected_fibers=len(ids),scale_quantiles=np.quantile(scales,[0,.5,1]).tolist(),zero_scale_fibers=int(np.count_nonzero(np.array(scales)==0)),max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),images_sha256=images,method='Arc-distance Gaussian weighted quadratic regression sigma18mm at original mixed controls; displacements capped12mm; retain root8mm and terminal2percent; ramp25mm and posterior spatial gate. Whole-curve body clearance backtracking on controls/midpoints. No normal projection/scalp transport/new noise. Original roots, tips, radii, counts and other objects untouched; not continuous collision or art acceptance.')
if side_envelope:m.update(side_envelope=True,method='Local posterior negativeX stepped side silhouette brush on all primary fibers intersecting x<-50mm,y>10mm,z1.770..1.870m. Displacement[+12,-4,-4]mm multiplied by smooth onset30mm in X,35mm in Y,25mm top/bottom Z and25mm after root8mm; resultant capped12mm. Roots/counts/radii/materials/other geometry unchanged; terminal points may move inside region. Whole-curve controls/midpoints body clearance backtracking; no continuous collision or art approval.')
if selection:m.update(selection=selection,method='Only exact inspected local projected set; assert no accepted inner curtain/fringe sweeps/curved accent selected. Gaussian arc-distance quadratic fit sigma30mm,25mm onset after original root8mm,12mm displacement cap, no blanket posterior gate. Terminal points may move; mixed counts/radii/roots retained. Whole-curve controls/midpoints body clearance backtracking. Preview only, not continuous collision or art approval.')
if rear_sweep:m.update(rear_sweep=True,method='Original restored rear-reaching raw paths; rotate midshaft XY about(0,-35mm) by at most0.22rad times sin(pi*t)^1.1,root8mm/25mm onset,posteriorZ<1.855/Y>15mm smooth25mm gate. Preserve radial distance before24mm displacement cap and whole-curve body-gap backtracking. Roots/tips/counts/radii/materials unchanged. Changes coherent flow direction without new scalp projection/noise/cut. Preview only;not continuous collision/art acceptance.')
if terminal_sweep:m.update(terminal_sweep=True,method='Original restored rear-reaching raw paths; progressive XY rotation about(0,-35mm),0.14rad times smoothstep((arc-8mm)/60mm)*smoothstep((oldY-15mm)/25mm). No upperZ gate or end reversal.24mm displacement cap then whole-curve body-gap backtracking. Original root8mm/counts/radii/Z values retained;terminal XY intentionally moves. Preview only;not continuous collision/art acceptance.')
m.update(model_saved=save,model_sha256=modelhash,positions_sha256=hashlib.sha256(p.tobytes()).hexdigest())
if save:m['method']=m['method'].replace('Preview only,','Saved static candidate,');(modeldir/'bend_smoothing_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
(out/'bend_smoothing_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('BEND_SMOOTHING_FINISHED',version,flush=True)
