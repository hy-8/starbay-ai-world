"""Read-only paired file invariants for local Fab trials; never art acceptance."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'Exports/fab_studies_structure01.json'
if out.exists():raise RuntimeError('Preserve existing audit')
def snapshot():
 rows={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data;a=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',a)
  h=hashlib.sha256(a.tobytes()+np.array(o.matrix_world,np.float32).tobytes()+repr([tuple(p.vertices) for p in m.polygons]).encode())
  for l in m.uv_layers:h.update(np.array([p.uv[:] for p in l.data],np.float32).tobytes())
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    a=np.empty(len(k.data)*3,np.float32);k.data.foreach_get('co',a);h.update(a.tobytes()+repr((k.name,k.value)).encode())
  rows[o.name]=h.hexdigest()
 return rows
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);old=snapshot();rows=[]
for version in ['fabfit01','fabfit02','fabfit03','fabfit04']:
 path=ROOT/'Exports'/version/'Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 assert snapshot()==old
 grooms=[]
 for o in bpy.data.objects:
  if not o.name.startswith('Muzammil Fab Standard') or o.type!='CURVES':continue
  p=np.empty(len(o.data.points)*3,np.float32);o.data.attributes['position'].data.foreach_get('vector',p)
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  assert np.isfinite(p).all() and np.isfinite(r).all() and (r>0).all()
  grooms.append(dict(object=o.name,curves=len(o.data.curves),points=len(o.data.points),finite=True,positive_radii=True,
   geometry_sha256=hashlib.sha256(p.tobytes()+r.tobytes()+np.array(o.matrix_world,np.float32).tobytes()).hexdigest()))
 assert len(grooms)==3
 missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing
 rows.append(dict(version=version,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
  all_original_mesh_geometry_uv_shape_keys_transforms_preserved=True,original_mesh_count=len(old),new_grooms=grooms,
  all_file_textures_available=True,scope='File invariants only; not artistic acceptance, complete collisions or animation'))
assert rows[2]['new_grooms']==rows[3]['new_grooms'],'Material-only comparison changed geometry'
out.write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'studies':rows,
 'fabfit03_vs_04_geometry_exactly_unchanged':True},indent=2),encoding='utf-8')
print('FAB_PAIRED_STRUCTURE_PASS',flush=True)
