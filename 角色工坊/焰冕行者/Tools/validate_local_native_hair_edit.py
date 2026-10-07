"""Compare explicit localized native edits, including untouched fiber subsets."""
import bpy,sys,json,hashlib,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];output,base,candidate,edited,attr=a[:5]
material_only='--material-only' in a
nape_profile='--nape-profile' in a
no_long_tails='--no-long-tails' in a
if no_long_tails and not nape_profile:raise ValueError('No-long-tail gate requires nape-profile comparison')
if not all(re.fullmatch('[A-Za-z0-9_.-]+',x) for x in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/output
if out.exists():raise RuntimeError('Fresh local audit required')
def arr(data,key,member,n):
 v=np.empty((len(data),n),np.float32) if n>1 else np.empty(len(data),np.float32)
 data.foreach_get(member,v.ravel());return v
def state(version):
 path=ROOT/'Exports'/version/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 meshes={};curves={};lighting={}
 def sockets(nodes):return [(n.name,n.bl_idname,[(i.name,repr(i.default_value[:]) if hasattr(i.default_value,'__len__') else repr(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in nodes]
 for ob in bpy.data.objects:
  if ob.type=='MESH':
   m=ob.data;h=hashlib.sha256(arr(m.vertices,'','co',3).tobytes()+np.array(ob.matrix_world,np.float32).tobytes()+repr([tuple(f.vertices) for f in m.polygons]).encode())
   for uv in m.uv_layers:h.update(np.array([v.uv[:] for v in uv.data],np.float32).tobytes())
   if m.shape_keys:
    for k in m.shape_keys.key_blocks:h.update(arr(k.data,'','co',3).tobytes()+repr((k.name,k.value)).encode())
   meshes[ob.name]=h.hexdigest()
  elif ob.type=='CURVES' and not ob.hide_render:
   cu=ob.data;p=arr(cu.attributes['position'].data,'','vector',3);r=arr(cu.attributes['radius'].data,'','value',1)
   assert np.isfinite(p).all() and np.isfinite(r).all() and (r>0).all(),ob.name
   curves[ob.name]=(p,r,np.array([c.points_length for c in cu.curves]),np.array(ob.matrix_world,np.float32))
  elif material_only and ob.type=='LIGHT':
   l=ob.data;lighting[ob.name]=repr((np.array(ob.matrix_world).tolist(),l.type,l.energy,tuple(l.color),getattr(l,'size',None),sockets(l.node_tree.nodes) if l.use_nodes else []))
  elif material_only and ob.type=='CAMERA':lighting[ob.name]=repr((np.array(ob.matrix_world).tolist(),ob.data.type,ob.data.lens,ob.data.ortho_scale))
 if material_only:
  s=bpy.context.scene;w=s.world;lighting['world']=repr((tuple(w.color),sockets(w.node_tree.nodes) if w.use_nodes else []));lighting['display']=repr((s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma))
 missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing,missing
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
 return digest,meshes,curves,lighting
beforehash,beforemesh,before,beforelight=state(base);afterhash,aftermesh,after,afterlight=state(candidate)
nape_result={}
assert beforemesh==aftermesh and set(before)==set(after)
if material_only:assert beforelight==afterlight
for name,(p,r,sizes,transform) in after.items():
 bp,br,bs,bt=before[name];assert np.array_equal(r,br) and np.array_equal(sizes,bs) and np.array_equal(transform,bt),name
 if name!=edited:assert np.array_equal(p,bp),name
 else:
  data=bpy.data.objects[name].data;mask=np.empty(len(data.curves),bool);data.attributes[attr].data.foreach_get('value',mask)
  assert (sizes==sizes[0]).all();n=int(sizes[0]);bp=bp.reshape(-1,n,3);p=p.reshape(-1,n,3)
  assert np.array_equal(p[:,0],bp[:,0]) and np.array_equal(p[~mask],bp[~mask])
  changed=int(mask.sum());delta=np.linalg.norm(p-bp,axis=2);maximum=float(delta.max())
  if material_only:assert np.array_equal(p,bp)
  if nape_profile:
   assert np.array_equal(p[:,:4],bp[:,:4])
   frame=np.empty(len(data.curves),bool);data.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
   assert np.array_equal(p[frame],bp[frame])
   remaining=int((p[:,-1,2]<1.640).sum())
   if no_long_tails:assert remaining==0,remaining
   nape_result=dict(first_four_points_exact=True,explicit_front_frame_exact=True,explicit_front_frame_fibers=int(frame.sum()),source_min_primary_tip_z_m=float(bp[:,-1,2].min()),candidate_min_primary_tip_z_m=float(p[:,-1,2].min()),primary_tips_below_1_640m=remaining,no_long_tail_gate=no_long_tails)
report=dict(source=base,source_sha256=beforehash,candidate=candidate,candidate_sha256=afterhash,mesh_count=len(beforemesh),mesh_geometry_uv_shape_keys_transforms_exact=True,visible_native_objects=len(after),curves_finite_radii_positive_textures_available=True,edited_object=edited,edited_fibers=changed,all_radii_topology_transforms_exact=True,all_roots_exact=True,unselected_fibers_exact=True,other_native_objects_exact=True,max_displacement_m=maximum,scope='Static localized file comparison. Not art, segment/body/eye/clothing/animation collision acceptance.')
if material_only:report.update(material_only=True,selection_fibers=changed,edited_fibers=0,all_visible_native_geometry_exact=True,light_world_camera_display_exact=True)
if nape_profile:report.update(nape_profile=nape_result)
out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('LOCAL_NATIVE_HAIR_EDIT_PASS',candidate,flush=True)
