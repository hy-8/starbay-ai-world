"""Bake only SintelHairOriginal legacy particle paths from a verified source.

Original Sintel / BenDansie hair CC BY3.0; retrieved via Scthe's mixed-license
format-conversion bundle. Do not import other bundle assets or execute scripts.
Cache is local. A gray source-head control render is not this project's hero.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
folder=ROOT/'Source/SintelFilm';source=folder/'Unity_Hair_Sintel_Source.blend'
out=folder/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh source bake required')
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='2a32f792a27beb8a85cb0be52bbcdc0970b6fcafc1fe31f7f808610166f32e57'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
for c in bpy.data.collections:c.hide_viewport=False
ob=bpy.data.objects['SintelHairOriginal'];settings=ob.particle_systems[0].settings
settings.display_step=6;settings.render_step=6
settings.child_percent=int(args[1]) if len(args)>1 else 250
settings.update_tag();ob.update_tag()
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=ev.particle_systems[0]
parents,children=len(ps.particles),len(ps.child_particles)
probe=[ps.co_hair(ev,particle_no=0,step=j)[:] for j in range(129)]
valid=np.flatnonzero(np.linalg.norm(np.array(probe),axis=1)>.1)
if not len(valid) or not np.array_equal(valid,np.arange(len(valid))):raise RuntimeError('Non-contiguous actual cache steps')
steps=len(valid)
if steps<9:raise RuntimeError('Actual particle cache not sufficiently evaluated')
paths=[];actual_steps=[]
for i in range(parents+children):
    a=np.array([ps.co_hair(ev,particle_no=i,step=j)[:] for j in range(steps)],np.float32)
    valid=np.flatnonzero(np.linalg.norm(a,axis=1)>.1)
    if len(valid)<4 or not np.array_equal(valid,np.arange(len(valid))):
        raise RuntimeError(f'Non-contiguous cache for actual hair {i}')
    a=a[:len(valid)];actual_steps.append(len(a))
    # Legacy children shorten their cache when their authored length is less
    # than the parent. Preserve each complete path; never discard short hairs.
    old=np.linspace(0,1,len(a));new=np.linspace(0,1,steps)
    paths.append(np.stack([np.interp(new,old,a[:,k]) for k in range(3)],axis=1))
paths=np.array(paths,np.float32)
if len(paths)<10000 or not np.isfinite(paths).all():raise RuntimeError('Source cache incomplete')
root_bounds=np.stack([paths[:,0].min(axis=0),paths[:,0].max(axis=0)])
if not (1.3<root_bounds[0,2]<1.7 and 1.6<root_bounds[1,2]<1.8):raise RuntimeError('Expected source head coordinates missing')
collider=bpy.data.objects['GEO-hair_collider.001']
body_v=np.array([collider.matrix_world@v.co for v in collider.data.vertices],np.float32)
collider.data.calc_loop_triangles();body_f=np.array([list(f.vertices) for f in collider.data.loop_triangles],np.int32)
out.mkdir(parents=True);render.mkdir(parents=True)
np.savez_compressed(out/'original_particle_paths.npz',positions=paths,source_head_vertices=body_v,source_head_triangles=body_f)
report=dict(original_object='SintelHairOriginal',source_sha256=source_hash,source_saved=False,autoexec_disabled=True,
 license='Original Sintel / BenDansie CC BY3.0; Scthe supplied mixed-license container; only original hair paths adopted for local evaluation',
 actual_parents=parents,actual_children=children,actual_valid_paths=len(paths),cache_points_per_path=steps,
 actual_cache_step_range=[min(actual_steps),max(actual_steps)],resampling='Per-hair contiguous actual cache; normalized interpolation retains actual tips',
 root_bounds_m=root_bounds.tolist(),hair_bounds_m=[paths.reshape(-1,3).min(axis=0).tolist(),paths.reshape(-1,3).max(axis=0).tolist()],
 radius_note='Legacy settings are not imported. New control uses original physical red hair shader and40um radii.',
 preview_scope='Gray source collider with original particle path shape. Not target-character results or artistic acceptance.')
(out/'bake_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Independent neutral control scene, no imported rig/material/texture/script.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
me=bpy.data.meshes.new('Source gray head collider');me.from_pydata(body_v.tolist(),[],body_f.tolist());me.update()
head=bpy.data.objects.new('Source head geometry • control only',me);scene.collection.objects.link(head)
mat=bpy.data.materials.new('Neutral gray source control');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.16,.16,.16,1);bs.inputs['Roughness'].default_value=.65;me.materials.append(mat)
for p in me.polygons:p.use_smooth=True
hm=bpy.data.materials.new('Physical red hair source control');hm.use_nodes=True
nt=hm.node_tree;nt.nodes.clear();output=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Color'].default_value=(.07,.006,.009,1);bs.inputs['Roughness'].default_value=.30;bs.inputs['Radial Roughness'].default_value=.38;nt.links.new(bs.outputs[0],output.inputs[0])
cu=bpy.data.hair_curves.new('Baked original Sintel particle path control');cu.add_curves([steps]*len(paths));cu.attributes['position'].data.foreach_set('vector',paths.ravel())
t=np.linspace(0,1,steps)
r=np.broadcast_to(.000040*(1-.995*t**2.6)**.7,(len(paths),steps)).astype(np.float32)
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r.ravel());cu.materials.append(hm)
hair=bpy.data.objects.new('Actual source hair • not project character',cu);scene.collection.objects.link(hair)
world=bpy.data.worlds.new('Source studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.055,.055,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def area(name,position,power,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=position;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large front key',(-.35,-.5,1.9),12,.4,(0,0,1.56))
area('Source edge',(.3,.2,1.9),16,.3,(0,0,1.56))
area('Source fill',(.4,-.3,1.6),4,.35,(0,0,1.56))
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1000,1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
for name,location in [('01_SourceThreeQuarter',(.38,-.65,1.74)),('02_SourceBack',(0,.68,1.68))]:
 d=bpy.data.cameras.new(name);d.lens=63;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,1.55))-o.location).to_track_quat('-Z','Y').to_euler();scene.camera=o
 scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Source_Groom_Control.blend'))
print('SINTEL_ACTUAL_PARTICLE_BAKE',len(paths),steps,flush=True)
