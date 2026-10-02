"""Attach reconstructed guide roots to actual scalp and release their tips.

No visible solid wig; retain all prior iterations. Blender -- version source.
"""
import bpy,sys,re,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:]
version,source=args[:2]
for v in [version,source]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',v):raise ValueError(v)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/source/'Ember_Regent.blend'))
body=bpy.data.objects['CC0 male body • retained topology']
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
hair=bpy.data.objects['Cherry asymmetric surface groom'];cu=hair.data
n=len(cu.attributes['position'].data);p=np.empty(n*3,dtype=np.float32)
cu.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,96,3)
C=Vector((0,-.044,1.771));t=np.linspace(0,1,96);rootweight=np.maximum(0,1-t/.20)**2
attached=0
for strand in p:
    root=Vector(strand[0]);direction=root-C
    if root.z<1.78 or direction.length<.01:continue
    hit,normal,_,_=bv.ray_cast(C,direction.normalized(),.35)
    if hit is None:continue
    change=np.asarray(hit+normal*.0005)-strand[0]
    if np.linalg.norm(change)>.075:continue
    strand+=change[None,:]*rootweight[:,None];attached+=1
# Independent gravitational free tips break the blunt surface-derived endings.
rng=np.random.default_rng(10403)
tail=np.maximum(0,(t-.79)/.21)**2
length=rng.uniform(.003,.014,(len(p),1))
p[:,:,2]-=length*tail[None,:]
posterior=p[:,0,1]>.018
p[posterior,:,0]+=rng.normal(0,.0025,(posterior.sum(),1))*tail
cu.attributes['position'].data.foreach_set('vector',p.ravel())
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';detail='--detail' in args
scene.render.resolution_x=1800 if detail else 1200;scene.render.resolution_y=2100 if detail else 1400
scene.render.resolution_percentage=100 if detail else 80;scene.cycles.samples=256 if detail else 96
scene.cycles.use_denoising=False
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'version':version,'source':source,'attached_root_count':attached,'main_strands':len(p),'changes':['surface-guide roots projected onto actual scalp with smooth first-20-percent blend','independent 3-14mm gravitational free tips'],'samples':scene.cycles.samples,'denoising':False,'status':'candidate requires visual review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('ROOTED_GROOM_SAVED',report,flush=True)
