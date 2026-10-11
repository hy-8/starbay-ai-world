"""Saved-file comparison and evaluation of the actual scalp mask node graph."""
import bpy,sys,ast,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];base,candidate,reportname=a[:3]
out=ROOT/'Exports'/reportname;assert not out.exists()
tree=ast.parse((ROOT/'Tools/validate_local_native_hair_edit.py').read_text(encoding='utf-8'))
code='\n'.join(ast.unparse(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['arr','state']).replace("ob.type == 'CURVES' and (not ob.hide_render)","ob.type == 'CURVES'")
material_scope=None;scene_materials_exact=True;material_only=False
exec(compile(code,'shared_snapshot','exec'))
bodyname='CC0 male body • retained topology'
def node_state(n):
 vals=[(i.name,repr(i.default_value[:]) if hasattr(i.default_value,'__len__') else repr(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]
 props={k:repr(getattr(n,k)) for k in ['operation','blend_type','model','parametrization','is_active_output'] if hasattr(n,k)}
 if n.type=='VALTORGB':props['ramp']=repr((n.color_ramp.interpolation,[(e.position,tuple(e.color)) for e in n.color_ramp.elements]))
 if n.type=='TEX_IMAGE':props['image']=repr((n.image.name,n.image.filepath)) if n.image else None
 return repr((n.bl_idname,vals,props))
def original_graphs():
 return [dict(nodes={n.name:node_state(n) for n in s.material.node_tree.nodes},links={(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in s.material.node_tree.links}) for s in bpy.data.objects[bodyname].material_slots]
before=state(base);graphs=original_graphs();bv={o.name:o.hide_render for o in bpy.data.objects}
after=state(candidate);body=bpy.data.objects[bodyname]
assert before[1]==after[1] and before[3]==after[3]
assert set(before[2])==set(after[2]) and all(all(np.array_equal(x,y) for x,y in zip(before[2][n],after[2][n])) for n in before[2])
assert bv=={o.name:o.hide_render for o in bpy.data.objects}
assert {k:v for k,v in before[4].items() if k!=bodyname}=={k:v for k,v in after[4].items() if k!=bodyname}
assert before[4][bodyname]!=after[4][bodyname]
vertices=arr(body.data.vertices,'','co',3)
for slot,old in zip(body.material_slots,graphs):
 nt=slot.material.node_tree
 assert all(node_state(nt.nodes[name])==value for name,value in old['nodes'].items())
 links={(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links}
 removed=old['links']-links;assert len(removed)==1
 output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 removedlink=removed.pop();assert removedlink[2:]==(output.name,'Surface')
 mix=nt.nodes['Skin and localized follicle backing'];assert mix.inputs[1].links[0].from_node.name==removedlink[0] and mix.inputs[1].links[0].from_socket.identifier==removedlink[1]
 assert output.inputs['Surface'].links[0].from_node==mix
 coord=nt.nodes['Head-local follicle coordinates'];assert coord.object==body
 # Follow real links to spatial factor before texture modulation/strength.
 strength=mix.inputs[0].links[0].from_node
 densitymul=strength.inputs[0].links[0].from_node
 spatial=densitymul.inputs[0].links[0].from_socket
 assert strength.operation=='MULTIPLY' and abs(strength.inputs[1].default_value-.95)<1e-6
 def evaluate(socket):
  n=socket.node
  if n.type=='TEX_COORD':assert socket.name=='Object';return vertices
  if n.type=='SEPXYZ':return evaluate(n.inputs[0].links[0].from_socket)[:,{'X':0,'Y':1,'Z':2}[socket.name]]
  assert n.type=='MATH',n.type
  v=[evaluate(i.links[0].from_socket) if i.is_linked else i.default_value for i in n.inputs]
  op=n.operation
  if op=='ADD':return v[0]+v[1]
  if op=='SUBTRACT':return v[0]-v[1]
  if op=='MULTIPLY':return v[0]*v[1]
  if op=='DIVIDE':return v[0]/v[1]
  if op=='ABSOLUTE':return np.abs(v[0])
  if op=='MINIMUM':return np.minimum(v[0],v[1])
  if op=='MAXIMUM':return np.maximum(v[0],v[1])
  raise AssertionError(op)
 actual=evaluate(spatial)
 y=(vertices[:,1]+.078)/.043;z=(vertices[:,2]-1.846)/.052
 edge=np.clip((1-y*y-z*z)*2.5,0,1);expected=edge*edge*(3-2*edge)*np.clip((abs(vertices[:,0])-.019)/.023,0,1)
 assert np.allclose(actual,expected,atol=2e-5) and np.all((actual>=0)&(actual<=1))
 assert not np.any(actual[vertices[:,2]<1.794]) and not np.any(actual[abs(vertices[:,0])<.019])
active=vertices[actual>0]
manifest=json.loads((ROOT/'Exports'/candidate/'follicle_shader_manifest.json').read_text())
assert manifest['source_sha256']==before[0] and manifest['model_sha256']==after[0]
out.write_text(json.dumps(dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],mesh_count=len(before[1]),all_mesh_geometry_uv_shape_keys_transforms_exact=True,all_native_hair_positions_radii_counts_transforms_exact=True,visibility_exact=True,all_nonbody_materials_exact=True,light_world_camera_display_exact=True,original_body_shader_nodes_internal_links_exact=True,only_original_surface_output_routed_through_local_mix=True,actual_mask_graph_matches_documented_ellipse_on_body_vertices=True,body_vertices_with_nonzero_mask=len(active),active_vertex_bounds_m=[active.min(0).tolist(),active.max(0).tolist()],scope='Independent saved file and actual math-node graph comparison. Scalp material intentionally changes, hair geometry does not. Surface mask is local to body object, not UV-baked or game-export verified. Mask vertex checks do not prove final art quality or continuous animation collision.'),indent=2),encoding='utf-8');print('LOCAL_FOLLICLE_SHADER_PASS',candidate,flush=True)
