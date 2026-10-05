"""Conservative local reshape of existing groom, preserving complete fibers.

No licensed geometry export, no generated portrait, no claim of art approval.
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
if out.exists() or render.exists():raise RuntimeError('Fresh candidate required')
source=ROOT/('Exports/settledshag01/Ember_Regent.blend' if any(x in a for x in ['--pigment-control','--gravity-ends']) else 'Exports/napeunderlay02/Ember_Regent.blend')
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology']
assert np.allclose(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mat=bpy.data.materials.new('Settled shag • unified physical red hair');mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear()
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.025,.0015,.0025,1)
ramp.color_ramp.elements[1].color=(.095,.009,.012,1)
nt.links.new(info.outputs['Random'],ramp.inputs[0])
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR'
bs.inputs['Roughness'].default_value=.36;bs.inputs['Radial Roughness'].default_value=.42
nt.links.new(ramp.outputs[0],bs.inputs['Color'])
if '--pigment-control' in a:
 bs.parametrization='MELANIN'
 bs.inputs['Melanin'].default_value=.52
 bs.inputs['Melanin Redness'].default_value=.8
 bs.inputs['Tint'].default_value=(.48,.06,.055,1)
 bs.inputs['Random Color'].default_value=.12
 bs.inputs['Roughness'].default_value=.28
 bs.inputs['Radial Roughness'].default_value=.35
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],output.inputs[0])
rows=[]
for o in bpy.data.objects:
 if o.type!='CURVES' or o.hide_render:continue
 o.data=o.data.copy();cu=o.data
 cu.materials.clear();cu.materials.append(mat)
 p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
 original=p.copy();repairs=0;maxrepair=0.
 longlayer=o.name.startswith(('Authored frontal revision','Original posterior surface'))
 # Names are explicit so a new component cannot silently receive deformation.
 if o.name.startswith('Authored frontal revision') or ('posterior' in o.name.lower() and 'coverage' not in o.name.lower()):longlayer=True
 if '--pigment-control' in a:longlayer=False
 if '--gravity-ends' in a:longlayer=o.name.startswith('Original posterior shag')
 if longlayer:
  for c in cu.curves:
   ix=slice(c.first_point_index,c.first_point_index+c.points_length);q=p[ix]
   t=np.linspace(0,1,len(q));env=t*t*(3-2*t)
   side=np.clip((np.abs(q[:,0])-.067)/.060,0,1)
   high=np.clip((q[:,2]-1.856)/.040,0,1)
   # Smooth spatial masks and zero root influence, never hard height cuts.
   if '--gravity-ends' in a:
    delta=np.diff(q,axis=0).astype(float);length=np.linalg.norm(delta,axis=1)
    w=np.clip((t[1:]-.30)/.70,0,1);w=w*w*(3-2*w)
    delta[:,2]-=.48*length*w
    delta[:,0]*=1-.28*w
    delta*=length[:,None]/np.maximum(np.linalg.norm(delta,axis=1)[:,None],1e-12)
    q[1:]=q[0]+np.cumsum(delta,axis=0)
    phase=float(q[0,0]*46+q[0,1]*32)
    # Root-coherent gentle variation, not independent per-fiber noise.
    q[:,0]+=.003*np.sin(t*2*np.pi+phase)*env
    q[:,1]+=.002*np.cos(t*2*np.pi+phase)*env
   else:
    q[:,2]-=.005*high*env
    q[:,0]-=np.sign(q[:,0])*.006*side*env
    q[:,2]-=.009*side*env
   # Keep all fibers and gently soften abrupt discrete shape variations.
   for _ in range(2):
    q[1:-1]=q[1:-1]*.5+(q[:-2]+q[2:])*.25
   q[0]=original[ix][0]
   for j in range(1,len(q)):
    hit,n,_,dist=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(n)
    if dist<.025 and gap<.0003:
     amount=.0004-gap;q[j]+=np.array(n)*amount;repairs+=1;maxrepair=max(maxrepair,amount)
  cu.attributes['position'].data.foreach_set('vector',p.ravel())
 rows.append(dict(object=o.name,curves=len(cu.curves),geometry_modified=longlayer,
  max_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),
  finite=bool(np.isfinite(p).all()),body_point_repairs=repairs,maximum_repair_m=maxrepair))
out.mkdir(parents=True);render.mkdir(parents=True)
report=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),components=rows,material_only_pigment_control='--pigment-control' in a,gravity_end_control='--gravity-ends' in a,
 method='Preserved complete existing fibers; smooth crown and side settlement, two low-pass path passes; unified physical hair material',
 artistic_status='Unreviewed real 3D candidate',scope='Static discrete body guard only, no complete clothing/segment/animation proof')
(out/'settlement_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in (['02_ThreeQuarter'] if '--single-view' in a else ['01_Front','02_ThreeQuarter','03_Side','04_Back']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('EXISTING_SHAG_SETTLED',version,flush=True)
