"""Bake licensed Fab particle paths to local native curves; no source autoexec.

Only operates on the existing NoAI content, using ordinary geometry scripts.
Do not redistribute original or derived groom geometry as standalone assets.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
folder=ROOT/'Source/FabMediumLayered';source=folder/'hairstyle.blend'
out=folder/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh study required')
sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert sha=='0adca6484a4d6c51c3dfd33e5d13ed42f3bf44cae3fcea8f4aa10c710077ecd4'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['HairStyle']
for ps in ob.particle_systems:
 ps.settings.display_step=5;ps.settings.render_step=5;ps.settings.update_tag()
ob.update_tag();bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
groups=[];paths=[];lengths=[]
for gi,ps in enumerate(ev.particle_systems):
 probe=np.array([ps.co_hair(ev,particle_no=0,step=j)[:] for j in range(70)])
 valid=np.flatnonzero(np.linalg.norm(probe,axis=1)>1e-7)
 if not len(valid) or not np.array_equal(valid,np.arange(len(valid))):raise RuntimeError('Source cache not contiguous')
 steps=len(valid)
 start=len(paths)
 for i in range(len(ps.particles)):
  q=np.array([ps.co_hair(ev,particle_no=i,step=j)[:] for j in range(steps)],np.float32)
  actual=np.flatnonzero(np.linalg.norm(q,axis=1)>1e-7)
  if len(actual)<4 or not np.array_equal(actual,np.arange(len(actual))):raise RuntimeError(f'Invalid particle {gi}/{i}')
  q=q[:len(actual)];lengths.append(len(q))
  t=np.linspace(0,1,len(q));tt=np.linspace(0,1,33)
  paths.append(np.stack([np.interp(tt,t,q[:,k]) for k in range(3)],axis=1))
 groups.append({'name':ps.name,'range':[start,len(paths)],'particles':len(ps.particles),'cache_steps':steps})
 print('EXTRACTED',ps.name,len(paths),flush=True)
p=np.array(paths,np.float32)
assert len(p)==54764 and np.isfinite(p).all()
v=np.array([ob.matrix_world@q.co for q in ob.data.vertices],np.float32)
ob.data.calc_loop_triangles();f=np.array([list(q.vertices) for q in ob.data.loop_triangles],np.int32)
out.mkdir(parents=True);render.mkdir(parents=True)
np.savez_compressed(out/'licensed_particle_paths.npz',positions=p,scalp_vertices=v,scalp_triangles=f)
report={'source_sha256':sha,'original_particle_count':len(p),'groups':groups,
 'source_blender_header':'5.1 file read with 4.5.9, cache validity checked; source unchanged',
 'cache_step_range':[min(lengths),max(lengths)],'positions_per_path':33,
 'hair_bounds_m':[p.reshape(-1,3).min(0).tolist(),p.reshape(-1,3).max(0).tolist()],
 'root_bounds_m':[p[:,0].min(0).tolist(),p[:,0].max(0).tolist()],
 'license':'Fab Standard License, NoAI; Muzammil; used locally as existing geometry, not generative model input',
 'scope':'Original source control on gray source scalp. Not target character or artistic acceptance.'}
(out/'bake_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
me=bpy.data.meshes.new('Source scalp control');me.from_pydata(v.tolist(),[],f.tolist());me.update()
head=bpy.data.objects.new('Licensed source scalp • control',me);s.collection.objects.link(head)
hm=bpy.data.materials.new('Neutral source head');hm.use_nodes=True
bs=hm.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.18,.18,.18,1);bs.inputs['Roughness'].default_value=.65;me.materials.append(hm)
for q in me.polygons:q.use_smooth=True
mat=bpy.data.materials.new('Physical burgundy red source control');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Color'].default_value=(.085,.008,.012,1);bs.inputs['Roughness'].default_value=.32;bs.inputs['Radial Roughness'].default_value=.4
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],output.inputs[0])
t=np.linspace(0,1,33)
for group in groups:
 q=p[slice(*group['range'])];cu=bpy.data.hair_curves.new(group['name']);cu.add_curves([33]*len(q));cu.attributes['position'].data.foreach_set('vector',q.ravel())
 r=np.broadcast_to(.000045*(1-.996*t**2.4)**.75,(len(q),33)).astype(np.float32);cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r.ravel());cu.materials.append(mat)
 hair=bpy.data.objects.new(group['name']+' • native source',cu);s.collection.objects.link(hair)
world=bpy.data.worlds.new('Gray source studio');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.05,.05,.05,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def aim(ob,pt):ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size in [('Source soft key',(-.3,.45,.4),12,.4),('Source rim',(.3,-.2,.3),12,.3),('Source fill',(.35,.4,0),4,.35)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,0,-.02))
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=64;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=960,1120;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
for name,pos in [('01_SourceThreeQuarter',(-.38,.65,.13)),('02_SourceBack',(0,-.68,.10))]:
 d=bpy.data.cameras.new(name);d.lens=63;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,0,-.025));s.camera=o
 s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Source_Groom_Control.blend'))
print('FAB_SOURCE_CONTROL_COMPLETE',version,flush=True)
