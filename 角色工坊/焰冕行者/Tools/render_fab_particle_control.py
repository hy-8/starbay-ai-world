"""Render the original licensed particle groom, not the converted cache.
No imported text blocks or automatic scripts are executed; source unchanged.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Source/FabMediumLayered/hairstyle.blend';out=ROOT/'Renders/fabparticlecontrol01'
if out.exists():raise RuntimeError('Fresh control required')
out.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene
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
for name,pos in [('01_OriginalFront',(-.38,-.65,.13)),('02_OriginalBack',(0,.68,.10))]:
 d=bpy.data.cameras.new(name);d.lens=63;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,0,-.025));s.camera=o
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'original_control_manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_saved':False,'autoexec_disabled':True,'original_geometry_radius_and_shader_retained':True,'scope':'Original source style control, not target character or art acceptance.'},indent=2),encoding='utf-8')
print('ORIGINAL_FAB_PARTICLE_CONTROL_RENDERED',flush=True)
