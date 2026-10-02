"""Art-directed diagonal fringe and softer crown for the reconstructed groom.

Independent 3D curves. No projected portrait or visible solid support mesh.
Blender -- version source [--detail]
"""
import bpy,sys,json,re,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:]
version,source=args[:2]
for v in [version,source]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',v):raise ValueError(v)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh candidate required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/source/'Ember_Regent.blend'))
col=bpy.data.collections['05_Hair'];main=bpy.data.objects['Cherry asymmetric surface groom']
for ob in col.objects:
    if ob.type!='CURVES':continue
    cu=ob.data;xyz=np.empty(len(cu.points)*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);p=xyz.reshape(-1,3)
    # Smoothly compress excessive crown height rather than clipping a flat cap.
    above=np.maximum(0,p[:,2]-1.886)
    p[:,2]-=above*.45
    if ob==main:
        weight=np.clip((p[:,2]-1.795)/.095,0,1)*np.clip((.075-p[:,1])/.13,0,1)
        p[:,0]+=.028*np.exp(-(p[:,0]/.09)**2)*weight
    cu.attributes['position'].data.foreach_set('vector',xyz)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());C=Vector((0,-.044,1.771))
rng=np.random.default_rng(10503);N=96;t=np.linspace(0,1,N);s=t[:,None]
strands=[];radii=[];guides=[]
for k in range(22):
    f=k/21;rx=.028+rng.uniform(-.004,.004);ry=-.124+f*.125
    h,n,_,_=bv.ray_cast(Vector((rx,ry,2.05)),Vector((0,0,-1)),.40)
    if h is None:continue
    h+=n*.0006
    endpoint=(-.047-.053*f,-.176+.087*f,1.764+.055*f)
    control=np.array([h,(-.007-.020*f,-.162+.060*f,1.892-.005*f),
                      (-.085-.016*f,-.180+.079*f,1.840-.023*f),endpoint])
    g=control[0]*(1-s)**3+3*control[1]*(1-s)**2*s+3*control[2]*(1-s)*s*s+control[3]*s**3
    g[:,0]+=.0035*np.sin(t*7.5+f)*np.sin(math.pi*t)
    g[:,1]+=.003*np.sin(t*8+f*2)*np.sin(math.pi*t)
    tangent=np.gradient(g,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
    lateral=np.cross(tangent,np.array([0,1,0]));lateral/=np.maximum(np.linalg.norm(lateral,axis=1,keepdims=True),1e-8)
    normal=np.cross(lateral,tangent);count=190;phase=rng.uniform(0,6.28,(count,1))
    width=rng.normal(0,.0021,(count,1))*(.65+.35*np.sin(math.pi*t))*(1-.82*t**4)
    width+=.00075*np.sin(t*19+phase)*np.sin(math.pi*t)
    depth=rng.normal(0,.0013,(count,1))*(1-.8*t**4)+.00045*np.sin(t*23+phase)*np.sin(math.pi*t)
    p=g[None,:,:]+lateral[None,:,:]*width[:,:,None]+normal[None,:,:]*depth[:,:,None]
    end=rng.uniform(.88,1,(count,1));q=t*end*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);blend=(q-lo)[:,:,None]
    p=p[np.arange(count)[:,None],lo]*(1-blend)+p[np.arange(count)[:,None],hi]*blend
    strands.append(p.astype(np.float32));radii.append((rng.uniform(.000027,.000038,(count,1))*(1-.982*t)**.7).astype(np.float32));guides.append(g)
xyz=np.concatenate(strands);radius=np.concatenate(radii)
cu=bpy.data.hair_curves.new('Art-directed diagonal layered fringe');cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.ravel());cu.materials.append(main.data.materials[0])
ob=bpy.data.objects.new('Independent swept cherry fringe',cu);col.objects.link(ob)
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';detail='--detail' in args;scene.cycles.use_denoising=False
scene.render.resolution_x=1800 if detail else 1200;scene.render.resolution_y=2100 if detail else 1400;scene.render.resolution_percentage=100 if detail else 80;scene.cycles.samples=256 if detail else 96
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'version':version,'source':source,'changes':['smooth crown height compression','front crown moved into stronger side part','independent diagonal scalp-rooted fringe'],'fringe_guides':len(guides),'fringe_strands':len(xyz),'samples':scene.cycles.samples,'status':'candidate requires visual review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');np.savez_compressed(out/'fringe_guides.npz',guides=np.asarray(guides))
print('ASYMMETRIC_FRINGE_SAVED',report,flush=True)
