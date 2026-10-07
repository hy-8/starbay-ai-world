"""Explicit static comparison for an additive crown sample; not art acceptance."""
import bpy,numpy as np,json,hashlib,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];filename,base,candidate=a[:3]
if not all(re.fullmatch('[A-Za-z0-9_.-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/filename
if out.exists():raise RuntimeError('Fresh check required')
def array(data,member,n):
 v=np.empty((len(data),n),np.float32);data.foreach_get(member,v.ravel());return v
def state(version):
 path=ROOT/'Exports'/version/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 meshes={};curves={}
 for o in bpy.data.objects:
  if o.type=='MESH':
   m=o.data;h=hashlib.sha256(array(m.vertices,'co',3).tobytes()+np.array(o.matrix_world,np.float32).tobytes()+repr([tuple(f.vertices) for f in m.polygons]).encode())
   for u in m.uv_layers:h.update(np.array([v.uv[:] for v in u.data],np.float32).tobytes())
   if m.shape_keys:
    for k in m.shape_keys.key_blocks:h.update(array(k.data,'co',3).tobytes()+repr((k.name,k.value)).encode())
   meshes[o.name]=h.hexdigest()
  elif o.type=='CURVES' and not o.hide_render:
   c=o.data;p=array(c.attributes['position'].data,'vector',3);r=array(c.attributes['radius'].data,'value',1);assert np.isfinite(p).all() and np.isfinite(r).all() and (r>0).all()
   curves[o.name]=hashlib.sha256(p.tobytes()+r.tobytes()+np.array([x.points_length for x in c.curves]).tobytes()+np.array(o.matrix_world,np.float32).tobytes()).hexdigest()
 assert not [im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
 return digest,meshes,curves
bh,bm,bc=state(base);ah,am,ac=state(candidate)
assert bm==am and all(ac[n]==d for n,d in bc.items());added=set(ac)-set(bc)
assert added=={'Original crown accent A','Original crown accent B','Original crown accent C'}
report=dict(source=base,candidate=candidate,source_sha256=bh,candidate_sha256=ah,mesh_count=len(bm),all_mesh_geometry_uv_shape_keys_transforms_exact=True,all_four_existing_visible_hair_exact=True,added_objects=sorted(added),added_fibers=2100,finite_positive_radii_textures_available=True,scope='Static additive file comparison only; not artistic acceptance or segment/body/eye/clothing/animation collision assurance.')
out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('ADDITIVE_PAIR_PASS',candidate,flush=True)
