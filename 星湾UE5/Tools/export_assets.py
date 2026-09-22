"""Blender-only asset preparation. Does not require or modify an Unreal installation.
Exports one baked static mesh per scene layer, plus imported doors kept separate.
The source GLBs and original .blend remain untouched.
Run in a separate background Blender process. Existing FBX exports are preserved;
use -- --output-dir <fresh-folder> to prepare a new asset version.
"""
import bpy, json, hashlib, argparse, sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
GAME=PROJECT.parent/'星湾街区_3D探索'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=PROJECT/'SourceAssets')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=args.output_dir.resolve()
# reset() below destroys the current in-memory scene. Never run it in an interactive
# editor where there may be unsaved manual changes; background export owns its scene.
if not bpy.app.background:
    raise RuntimeError('Use blender --background --factory-startup --python export_assets.py; the open editor scene must be preserved')
if OUT.exists() and (list(OUT.glob('*.fbx')) or (OUT/'asset_manifest.json').exists()):
    raise RuntimeError('Existing exports will not be overwritten. Pass -- --output-dir <fresh-folder>: '+str(OUT))
for source in ('starbay_environment.glb','district_detail_v6.glb'):
    if not (GAME/'assets'/source).is_file():raise RuntimeError('Missing source GLB: '+source)
OUT.mkdir(parents=True,exist_ok=True)
records=[]

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1.0

def export_objects(objects,name):
    if not objects:raise RuntimeError('No mesh objects to export for '+name)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    # Bake object transforms into vertices before join, preserving text and placement.
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.join()
    ob=bpy.context.object
    ob.name=name
    if not ob.data.vertices:raise RuntimeError('Empty mesh: '+name)
    # Keep Blender world positions here. The UE bootstrap infers the FBX axis conversion
    # from the three calibration meshes, then maps north to UE X and east to UE Y.
    dest=OUT/(name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(dest),use_selection=True,object_types={'MESH'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Y',axis_up='Z',use_space_transform=True,
        bake_anim=False,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
    bounds=[ob.matrix_world@v.co for v in ob.data.vertices]
    records.append({'name':name,'file':dest.name,'bytes':dest.stat().st_size,
        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),
        'blenderBoundsMeters':[[min(v[i] for v in bounds) for i in range(3)],
                               [max(v[i] for v in bounds) for i in range(3)]]})

for source,name in [('starbay_environment.glb','SM_District'),('district_detail_v6.glb','SM_CourtyardDetails')]:
    reset()
    bpy.ops.import_scene.gltf(filepath=str(GAME/'assets'/source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    # Door leaves remain separate assets for future native interaction; no irreversible mesh merge.
    doors=[o for o in meshes if o.name.startswith('EntryDoor')]
    export_objects([o for o in meshes if o not in doors],name)
    for door in doors:export_objects([door], 'SM_'+door.name)

# Three one-meter cubes calibrate handedness, scale and both horizontal axes.
for suffix,location in [('Origin',(0,0,.5)),('East',(10,0,.5)),('North',(0,10,.5))]:
    reset()
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    export_objects([bpy.context.object],'SM_Calibration_'+suffix)
report={'schema':1,'units':'meters in source, centimeters in Unreal',
        'sourceGameToUnreal':'X=-game.z*100, Y=game.x*100, Z=game.y*100',
        'importTransformStatus':'requires Unreal calibration verification',
        'assets':records}
(OUT/'asset_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('STARBAY_UE_ASSETS_READY',len(records))
