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
def curve_geometry(o):
 p=np.empty(len(o.data.points)*3,np.float32);o.data.attributes['position'].data.foreach_get('vector',p)
 r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
 return hashlib.sha256(p.tobytes()+r.tobytes()+np.array(o.matrix_world,np.float32).tobytes()+repr([c.points_length for c in o.data.curves]).encode()).hexdigest()
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);original=meshes();rows=[]
original_curves={o.name:curve_geometry(o) for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render}
coverage_source=ROOT/'Exports/nativecoverage05/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(coverage_source),use_scripts=False)
primary_name='Bystedt layercut derivative • native root reflow'
coverage_support={o.name:curve_geometry(o) for o in bpy.data.objects if o.type=='CURVES' and not o.hide_render and o.name!=primary_name}
base_primary=bpy.data.objects[primary_name].data
base_positions=np.empty((len(base_primary.points),3),np.float32);base_primary.attributes['position'].data.foreach_get('vector',base_positions.ravel())
base_roots=base_positions[np.array([c.first_point_index for c in base_primary.curves])]
for version in a[1:]:
 path=ROOT/'Exports'/version/'Ember_Regent.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 assert meshes()==original,version+' original mesh changed'
 count=0;geometry={}
 for o in bpy.data.objects:
  if o.type!='CURVES' or o.hide_render:continue
  p=np.empty(len(o.data.points)*3,np.float32);o.data.attributes['position'].data.foreach_get('vector',p)
  r=np.empty(len(o.data.points),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
  assert np.isfinite(p).all() and np.isfinite(r).all() and (r>0).all(),o.name
  count+=len(o.data.curves)
  geometry[o.name]=hashlib.sha256(p.tobytes()+r.tobytes()+np.array(o.matrix_world,np.float32).tobytes()+repr([c.points_length for c in o.data.curves]).encode()).hexdigest()
 missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing,missing
 rows.append(dict(version=version,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
  original_mesh_geometry_uv_shape_keys_transforms_preserved=True,original_mesh_count=len(original),
  visible_native_curve_count=count,visible_curve_points_finite=True,radii_finite_positive=True,file_textures_available=True,
  visible_curve_geometry_by_object=geometry))
 if version.startswith(('nativesublayer','nativesections','nativerods','crosspart','nativedeclump','nativenodecontrol','nativeroll')):
  for name,digest in coverage_support.items():assert geometry.get(name)==digest,version+' short support changed'
  rows[-1]['short_support_geometry_exactly_unchanged_from']='nativecoverage05'
  if version.startswith(('nativesublayer','nativesections','nativerods','crosspart')):
   main=bpy.data.objects[primary_name].data
   pts=np.empty((len(main.points),3),np.float32);main.attributes['position'].data.foreach_get('vector',pts.ravel())
   roots=pts[np.array([c.first_point_index for c in main.curves])]
   assert np.array_equal(roots,base_roots),version+' actual follicle points changed'
   rows[-1]['all_primary_roots_exactly_unchanged_from']='nativecoverage05'
byversion={r['version']:r for r in rows}
for control in ['nativelobe03','nativelobe04']:
 if control in byversion and 'nativeroot03' in byversion:
  assert byversion[control]['visible_curve_geometry_by_object']==byversion['nativeroot03']['visible_curve_geometry_by_object'],'Shader control changed geometry'
  byversion[control]['visible_curve_geometry_exactly_unchanged_from']='nativeroot03'
if 'nativecoverage05' in byversion and 'nativelobe04' in byversion:
 before=byversion['nativelobe04']['visible_curve_geometry_by_object'];after=byversion['nativecoverage05']['visible_curve_geometry_by_object']
 for name,digest in before.items():assert after[name]==digest,'Undercoat changed primary geometry'
 for name in set(after)-set(before):assert after[name]==original_curves[name],'Restored support geometry changed'
 byversion['nativecoverage05']['primary_geometry_exactly_unchanged_from']='nativelobe04'
 byversion['nativecoverage05']['restored_short_geometry_exactly_unchanged_from_stable']=True
output.write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),studies=rows,
 scope='Static file checks only. Not artistic acceptance or exhaustive head/clothing/segments/animation validation.'),indent=2),encoding='utf-8')
print('HAIR_CANDIDATE_FILES_PASS',flush=True)
