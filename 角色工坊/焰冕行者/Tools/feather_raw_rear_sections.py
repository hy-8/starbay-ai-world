"""Combine explicit rear guide families, tiered lengths and tapered terminal spread."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a;veil='--layer-veil' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';out=ARCHIVE/'Renders'/version;assert not out.exists()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(source);bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);oldr=r.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
roots=p[off[:-1]];tips=p[off[1:]-1]
mask&=(tips[:,1]>.015)&(tips[:,2]<1.800)&(roots[:,1]>-.030)
if pilot:mask&=roots[:,0]<-.005
ids=np.flatnonzero(mask);ts=np.linspace(0,1,48);sampled=[];arcs=[]
for i in ids:
 q=old[off[i]:off[i+1]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];arcs.append(arc)
 sampled.append(np.column_stack([np.interp(ts*arc[-1],arc,q[:,j]) for j in range(3)]))
sampled=np.array(sampled);features=sampled[:,[12,24,36],:].reshape(len(ids),-1)
K=48 if pilot else 128;centers=[features[len(ids)//2]];distance=np.full(len(ids),np.inf)
for k in range(1,K):
 distance=np.minimum(distance,((features-centers[-1])**2).sum(1));centers.append(features[np.argmax(distance)])
centers=np.array(centers)
for _ in range(15):
 labels=np.argmin(((features[:,None]-centers[None])**2).sum(2),axis=1)
 for k in range(K):
  if np.any(labels==k):centers[k]=features[labels==k].mean(0)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
scales=[];cuts=[];changed_ids=[]
rng=np.random.default_rng(94031);veil_pick=rng.random(len(sizes));veil_length=rng.random(len(sizes))
for k in range(K):
 rows=np.flatnonzero(labels==k)
 if not len(rows):continue
 center=sampled[rows].mean(0);anchor=center[24]
 field=np.sin(anchor[0]*191+anchor[1]*139+anchor[2]*113)
 for row in rows:
  i=ids[row];q=old[off[i]:off[i+1]].astype(float);radius=oldr[off[i]:off[i+1]].astype(float);arc=arcs[row];L=arc[-1];t=arc/max(L,1e-8)
  if veil and (veil_pick[i]>.28 or L<.055):continue
  cut=min(.032,(.10+.16*(.5+.5*field))*L)
  if veil:cut=min(.060,L*(.22+.26*(.5+.5*field))*(.88+.12*veil_length[i]))
  remap=arc-cut*smooth((arc-.012)/max(L-.012,1e-8));short=np.column_stack([np.interp(remap,arc,q[:,j]) for j in range(3)])
  ct=np.clip(remap/max(L,1e-8),0,1)
  c=np.column_stack([np.interp(ct,ts,center[:,j]) for j in range(3)])
  tangent=np.gradient(c,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
  normal=c-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
  across=np.cross(tangent,normal)
  width=np.sum((short-c)*across,axis=1)
  contraction=.82*smooth((t-.25)/.65)*smooth((arc-.008)/.025)
  if veil:contraction*=.35
  pull=.008*np.tanh(width*contraction/.008)
  feather=short-across*pull[:,None]
  # Each family gets a gentle outward/backward feathered end, not a random kink.
  terminal=smooth((t-.60)/.40)*smooth((arc-.008)/.025)
  feather+=terminal[:,None]*np.array([np.sign(anchor[0])*(.003+.004*(.5+.5*field)),.004,0])
  if veil:
   # A sparse raised layer leaves most original flow in place as coverage.
   # Local normal here is derived from existing guide direction, not face projection.
   feather+=normal*(.006*smooth((t-.25)/.55))[:,None]*smooth((arc-.008)/.025)[:,None]
  delta=feather-q;delta[arc<=.008]=0
  samples=np.vstack([q,(q[:-1]+q[1:])*.5]);steps=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(steps,axis=1)>1e-7
  samples=samples[moving];steps=steps[moving];limits=[min(.0003,gap(v))-1e-6 for v in samples]
  scale=1.
  for trial in range(7):
   if all(gap(v+d*scale)>=g for v,d,g in zip(samples,steps,limits)):break
   scale*=.5
  else:scale=0.
  p[off[i]:off[i+1]]=q+delta*scale
  newradius=np.interp(remap,arc,radius)*(1-.985*smooth((t-.70)/.30))
  newradius[arc<=.008]=radius[arc<=.008]
  r[off[i]:off[i+1]]=radius+(newradius-radius)*scale
  scales.append(scale);cuts.append(cut);changed_ids.append(int(i))
assert np.array_equal(old[off[:-1]],p[off[:-1]]) and np.isfinite(p).all() and (r>0).all()
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.attributes['radius'].data.foreach_set('value',r);cu.update_tag()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
out.mkdir(parents=True);images={}
for shot in (['04_Back','05_OppositeSide'] if pilot else ['04_Back','05_OppositeSide','03_Side','02_ThreeQuarter']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
m=dict(source=base,source_sha256=before,source_unchanged=True,pilot=pilot,model_saved=False,selected_fibers=len(ids),guide_families=K,scale_quantiles=np.quantile(scales,[0,.5,1]).tolist(),zero_scale_fibers=int(np.count_nonzero(np.array(scales)==0)),requested_cut_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist(),max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),images_sha256=images,method='Original rear families clustered by 25/50/75percent arc positions. Combined10-26percent arc shortening capped32mm, transverse taper82percent capped8mm and terminal outward3-7mm/back4mm feather. Mixed control counts and root8mm retained; terminal radii tapered. Whole-curve body clearance backtracking on controls/midpoints. No new scalp projection. Static preview only; no continuous collision or art acceptance.')
if veil:m.update(layer_veil=True,selected_fibers=len(changed_ids),eligible_fibers=len(ids),method='Sparse layer on original rear: deterministic seed94031 picks28percent of eligible fibers longer55mm; family cut22-48percent times0.88-1 jitter capped60mm, transverse contraction28.7percent capped8mm, outward3-7mm/back4mm tip plus6mm gradual lift along guide-derived normal. Remaining fibers untouched for coverage. Root8mm, mixed counts retained, changed terminal radii tapered; whole-curve discrete body guard. No new scalp projection, no saved model or continuous-collision/art approval.')
(out/'feather_sections_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8');print('FEATHER_SECTIONS_FINISHED',version,flush=True)
