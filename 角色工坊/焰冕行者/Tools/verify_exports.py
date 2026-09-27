"""Real Blender readback of static delivery files, run in a fresh background process."""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v04'
directory=ROOT/'Exports'/version
if not bpy.app.background:raise RuntimeError('Only run in background Blender.')
report={'version':version,'checks':[]}
for suffix in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    file=directory/('Ember_Regent_Static.'+suffix)
    if suffix=='glb':bpy.ops.import_scene.gltf(filepath=str(file))
    else:bpy.ops.import_scene.fbx(filepath=str(file))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    assert points and all(math.isfinite(x) for v in points for x in v)
    low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
    size=[high[i]-low[i] for i in range(3)]
    assert 1.85<size[2]<2.3, size
    assert len(meshes)>100
    assert all(len(o.data.materials)>0 for o in meshes)
    assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
    report['checks'].append({'format':suffix,'mesh_objects':len(meshes),'vertices':len(points),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'bounds_meters':{'min':low,'max':high,'size':size},'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'result':'passed: import, finite geometry, human scale, materials, no stage/rig implied'})
bpy.ops.wm.open_mainfile(filepath=str(directory/'Ember_Regent.blend'))
missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
assert all(name in bpy.data.collections for name in ['01_Body','03_OuterRobe','04_Mantle','05_Hair','06_Regalia'])
report['blend']='Reopened editable collections; no missing external texture images.'
report['limitations']='Static geometry only; no performance, rigging, deformation, animation, cloth, or Unreal play validation.'
(directory/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VERIFICATION_PASSED',json.dumps(report))
