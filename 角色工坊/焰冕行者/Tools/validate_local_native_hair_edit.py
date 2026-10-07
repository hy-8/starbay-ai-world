"""Compare explicit localized native edits, including untouched fiber subsets."""
import bpy,sys,json,hashlib,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];output,base,candidate,edited,attr=a[:5]
material_only='--material-only' in a
nape_profile='--nape-profile' in a
entry_profile='--entry-profile' in a
tip_profile='--tip-profile' in a
fringe_profile='--fringe-profile' in a
scene_materials_exact='--scene-materials-exact' in a
no_long_tails='--no-long-tails' in a
material_scope='support' if '--material-scope-support' in a else 'primary' if '--material-scope-primary' in a else None
donor_version=a[a.index('--donor')+1] if '--donor' in a else None
if donor_version and not re.fullmatch('[A-Za-z0-9_-]+',donor_version):raise ValueError('Invalid donor version')
if material_scope and not material_only:raise ValueError('Material scope requires material-only comparison')
if '--material-scope-support' in a and '--material-scope-primary' in a:raise ValueError('Ambiguous material scope')
if no_long_tails and not (nape_profile or entry_profile or tip_profile or fringe_profile):raise ValueError('No-long-tail gate requires nape/entry/tip/fringe profile comparison')
if not all(re.fullmatch('[A-Za-z0-9_.-]+',x) for x in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/output
if out.exists():raise RuntimeError('Fresh local audit required')
def arr(data,key,member,n):
 v=np.empty((len(data),n),np.float32) if n>1 else np.empty(len(data),np.float32)
 data.foreach_get(member,v.ravel());return v
def state(version):
 path=ROOT/'Exports'/version/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 meshes={};curves={};lighting={};materials={}
 def sockets(nodes):return [(n.name,n.bl_idname,[(i.name,repr(i.default_value[:]) if hasattr(i.default_value,'__len__') else repr(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in nodes]
 def material_graph(mat):
  if mat is None:return None
  nodes=[]
  if mat.use_nodes:
   for node in mat.node_tree.nodes:
    props={key:repr(getattr(node,key)) for key in ['model','parametrization','component','operation','blend_type','is_active_output'] if hasattr(node,key)}
    if node.type=='VALTORGB':props['ramp']=repr((node.color_ramp.interpolation,[(e.position,tuple(e.color)) for e in node.color_ramp.elements]))
    if node.type=='TEX_IMAGE':props['image']=repr((node.image.name,node.image.filepath)) if node.image else None
    nodes.append((node.name,props))
   links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links)
   return repr((sockets(sorted(mat.node_tree.nodes,key=lambda n:n.name)),sorted(nodes),links))
  return repr((False,tuple(mat.diffuse_color),mat.roughness,mat.metallic))
 for ob in bpy.data.objects:
  if (material_scope or scene_materials_exact) and (ob.type=='MESH' or (ob.type=='CURVES' and not ob.hide_render)):
   materials[ob.name]=tuple(material_graph(slot.material) for slot in ob.material_slots)
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
  elif (material_only or scene_materials_exact) and ob.type=='LIGHT':
   l=ob.data;lighting[ob.name]=repr((np.array(ob.matrix_world).tolist(),l.type,l.energy,tuple(l.color),getattr(l,'size',None),sockets(l.node_tree.nodes) if l.use_nodes else []))
  elif (material_only or scene_materials_exact) and ob.type=='CAMERA':lighting[ob.name]=repr((np.array(ob.matrix_world).tolist(),ob.data.type,ob.data.lens,ob.data.ortho_scale))
 if material_only or scene_materials_exact:
  s=bpy.context.scene;w=s.world;lighting['world']=repr((tuple(w.color),sockets(w.node_tree.nodes) if w.use_nodes else []));lighting['display']=repr((s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma))
 missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing,missing
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
 return digest,meshes,curves,lighting,materials
beforehash,beforemesh,before,beforelight,beforematerials=state(base);afterhash,aftermesh,after,afterlight,aftermaterials=state(candidate)
nape_result={};entry_result={};tip_result={};fringe_result={}
assert beforemesh==aftermesh and set(before)==set(after)
if material_only or scene_materials_exact:assert beforelight==afterlight
if scene_materials_exact:assert beforematerials==aftermaterials
scope_result={}
if material_scope:
 assert set(beforematerials)==set(aftermaterials)
 allowed=set(before)-{edited} if material_scope=='support' else {edited}
 changed_materials=[name for name in beforematerials if beforematerials[name]!=aftermaterials[name]]
 assert changed_materials and set(changed_materials)<=allowed,(material_scope,changed_materials)
 scope_result=dict(allowed_scope=material_scope,objects_with_changed_material_graphs=sorted(changed_materials),all_disallowed_material_slots_and_graphs_exact=True,mesh_material_slots_and_graphs_exact=True)
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
  if entry_profile:
   assert n==65 and np.array_equal(p[:,16:],bp[:,16:])
   remaining=int((p[:,-1,2]<1.640).sum())
   if no_long_tails:assert remaining==0,remaining
   entry_result=dict(all_points_index16_through64_exact=True,all_true_follicles_exact=True,first_four_intentionally_allowed_to_change=True,changed_shafts_in_first_four=int((np.linalg.norm(p[:,:4]-bp[:,:4],axis=2).max(axis=1)>0).sum()),minimum_primary_tip_z_m=float(p[:,-1,2].min()),primary_tips_below_1_640m=remaining,no_long_tail_gate=no_long_tails)
  if tip_profile:
   frame=np.empty(len(data.curves),bool);data.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
   assert n==65 and np.array_equal(p[frame],bp[frame])
   remaining=int((p[:,-1,2]<1.640).sum())
   if no_long_tails:assert remaining==0,remaining
   tip_result=dict(explicit_foreground_exact=True,explicit_foreground_fibers=int(frame.sum()),all_true_follicles_exact=True,first_four_intentionally_allowed_to_change=True,minimum_primary_tip_z_m=float(p[:,-1,2].min()),primary_tips_below_1_640m=remaining,no_long_tail_gate=no_long_tails)
  if fringe_profile:
   assert n==65
   frame=np.empty(len(data.curves),bool);data.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
   actual_changed=np.any(p!=bp,axis=(1,2))
   assert np.any(actual_changed&frame), 'Fringe profile requires an actual foreground edit'
   remaining=int((p[:,-1,2]<1.640).sum())
   if no_long_tails:assert remaining==0,remaining
   fringe_result=dict(old61_foreground_fibers=int(frame.sum()),actually_changed_old61_foreground_fibers=int((actual_changed&frame).sum()),
    actually_changed_other_primary_fibers=int((actual_changed&~frame).sum()),all_true_follicles_exact=True,
    minimum_primary_tip_z_m=float(p[:,-1,2].min()),primary_tips_below_1_640m=remaining,no_long_tail_gate=no_long_tails,
    scope='Foreground edit intentionally allowed; no assertion that old61 foreground geometry is unchanged. Static file counts, not art or continuous collision acceptance.')
report=dict(source=base,source_sha256=beforehash,candidate=candidate,candidate_sha256=afterhash,mesh_count=len(beforemesh),mesh_geometry_uv_shape_keys_transforms_exact=True,visible_native_objects=len(after),curves_finite_radii_positive_textures_available=True,edited_object=edited,edited_fibers=changed,all_radii_topology_transforms_exact=True,all_roots_exact=True,unselected_fibers_exact=True,other_native_objects_exact=True,max_displacement_m=maximum,scope='Static localized file comparison. Not art, segment/body/eye/clothing/animation collision acceptance.')
if material_only:report.update(material_only=True,selection_fibers=changed,edited_fibers=0,all_visible_native_geometry_exact=True,light_world_camera_display_exact=True)
if nape_profile:report.update(nape_profile=nape_result)
if entry_profile:report.update(entry_profile=entry_result)
if tip_profile:report.update(tip_profile=tip_result)
if fringe_profile:report.update(fringe_profile=fringe_result)
if scene_materials_exact:report.update(all_material_slots_graphs_exact=True,light_world_camera_display_exact=True)
if material_scope:report.update(material_scope_comparison=scope_result)
if donor_version:
 donorhash,donormesh,donorcurves,donorlight,donormaterials=state(donor_version)
 dp,dr,ds,dt=donorcurves[edited];ap,ar,ass,at=after[edited]
 assert np.array_equal(ar,dr) and np.array_equal(ass,ds) and np.array_equal(at,dt)
 assert np.array_equal(ap.reshape(-1,n,3)[mask],dp.reshape(-1,n,3)[mask])
 report.update(donor=donor_version,donor_sha256=donorhash,selected_saved_paths_exact_to_donor=True,all_radii_topology_transforms_exact_to_donor=True)
out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('LOCAL_NATIVE_HAIR_EDIT_PASS',candidate,flush=True)
