"""Paired static file checks. These checks do not decide artistic quality."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];output=ROOT/'Exports'/a[0]
if output.exists() or output.parent!=ROOT/'Exports':raise RuntimeError('Fresh audit required')
def meshes():
 result={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data;p=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',p)
  h=hashlib.sha256(p.tobytes()+np.array(o.matrix_world,np.float32).tobytes()+repr([tuple(f.vertices) for f in m.polygons]).encode())
  for uv in m.uv_layers:h.update(np.array([x.uv[:] for x in uv.data],np.float32).tobytes())
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    p=np.empty(len(k.data)*3,np.float32);k.data.foreach_get('co',p);h.update(p.tobytes()+repr((k.name,k.value)).encode())
  result[o.name]=h.hexdigest()
 return result
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);original=meshes();rows=[]
for version in a[1:]:
 path=ROOT/'Exports'/version/'Ember_Regent.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 assert meshes()==original,version+' original mesh changed'
 count=0
 for o in bpy.data.objects:
  if o.type!='CURVES' or o.hide_render:continue
  p=np.empty(len(o.data.points)*3,np.float32);o.data.attributes['position'].data.foreach_get('vector',p)
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  assert np.isfinite(p).all() and np.isfinite(r).all() and (r>0).all(),o.name
  count+=len(o.data.curves)
 missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing,missing
 rows.append(dict(version=version,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
  original_mesh_geometry_uv_shape_keys_transforms_preserved=True,original_mesh_count=len(original),
  visible_native_curve_count=count,visible_curve_points_finite=True,radii_finite_positive=True,file_textures_available=True))
output.write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),studies=rows,
 scope='Static file checks only. Not artistic acceptance or exhaustive head/clothing/segments/animation validation.'),indent=2),encoding='utf-8')
print('HAIR_CANDIDATE_FILES_PASS',flush=True)
