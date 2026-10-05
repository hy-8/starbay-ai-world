"""Counter-comb existing native fringe away from the wide outward curtain.

Retains all native follicles, source micro-waves, short support and rear hair.
Not a new template, runtime simulation or art-acceptance assertion.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh cross-part study only')
source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();root=raw[:,0];tip=raw[:,-1];t=np.linspace(0,1,65)
ids=np.flatnonzero((tip[:,1]<-.14)&(tip[:,2]<1.81)&(root[:,2]>1.81)&(root[:,1]<-.035)&(root[:,0]>.012))
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
contacts=0
for i in ids:
 old=raw[i];v=old.copy();w=smooth((t-.12)/.78)
 # This changes the direction across the actual part, unlike global mirroring.
 v[:,0]=root[i,0]+(old[:,0]-root[i,0])*(1-2.2*w)-.011*w
 v[:,1]-=.004*np.sin(np.pi*t)*w
 # Reduced tight root crest, keeping native shoulder length and micro-waves.
 crest=smooth((v[:,2]-(root[i,2]+.004))/.015)*smooth(t/.12)*(1-smooth((t-.50)/.15))
 v[:,2]-=.005*crest
 for _ in range(2):
  correction=np.zeros((65,3))
  for j in range(1,64):
   if v[j,2]<1.795:continue
   hit,n,_,dist=bv.find_nearest(Vector(v[j]));gap=(Vector(v[j])-hit).dot(n)
   if dist<.03 and gap<.001:
    delta=np.array(n)*(.0012-gap);contacts+=1
    for k in range(max(1,j-2),min(65,j+3)):correction[k]+=delta*np.exp(-.5*((k-j)/1.3)**2)
  v+=correction
 v[0]=root[i];q[i]=v
assert np.array_equal(q[:,0],raw[:,0]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
out.mkdir(parents=True);render.mkdir(parents=True)
(out/'crosspart_manifest.json').write_text(json.dumps(dict(source='nativecoverage05',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 author='Daniel Bystedt',license='CC BY-SA; version unspecified',changed_fibers=len(ids),all_original_roots_unchanged=True,
 smooth_contact_events=contacts,max_displacement_m=float(np.linalg.norm(q[ids]-raw[ids],axis=2).max()),
 method='Native positive-part fringe counter-combed across actual part by smooth whole-shaft X warp; original micro-waves, follicles and rear/support retained',
 status='Unreviewed actual direction study',scope='Discrete body contact only, not full segment/eye/clothing/animation/art acceptance'),indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
name='02_ThreeQuarter';s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('CROSS_PART_FRINGE_SAVED',version,len(ids),flush=True)
