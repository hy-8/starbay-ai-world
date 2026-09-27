"""Export the saved couture model in a separate Blender process. Never resaves the source."""
import bpy, sys, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v11'
if not bpy.app.background:raise RuntimeError('Background Blender only.')
directory=ROOT/'Exports'/version
for ext in ['glb','fbx']:
    if (directory/('Ember_Regent_Static.'+ext)).exists():raise RuntimeError('Existing export protected.')
bpy.ops.wm.open_mainfile(filepath=str(directory/'Ember_Regent.blend'))
bpy.ops.object.select_all(action='DESELECT')
for c in bpy.data.collections:
    if c.name.startswith(('90_','08_')):continue
    for o in c.objects:
        if o.type in ['MESH','CURVE'] and not o.hide_render and not o.hide_get():o.select_set(True)
objects=list(bpy.context.selected_objects)
assert objects
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.object.convert(target='MESH')
objects=list(bpy.context.selected_objects)
report={'version':version,'status':'static couture display model; no rig/cloth physics/UE play validation','units':'meters','mesh_objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'excluded_collections':['90_Stage','08_EmberFX'],'textile_maps':['Ember_Brocade_Albedo.png','Ember_Brocade_ORM.png','Ember_Brocade_Normal.png']}
bpy.ops.export_scene.gltf(filepath=str(directory/'Ember_Regent_Static.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.ops.export_scene.fbx(filepath=str(directory/'Ember_Regent_Static.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,bake_anim=False,add_leaf_bones=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
report['files']={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in directory.iterdir() if p.suffix in ['.blend','.glb','.fbx']}
(directory/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('COUTURE_EXPORT_COMPLETE',json.dumps(report))
