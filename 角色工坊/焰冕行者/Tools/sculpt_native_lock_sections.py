"""Local section comb on actual native shafts, not replacement shell geometry.

Bystedt CC BY-SA derivative stays local. Existing scalp support untouched.
Representative sections first; whole-head work requires inspected results.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
sample='--sample' in a
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh section comb required')
source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
q=p.reshape(-1,65,3).astype(float);raw=q.copy();root=q[:,0];tip=q[:,-1]
ids=np.flatnonzero((tip[:,1]<-.14)&(tip[:,2]<1.81)&(root[:,2]>1.81)&(root[:,1]<-.035))
labels,inv=np.unique(np.round(tip[ids]/.007).astype(int),axis=0,return_inverse=True)
counts=np.bincount(inv);groups=[ids[inv==k] for k in np.argsort(counts)[::-1] if counts[k]>=100]
if sample:groups=groups[:6]
body=bpy.data.objects['CC0 male body • retained topology']
assert np.allclose(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);rows=[];guard=0
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
for g,members in enumerate(groups):
 old=raw[members];center=np.median(old,axis=0)
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 radial=center-np.array([0,-.044,1.771]);normal=radial-tangent*np.sum(radial*tangent,axis=1)[:,None]
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8)
 across=np.cross(tangent,normal);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
 coord=old[:,0]@across[0];order=np.argsort(coord);parts=np.array_split(order,3)
 phase=(g*2.399963)%6.283185
 # Native complete roots are kept, section depth diverges gradually after them.
 for level,sub in enumerate(parts):
  if not len(sub):continue
  ix=members[sub];sign=level-1
  lateral=sign*(.0048*np.sin(np.pi*t)+.0025*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t))*smooth(t/.30)
  depth=(sign*.0062*np.sin(np.pi*t)**1.25+.0018*np.cos(phase)*np.sin(2*np.pi*t)*np.sin(np.pi*t))*smooth(t/.28)
  v=raw[ix]+across[None]*lateral[None,:,None]+normal[None]*depth[None,:,None]
  # The high positive-side tight loop relaxes coherently; no root movement.
  crest=smooth((v[:,:,2]-(root[ix,2,None]+.004))/.016)*(1-smooth((t-.48)/.20))[None]*smooth(t/.10)[None]
  v[:,:,2]-=.0075*crest
  # Small section cuts use along-shaft resampling, never abrupt deleted points.
  cut=[.91,1.,.96][level]
  if cut<1:
   for k in range(len(v)):
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v[k],axis=0),axis=1))]
    v[k]=np.stack([np.interp(t*arc[-1]*cut,arc,v[k,:,j]) for j in range(3)],axis=1)
  # Relax inherited terminal zigzags without erasing the complete wave shape.
  for _ in range(4):
   mid=(v[:,:-2]+2*v[:,1:-1]+v[:,2:])*.25
   w=(.4*smooth((t[1:-1]-.67)/.18))[None,:,None]
   v[:,1:-1]=v[:,1:-1]*(1-w)+mid*w
  # Broad smooth correction around contact events rather than isolated snaps.
  for k,index in enumerate(ix):
   for iteration in range(2):
    correction=np.zeros((65,3))
    for j in range(1,64):
     if v[k,j,2]<1.80:continue
     hit,n,_,dist=bv.find_nearest(Vector(v[k,j]));gap=(Vector(v[k,j])-hit).dot(n)
     if dist<.025 and gap<.0005:
      delta=np.array(n)*(.0007-gap);guard+=1
      for l in range(max(1,j-2),min(65,j+3)):correction[l]+=delta*np.exp(-.5*((l-j)/1.2)**2)
    v[k]+=correction
   q[index]=v[k];q[index,0]=raw[index,0]
 rows.append(dict(fibers=len(members),subsection_counts=list(map(len,parts)),
  section_cut_factors=[.91,1.,.96],max_displacement_m=float(np.linalg.norm(q[members]-raw[members],axis=2).max())))
assert np.array_equal(q[:,0],raw[:,0]) and np.isfinite(q).all()
changed=np.flatnonzero(np.max(np.linalg.norm(q-raw,axis=2),axis=1)>1e-8)
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source='nativecoverage05',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',representative_sample=sample,
 sections=rows,changed_fibers=len(changed),all_original_roots_unchanged=True,all_support_geometry_unchanged=True,
 method='Existing endpoint sections split by real root ordering; coherent 3D depth comb, gentle layer cuts along shafts, tight crest relaxation, terminal fairing',
 smooth_contact_events=guard,status='Unreviewed 3D section sculpt',
 scope='Discrete body contact only; not exhaustive segment/clothing/animation or artistic validation')
(out/'section_comb_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if sample else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('NATIVE_SECTIONS_COMBED',version,len(changed),flush=True)
