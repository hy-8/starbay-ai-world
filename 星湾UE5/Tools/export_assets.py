"""Blender-only asset preparation. Does not require or modify an Unreal installation.
Exports one baked static mesh per scene layer, plus imported doors kept separate.
The source GLBs and original .blend remain untouched.
"""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Matrix

PROJECT=Path(__file__).resolve().parents[1]
GAME=PROJECT.parent/'星湾街区_3D探索'
OUT=PROJECT/'SourceAssets'
OUT.mkdir(exist_ok=True)
records=[]

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1.0

def export_objects(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    # Bake object transforms into vertices before join, preserving text and placement.
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.join()
    ob=bpy.context.object
    ob.name=name
    # Canonical Unreal coordinates expressed as Blender meters before FBX conversion:
    # UE X = Blender Y (north), UE Y = Blender X (east), UE Z = Blender Z.
    # Standard FBX -Y/Z conversion is handled by UE; verify with exported calibration markers.
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
