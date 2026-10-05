"""Source-matching Blender comparison; original licensed file is never saved.

Ordinary read/render control, no generative-model input, scripts disabled.
Run separately in each version with fresh output labels.
"""
import bpy,sys,json,hashlib,re
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];label=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',label):raise ValueError(label)
out=ROOT/'Exports'/label;render=ROOT/'Renders'/label
if out.exists() or render.exists():raise RuntimeError('Fresh version control required')
source=ROOT/'Source/FabMediumLayered/hairstyle.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();out.mkdir(parents=True)
dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for ob in bpy.data.objects:
 ev=ob.evaluated_get(dg)
 for ps in ev.particle_systems:
  paths=[np.array([k.co[:] for k in p.hair_keys],np.float32) for p in ps.particles]
  h=hashlib.sha256()
  for q in paths:h.update(q.tobytes())
  lengths=[float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum()) for q in paths]
  if not paths or not max(lengths)>0:raise RuntimeError('Require actual evaluated particle keys')
  scalars={p.identifier:getattr(ps.settings,p.identifier) for p in ps.settings.bl_rna.properties
   if p.type in {'INT','FLOAT','BOOLEAN','ENUM'} and not getattr(p,'is_array',False)}
  rows.append(dict(object=ob.name,system=ps.name,actual_particles=len(ps.particles),
   child_particles=len(ps.child_particles),saved_key_counts=sorted(set(map(len,paths))),
   full_key_sha256=h.hexdigest(),length_quantiles_m=np.quantile(lengths,[0,.5,.9,1]).tolist(),settings=scalars))
report=dict(blender_version=bpy.app.version_string,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 autoexec_disabled=True,source_saved=False,key_scope='Evaluated particles after frame_set(1), not raw unevaluated zero keys',systems=rows,
 scope='Saved keys/settings and original source render only; not fitting or art acceptance')
(out/'version_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FAB_VERSION_KEY_AUDIT',bpy.app.version_string,[(r['system'],r['actual_particles'],r['full_key_sha256']) for r in rows],flush=True)
if '--render' not in a:sys.exit(0)
render.mkdir(parents=True);s=bpy.context.scene
hair=bpy.data.objects['HairStyle'];hair.show_instancer_for_render=False
me=hair.data.copy();me.materials.clear();head=bpy.data.objects.new('Source scalp gray control only',me);s.collection.objects.link(head)
mat=bpy.data.materials.new('Neutral source scalp');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.18,.18,.18,1);bs.inputs['Roughness'].default_value=.65;me.materials.append(mat)
for p in me.polygons:p.use_smooth=True
for o in list(bpy.data.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
world=bpy.data.worlds.new('Neutral original source studio');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.05,.05,.05,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def aim(ob,pt):ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size in [('Source soft key',(-.3,-.45,.4),12,.4),('Source rim',(.3,.2,.3),12,.3),('Source fill',(.35,-.4,0),4,.35)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,0,-.02))
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=960,1120;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
name='01_OriginalFront';d=bpy.data.cameras.new(name);d.lens=63;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=(-.38,-.65,.13);aim(o,(0,0,-.025));s.camera=o
s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report['render_sha256']=hashlib.sha256((render/(name+'.png')).read_bytes()).hexdigest()
(out/'version_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FAB_VERSION_RENDERED',label,flush=True)
