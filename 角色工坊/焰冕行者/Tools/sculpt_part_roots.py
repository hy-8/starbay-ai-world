"""Recomb just the raised part roots of a saved native groom.

Actual curve geometry, no compositing or portrait generation. Adapted Bystedt
hair retains CC BY-SA; version unspecified in inspected original evidence.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0];source_version=args[1]
DRAFT='--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in [version,source_version]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
ob=next(o for o in bpy.data.collections['05_Hair'].objects if o.type=='CURVES')
cu=ob.data;p=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,3).astype(float)
changed=0;fixed=0;offset=0

def recomb(s):
 global changed,fixed
 r=s[0].copy()
 if not (.005<r[0]<.063 and -.142<r[1]<-.027 and r[2]>1.837):return s
 m=min(len(s)-2,max(4,int(len(s)*.35)));end=s[m].copy()
 hit,n,_,_=bv.find_nearest(Vector(r));normal=np.array(n)
 d=end-r;length=max(float(np.linalg.norm(d)),.010)
 tangent=d-normal*np.dot(d,normal);tangent/=max(float(np.linalg.norm(tangent)),1e-8)
 end_tan=s[m+1]-s[m-1];end_tan/=max(float(np.linalg.norm(end_tan)),1e-8)
 a=r+tangent*length*.34+normal*.0015;b=end-end_tan*length*.24
 u=np.linspace(0,1,m+1)[:,None]
 s[:m+1]=(1-u)**3*r+3*(1-u)**2*u*a+3*(1-u)*u*u*b+u**3*end
 for i in range(1,m+1):
  hit,n,_,dist=bv.find_nearest(Vector(s[i]));gap=(Vector(s[i])-hit).dot(n)
  if gap<.0008 and dist<.045:s[i]=np.array(hit+n*.0010);fixed+=1
 changed+=1
 return s

for c in cu.curves:
 size=len(c.points);p[offset:offset+size]=recomb(p[offset:offset+size]);offset+=size
cu.attributes['position'].data.foreach_set('vector',p.astype(np.float32).ravel())
for go in bpy.data.objects:
 if go.type!='CURVE' or 'Cut and shaped source guides' not in go.name:continue
 for sp in go.data.splines:
  s=recomb(np.array([q.co[:3] for q in sp.points],float))
  for q,v in zip(sp.points,s):q.co=(*v,1)
tx=bpy.data.texts.get('ADAPTED_HAIR_CREDITS')
if tx:tx.write('\nFurther modification: crown part roots recombed along the actual scalp tangent with a local cubic transition. Hidden guide evidence is not a live modifier of the dense groom.\n')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if DRAFT else 192;scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),hair_author='Daniel Bystedt',license='CC BY-SA; version unspecified in inspected source',method='local scalp-tangent cubic transition for crown part roots; other fibers and radii retained',curves_recombed_including_source_guides=changed,clearance_repairs=fixed,draft=DRAFT,samples=scene.cycles.samples,status='unreviewed actual geometry candidate')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('PART_ROOT_FLOW_SAVED',version,flush=True)
