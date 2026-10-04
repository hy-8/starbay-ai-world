"""Actual source-model control render, not a finished character portrait.

Hair Styles: Daniel Bystedt, CC BY-SA (version unspecified in source).
Preserves the source file; only camera/lighting are changed in memory.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
LONG='--long' in args
X=5 if LONG else 10
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
dest=ROOT/'Renders'/version
if dest.exists():raise RuntimeError('Fresh review directory required')
dest.mkdir(parents=True)
source=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
for name in ['Braids hair','Cyberpunk hair','Curly hair' if LONG else 'Long hair']:bpy.data.collections[name].hide_render=True
if LONG:
 for key in ['long hair main','long hair strands']:
  h=bpy.data.objects[key]
  print('LONG_MODIFIERS',key,[(m.name,m.type) for m in h.modifiers],flush=True)
  for mod in h.modifiers:
   if mod.type!='NODES':continue
   for n in mod.node_group.nodes:
    if n.type=='GROUP':print('LONG_GROUP',key,n.node_tree.name,[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],flush=True)
for o in bpy.data.objects:
 if o.type in ['LIGHT','FONT']:o.hide_render=True
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles_curves.shape='THICK'
def light(name,loc,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((X,-.3,15.2))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Source control key',(X-5,-9,20),4500,7);light('Source control fill',(X+6,-6,17),2200,6);light('Source control contour',(X+3,4,19),5000,5)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.04,.04,.04,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
camera=bpy.data.cameras.new('Source control camera');ob=bpy.data.objects.new('Source control camera',camera);scene.collection.objects.link(ob);scene.camera=ob;camera.type='ORTHO';camera.ortho_scale=4.6
scene.render.resolution_x=1050;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
for name,loc in [('01_Front',(X,-30,15.5)),('02_ThreeQuarter',(X+8,-28,15.5))]:
 ob.location=loc;ob.rotation_euler=(Vector((X,-.3,15.1))-ob.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
record={'type':'source asset control render; not the user character','author':'Daniel Bystedt','license':'CC BY-SA','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'changes':'camera and lighting only','source_style':'long hair' if LONG else 'curly hair','adopted_on_character':False}
(dest/'source_control.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('SOURCE_CONTROL_RENDERED',version,flush=True)
