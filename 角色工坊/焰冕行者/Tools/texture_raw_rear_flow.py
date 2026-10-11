"""Submillimeter strand-direction variation on original mixed-control rear paths."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
selection=a[a.index('--selection')+1] if '--selection' in a else None
loose='--loose' in a;pilot='--pilot' in a;relief='--coherent-relief' in a;posterior_only='--posterior-only' in a
assert not posterior_only or relief
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2]+([selection] if selection else []))
save='--save-archive' in a;save_only='--save-only' in a;assert not save_only or save
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ARCHIVE/'Renders'/version;md=ARCHIVE/'Exports'/version
assert not out.exists() and not (ROOT/'Renders'/version).exists() and (not save or not md.exists())
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];roots=p[off[:-1]];tips=p[off[1:]-1]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
mask&=(tips[:,1]>.015)&(tips[:,2]<1.800)&(roots[:,1]>-.030)
if pilot:mask&=roots[:,0]<-.005
if selection:
 sm=json.loads((ROOT/'Renders'/selection/'edit_id_manifest.json').read_text());assert sm['source_sha256']==digest
 selected=np.zeros(len(sizes),bool);selected[np.load(ROOT/'Renders'/selection/'local_projected_indices.npz')['selected']]=True;mask&=selected
ids=np.flatnonzero(mask);assert len(ids)>100
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
scales=[];rng=np.random.default_rng(731992);phase=rng.uniform(0,2*np.pi,(len(sizes),2));amplitude=rng.uniform(.00035,.00075,len(sizes))
if loose:amplitude=rng.uniform(.0012,.0025,len(sizes))
for i in ids:
 path=old[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];t=arc/max(arc[-1],1e-8)
 tangent=np.gradient(path,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
 normal=path-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
 across=np.cross(tangent,normal)
 envelope=smooth((arc-.008)/.015)*(1-smooth((t-.82)/.13))
 waves=min(3.,max(1.,arc[-1]/.040))
 if loose:waves=min(2.,max(1.,arc[-1]/.070))
 transverse=np.sin(t*2*np.pi*waves+phase[i,0]);lift=.35+.35*np.sin(t*2*np.pi*(waves*.77)+phase[i,1])
 shift=amplitude[i]*envelope[:,None]*(across*transverse[:,None]+normal*lift[:,None])
 if relief:
  # Spatially coherent narrow raised sections in existing flow, not per-fiber noise.
  center=np.array([np.interp(.55*arc[-1],arc,path[:,j]) for j in range(3)])
  field=center[0]*510+center[1]*250+center[2]*140
  height=.001+.007*(.5+.5*np.sin(field))**2
  arch=smooth((arc-.008)/.025)*np.sin(np.pi*np.clip(t,0,1))**1.1
  shift=arch[:,None]*(normal*height+across*(.002*np.sin(field+.7)))
  if posterior_only:shift*=(smooth((1.850-path[:,2])/.025)*smooth((path[:,1]-.015)/.025))[:,None]
 samples=np.vstack([path,(path[:-1]+path[1:])*.5]);steps=np.vstack([shift,(shift[:-1]+shift[1:])*.5]);moving=np.linalg.norm(steps,axis=1)>1e-7
 samples=samples[moving];steps=steps[moving];thresholds=[min(.0003,gap(v))-1e-6 for v in samples];scale=1.
 for trial in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(samples,steps,thresholds)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=path+shift*scale;scales.append(scale)
assert np.isfinite(p).all() and np.array_equal(old[off[:-1]],p[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();modelhash=None
if save:
 cu.attributes.new('native_rear_strand_variation','BOOLEAN','CURVE').data.foreach_set('value',mask)
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
out.mkdir(parents=True);images={}
if not save_only:
 for shot in (['04_Back','05_OppositeSide'] if selection or pilot else ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']):
  s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
m=dict(source=base,source_sha256=digest,source_unchanged=True,selection=selection,model_saved=save,model_sha256=modelhash,render_archive=str(out),selected_fibers=len(ids),scale_quantiles=np.quantile(scales,[0,.5,1]).tolist(),zero_scale_fibers=int(np.count_nonzero(np.array(scales)==0)),max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),images_sha256=images,method='Restored raw rear paths only;optional exact inspected projection intersection. Keep original mixed control counts,radii,root8mm and terminal5percent. Smooth individual transverse/positive-normal directional variation0.35-0.75mm amplitude,1-3 waves over full path,seed731992. One scalar backtracking per curve preserves sampled original body clearance at controls/midpoints. No full-path resampling or material changes. Not continuous collision or art acceptance.')
(out/'strand_variation_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
m.update(loose=loose,pilot=pilot,amplitude_range_m=[.0012,.0025] if loose else [.00035,.00075],wave_range=[1,2] if loose else [1,3])
if loose:m['method']=m['method'].replace('0.35-0.75mm amplitude,1-3 waves','1.2-2.5mm amplitude,1-2 waves')
if relief:
 m.update(coherent_relief=True,method='Restored raw rear paths only. Preserve mixed counts,radii,root8mm,endpoints,original materials. At55percent arc,field=510*x+250*y+140*z;normal relief1..8mm by squared sine field,transverse2mm sine. Smooth25mm onset after8mm times sin(pi*t)^1.1 arch;no terminal5percent preservation claim. Whole-curve backtracking preserves original sampled body gap at controls/midpoints. Not continuous collision or art acceptance.')
 m.update(posterior_only=posterior_only,posterior_gate='Multiply displacement by smoothstep((1.850-oldZ)/25mm)*smoothstep((oldY-15mm)/25mm). Controls at/above1.850m or at/beforeY15mm exact.' if posterior_only else None)
 m.update(amplitude_range_m=[.001,.008],wave_range=None,amplitude_meaning='Normal relief before arch/spatial gate/backtracking;transverse component at most2mm')
(out/'strand_variation_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
if save:(md/'strand_variation_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('STRAND_VARIATION_RENDERED',version,len(ids),flush=True)
