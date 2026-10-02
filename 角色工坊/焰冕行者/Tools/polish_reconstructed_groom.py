"""Trim frontal undercoat away from eyes and face; refine physical color.

Keeps the independently reconstructed visible layers and old candidates.
Blender: -- version source-version [--detail]
"""
import bpy,sys,re,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source=args[:2]
for v in [version,source]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',v):raise ValueError(v)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/source/'Ember_Regent.blend'))
col=bpy.data.collections['05_Hair']
ob=bpy.data.objects['Scalp rooted coverage beneath sculpted locks']
cu=ob.data;n=len(cu.attributes['position'].data)
pos=np.empty(n*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',pos);pos=pos.reshape(-1,72,3)
rad=np.empty(n,dtype=np.float32);cu.attributes['radius'].data.foreach_get('value',rad);rad=rad.reshape(-1,72)
kept=[];radii=[];trimmed=0
for p,r in zip(pos,rad):
    # Real hairline: frontal undercoat stops above the brows; temples expose
    # the eye area; posterior fibers stay shorter than the visible layers.
    invalid=((p[:,1]<-.105)&(p[:,2]<1.791)&(np.abs(p[:,0])<.080))
    invalid|=((p[:,1]<-.055)&(p[:,2]<1.705))
    invalid|=(p[:,2]<1.674)
    bad=np.flatnonzero(invalid);stop=int(bad[0]) if len(bad) else 72
    if stop<8:continue
    if stop<72:trimmed+=1
    index=np.linspace(0,stop-1,72)
    p2=np.column_stack([np.interp(index,np.arange(72),p[:,j]) for j in range(3)])
    kept.append(p2);radii.append(r[0]*(1-.98*np.linspace(0,1,72))**.65)
data=bpy.data.hair_curves.new('Trimmed scalp-rooted undercoat with open eyes');data.add_curves([72]*len(kept))
data.attributes['position'].data.foreach_set('vector',np.asarray(kept,dtype=np.float32).ravel())
data.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.asarray(radii,dtype=np.float32).ravel())
for m in cu.materials:data.materials.append(m)
ob.data=data
mat=data.materials[0]
for node in mat.node_tree.nodes:
    if node.type=='VALTORGB':
        node.color_ramp.elements[0].color=(.008,.0008,.0013,1)
        node.color_ramp.elements[1].color=(.046,.004,.007,1)
    if node.type=='MAP_RANGE':
        node.inputs['To Min'].default_value=.28
        node.inputs['To Max'].default_value=.48
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.use_denoising=False
detail='--detail' in args
scene.render.resolution_x=1800 if detail else 1200;scene.render.resolution_y=2100 if detail else 1400
scene.render.resolution_percentage=100 if detail else 80;scene.cycles.samples=256 if detail else 96
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'version':version,'source':source,'changes':['frontal undercoat trimmed above brows','temple and neck undercoat shortened','dark cherry physical fiber color and varied roughness'],'undercoat_strands':len(kept),'trimmed_strands':trimmed,'samples':scene.cycles.samples,'denoising':False,'status':'candidate requires visual review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('POLISHED_GROOM_SAVED',report,flush=True)
