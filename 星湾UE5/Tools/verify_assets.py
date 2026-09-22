"""Blender round-trip validation of FBX exports, independent of Unreal."""
import bpy,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'SourceAssets'
manifest=json.loads((SOURCE/'asset_manifest.json').read_text(encoding='utf-8'))
results=[]
for rec in manifest['assets']:
    path=SOURCE/rec['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256'],rec['file']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(path))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==1,(rec['file'],len(meshes))
    ob=meshes[0]
    points=[ob.matrix_world@v.co for v in ob.data.vertices]
    bounds=[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
    error=max(abs(a-b) for x,y in zip(bounds,rec['blenderBoundsMeters']) for a,b in zip(x,y))
    assert error<.002,(rec['file'],error)
    assert len(ob.data.vertices)==rec['vertices'],rec['file']
    assert all(math.isfinite(c) for p in points for c in p)
    assert all(len(face.vertices)>=3 for face in ob.data.polygons)
    results.append({'asset':rec['file'],'boundsErrorMeters':error,'vertices':len(ob.data.vertices),'sha256Verified':True})
report={'status':'passed','scope':'FBX Blender round trip, bounds, vertex count, finite coordinates, checksums','unrealImportTested':False,'assets':results}
(ROOT/'Validation').mkdir(exist_ok=True)
(ROOT/'Validation'/'asset_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('STARBAY_FBX_ROUNDTRIP_PASS',len(results))
