"""Independent saved-file checks for intentional mixed-topology donor restoration."""
import bpy,sys,json,hashlib,ast
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];base,candidate,reportname=a[:3]
out=ROOT/'Exports'/reportname;assert not out.exists()
# Reuse the established mesh/material snapshot, including hidden support geometry.
source=(ROOT/'Tools/validate_local_native_hair_edit.py').read_text(encoding='utf-8')
tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['arr','state']]
code='\n'.join(ast.unparse(n) for n in functions).replace("ob.type == 'CURVES' and (not ob.hide_render)","ob.type == 'CURVES'")
if '--resolve-image-paths' in a:
 code=code.replace('node.image.filepath)', 'str(Path(bpy.path.abspath(node.image.filepath)).resolve()))')
material_scope=None;scene_materials_exact=True;material_only=False
exec(compile(code,'shared_snapshot','exec'))
primary='Bystedt layercut derivative • native root reflow'
if '--support-reflow' in a:primary='Abhay flow derivative • real scalp sampled short support'
support='Original posterior coverage • surface-grown short fibers'
def attrs(cu):
 result={}
 for attr in cu.attributes:
  if attr.domain!='CURVE':continue
  member,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attr.data_type]
  v=np.empty(len(attr.data)*width,dtype);attr.data.foreach_get(member,v)
  result[attr.name]=(attr.data_type,v)
 return result
before=state(base);beforeattrs=attrs(bpy.data.objects[primary].data)
beforevisibility={o.name:o.hide_render for o in bpy.data.objects}
after=state(candidate);afterattrs=attrs(bpy.data.objects[primary].data)
aftervisibility={o.name:o.hide_render for o in bpy.data.objects}
for index,label in [(1,'meshes'),(3,'lighting'),(4,'materials')]:
 if before[index]!=after[index]:
  changed={k:dict(before=before[index].get(k),after=after[index].get(k)) for k in set(before[index])|set(after[index]) if before[index].get(k)!=after[index].get(k)}
  (ROOT/'Exports'/(reportname+'.mismatch.json')).write_text(json.dumps({label:changed},indent=2),encoding='utf-8')
  raise AssertionError((label,list(changed)))
assert set(before[2])==set(after[2]) and set(beforevisibility)==set(aftervisibility)
for name,v in beforevisibility.items():assert aftervisibility[name]==(True if name==support else v)
for name,data in before[2].items():
 if name!=primary:
  assert all(np.array_equal(x,y) for x,y in zip(data,after[2][name])),name
retained=None
if '--remove' in a:
 retained=np.load(ROOT/'Exports'/candidate/'local_retained_indices.npz')['retained'];assert retained.ndim==1 and len(retained)>0 and np.all(np.diff(retained)>0)
 assert retained.min()>=0 and retained.max()<len(before[2][primary][2])
for name,(kind,values) in beforeattrs.items():
 if retained is not None:values=values.reshape(len(before[2][primary][2]),-1)[retained].ravel()
 assert kind==afterattrs[name][0] and np.array_equal(values,afterattrs[name][1]),name
bp,br,bs,bt=before[2][primary];ap,ar,asz,at=after[2][primary]
assert np.array_equal(bt,at)
if retained is not None:
 keep=np.zeros(len(bs),bool);keep[retained]=True;pointkeep=np.repeat(keep,bs)
 assert np.array_equal(bp[pointkeep],ap) and np.array_equal(br[pointkeep],ar) and np.array_equal(bs[keep],asz)
 assert not beforeattrs['native_inner_curtain_shift'][1][~keep].any()
 manifest=json.loads((ROOT/'Exports'/candidate/'stray_removal_manifest.json').read_text());assert manifest['model_sha256']==after[0] and manifest['source_sha256']==before[0] and manifest['removed_fibers']==int((~keep).sum())
 selected=np.load(ROOT/'Renders'/manifest['selection']/'local_projected_indices.npz')['selected'];assert np.array_equal(np.flatnonzero(~keep),selected)
 result=dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],mesh_count=len(before[1]),meshes_uv_shape_keys_transforms_exact=True,other_native_geometry_exact=True,material_light_world_camera_display_exact=True,image_paths_compared_as_resolved_absolute='--resolve-image-paths' in a,retained_curve_history_exact=True,retained_positions_radii_counts_transforms_exact=True,accepted_inner_curtain_retained=True,removed_fibers=len(selected),retained_fibers=len(retained),scope='Independent saved-file mixed-count deletion comparison to exact local inspected selection. Count/topology intentionally reduced;all retained fibers exact. Not artistic or collision acceptance.')
 out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('STRAY_REMOVAL_AUDIT_PASS',candidate,flush=True);sys.exit(0)
assert len(bs)==len(asz)
if '--support-reflow' in a:
 mask=afterattrs['native_recombed_rear_support'][1]
 assert np.array_equal(bs,asz) and np.array_equal(br,ar)
 offsets=np.r_[0,np.cumsum(bs)];roots=bp[offsets[:-1]]
 manifest=json.loads((ROOT/'Exports'/candidate/'support_reflow_manifest.json').read_text())
 selected=np.load(ROOT/'Renders'/manifest['selection']/'local_projected_indices.npz')['selected']
 expected=np.zeros(len(bs),bool);expected[selected]=True;expected&=(roots[:,0]<-.015)&(roots[:,1]>-.025)
 assert np.array_equal(mask,expected)
 retained_root_controls=0
 for i in range(len(bs)):
  old=bp[offsets[i]:offsets[i+1]];p=ap[offsets[i]:offsets[i+1]]
  assert np.array_equal(old[0],p[0])
  if not mask[i]:assert np.array_equal(old,p)
  else:
   arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))];protected=arc<=.008
   assert np.array_equal(old[protected],p[protected]);retained_root_controls+=int(protected.sum())
 delta=float(np.linalg.norm(ap-bp,axis=1).max());assert np.isfinite(ap).all() and delta>0
 from mathutils import Vector
 from mathutils.bvhtree import BVHTree
 bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
 changed=np.linalg.norm(ap-bp,axis=1)>1e-8;gaps=[]
 for point in ap[changed]:
  h,n,_,_=bv.find_nearest(Vector(point));gaps.append(float((Vector(point)-h).dot(n)))
 assert min(gaps)>.00045 and float(ap[changed,2].min())>=float(bp[:,2].min())-1e-6
 assert abs(delta-manifest['max_same_index_displacement_m'])<1e-6
 assert manifest['model_sha256']==after[0] and manifest['source_sha256']==before[0] and manifest['selected_fibers']==int(mask.sum())
 result=dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],mesh_count=len(before[1]),meshes_uv_shape_keys_transforms_exact=True,all_other_native_geometry_exact=True,material_light_world_camera_display_exact=True,image_paths_compared_as_resolved_absolute='--resolve-image-paths' in a,historical_curve_attributes_exact=True,all_radii_point_counts_transforms_exact=True,all_roots_exact=True,unselected_fibers_exact=int((~mask).sum()),selected_fibers=int(mask.sum()),root_arc8mm_controls_exact=retained_root_controls,max_same_index_displacement_m=delta,scope='Independent saved-file support-only deformation and exact projected selection/filter verification. Main hair including accepted part,other supports and meshes unchanged. Static audit,not artistic or continuous collision acceptance.')
 result.update(changed_controls_signed_body_gap_quantiles_m=np.quantile(gaps,[0,.5,1]).tolist(),changed_controls_min_z_m=float(ap[changed,2].min()),short_arc_budget=manifest.get('short_arc_budget'),scalp_fit=manifest.get('scalp_fit',False))
 if manifest.get('scalp_fit'):
  tail_gaps=[]
  for i in np.flatnonzero(mask):
   old=bp[offsets[i]:offsets[i+1]];p=ap[offsets[i]:offsets[i+1]]
   arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
   target=min(float(arc[-1]),.045,max(.014,float(old[0,2]-1.790)))
   mapped=np.minimum(arc,.008)+np.maximum(arc-.008,0)*(target-.008)/max(float(arc[-1])-.008,1e-9)
   for point in p[mapped>=.022]:
    h,n,_,_=bv.find_nearest(Vector(point));tail_gaps.append(float((Vector(point)-h).dot(n)))
  assert tail_gaps and max(tail_gaps)<=.0033
  result.update(fully_transitioned_controls=len(tail_gaps),fully_transitioned_signed_gap_quantiles_m=np.quantile(tail_gaps,[0,.5,1]).tolist())
 out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('SUPPORT_REFLOW_AUDIT_PASS',candidate,flush=True);sys.exit(0)
if '--channels' in a:
 mask=afterattrs['native_sweep_channels'][1];assert np.array_equal(bs,asz) and np.array_equal(br,ar)
 assert not np.any(beforeattrs['native_inner_curtain_shift'][1][mask])
 offsets=np.r_[0,np.cumsum(bs)];selected=[]
 for i in range(len(bs)):
  old=bp[offsets[i]:offsets[i+1]];p=ap[offsets[i]:offsets[i+1]]
  assert np.array_equal(old[0],p[0])
  if not mask[i]:assert np.array_equal(old,p)
  else:
   assert bs[i]==65 and np.array_equal(old[:8],p[:8]) and np.array_equal(old[56:],p[56:]);selected.append(i)
 delta=float(np.linalg.norm(ap-bp,axis=1).max());assert 0<delta<=.004001
 manifest=json.loads((ROOT/'Exports'/candidate/'sweep_channels_manifest.json').read_text())
 assert manifest['model_sha256']==after[0] and manifest['source_sha256']==before[0] and manifest['selected_fibers']==len(selected)
 result=dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],mesh_count=len(before[1]),meshes_uv_shape_keys_transforms_exact=True,other_native_geometry_exact=True,material_light_world_camera_display_exact=True,image_paths_compared_as_resolved_absolute='--resolve-image-paths' in a,historical_curve_attributes_exact=True,all_radii_point_counts_transforms_exact=True,all_roots_exact=True,unselected_fibers_exact=int((~mask).sum()),selected_fibers=len(selected),first8_last9_controls_exact=True,max_same_index_displacement_m=delta,scope='Independent saved mixed-control localized deformation audit. Material image paths resolved to original absolute files after drive change. Static comparison only;not artistic or continuous collision acceptance.')
 out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('CHANNELS_AUDIT_PASS',candidate,flush=True);sys.exit(0)
if '--trim' in a or '--accent' in a or '--layer-trim' in a:
 accent='--accent' in a
 layered='--layer-trim' in a
 mask=afterattrs['native_raw_rear_layers' if layered else 'native_trimmed_outer_accent' if accent else 'native_rounded_nape'][1]
 if accent:assert not np.any(beforeattrs['native_inner_curtain_shift'][1][mask])
 else:assert np.all(beforeattrs['native_restored_raw_controls'][1][mask])
 bo=np.r_[0,np.cumsum(bs)];ao=np.r_[0,np.cumsum(asz)];cuts=[]
 for i in range(len(bs)):
  p=ap[ao[i]:ao[i+1]];r=ar[ao[i]:ao[i+1]];old=bp[bo[i]:bo[i+1]];rad=br[bo[i]:bo[i+1]]
  if not mask[i]:assert np.array_equal(p,old) and np.array_equal(r,rad);continue
  assert np.array_equal(p[0],old[0]) and np.array_equal(p[:-1],old[:len(p)-1])
  if accent:assert len(p)<len(old) and np.array_equal(p,old[:len(p)])
  j=len(p)-1;v=old[j]-old[j-1];t=float(np.dot(p[-1]-old[j-1],v)/np.dot(v,v))
  assert -1e-5<=t<=1.00001 and np.linalg.norm(p[-1]-(old[j-1]+t*v))<2e-7
  expected=rad[:len(p)].copy();k=min(4,len(expected)-1);f=np.linspace(0,1,k);expected[-k:]*=1-.99*f**1.4
  assert np.array_equal(r,expected)
  oldlength=float(np.linalg.norm(np.diff(old,axis=0),axis=1).sum());newlength=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
  cuts.append(oldlength-newlength)
  if layered:assert .00099<cuts[-1]<.03501 and cuts[-1]<=oldlength*.26001
  elif not accent:assert .00099<cuts[-1]<.03201 and cuts[-1]<=oldlength*.22001
 manifest=json.loads((ROOT/'Exports'/candidate/('outer_accent_manifest.json' if accent else 'rounded_nape_manifest.json')).read_text())
 assert manifest['model_sha256']==after[0] and manifest['source_sha256']==before[0] and manifest['trimmed_fibers' if accent else 'selected_fibers']==int(mask.sum())
 result=dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],mesh_count=len(before[1]),meshes_uv_shape_keys_transforms_exact=True,other_native_geometry_exact=True,material_light_world_camera_display_exact=True,historical_curve_attributes_exact=True,unchanged_fibers_paths_radii_counts_exact=int((~mask).sum()),trimmed_fibers=int(mask.sum()),all_current_roots_exact=True,trimmed_control_prefixes_exact=True,terminal_points_on_source_segments=True,intentional_terminal_taper_verified=True,polyline_shortening_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist(),scope='Independent saved mixed-control trim comparison. Selected point counts and terminal radii intentionally change. Not art or continuous collision proof.')
 out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('RAW_TRIM_AUDIT_PASS',candidate,flush=True);sys.exit(0)
assert (bs==65).all()
bp=bp.reshape(-1,65,3);br=br.reshape(-1,65)
offset=np.r_[0,np.cumsum(asz)]
mapping=np.load(ROOT/'Exports/nativefocusedpart177/local_retained_indices.npz')['retained']
assert np.array_equal(afterattrs['native_original_donor_index'][1],mapping)
rawmask=afterattrs['native_restored_raw_controls'][1]
donorpath=ROOT/'Exports/layercut04/Ember_Regent.blend';donorhash=hashlib.sha256(donorpath.read_bytes()).hexdigest()
with bpy.data.libraries.load(str(donorpath),link=False) as (src,dst):dst.objects=['Daniel Bystedt adapted layered cut • CC BY-SA']
d=dst.objects[0];assert np.array_equal(np.array(d.matrix_world),np.eye(4))
cu=d.data;dp=arr(cu.attributes['position'].data,'','vector',3);dr=arr(cu.attributes['radius'].data,'','value',1)
ds=np.array([c.points_length for c in cu.curves]);doff=np.r_[0,np.cumsum(ds)]
protected=beforeattrs['native_resculpted_fringe_sweeps'][1]|beforeattrs['native_inner_curtain_shift'][1]
protected=protected.copy()
for i,k in enumerate(mapping):
 path=dp[doff[k]:doff[k+1]]
 protected[i]|=(path[:,1].min()<-.09 or (path[0,1]<.015 and path[:,2].max()>1.880))
assert np.array_equal(rawmask,~protected)
cuts=0;rootdelta=[]
for i,k in enumerate(mapping):
 p=ap[offset[i]:offset[i+1]];r=ar[offset[i]:offset[i+1]]
 if protected[i]:
  assert np.array_equal(p,bp[i]) and np.array_equal(r,br[i]);continue
 donor=dp[doff[k]:doff[k+1]];radii=dr[doff[k]:doff[k+1]]
 assert np.array_equal(p[0],donor[0])
 rootdelta.append(float(np.linalg.norm(p[0]-bp[i,0])))
 floor=1.681+.010*np.sin(donor[0,0]*83+donor[0,1]*67)+.007*np.clip(abs(donor[0,0])/.09,0,1)
 cross=np.flatnonzero(donor[:,2]<floor)
 if not len(cross):
  assert np.array_equal(p,donor) and np.array_equal(r,radii);continue
 cuts+=1;j=int(cross[0])
 if j==0:
  assert len(p)==2 and np.isclose(r[-1],radii[0]*.01,rtol=1e-6)
  assert r[0]==radii[0]
  v=donor[1]-donor[0];t=float(np.dot(p[1]-donor[0],v)/np.dot(v,v))
  assert -1e-5<=t<=1.00001 and np.linalg.norm(p[1]-(donor[0]+t*v))<2e-7
  assert abs(np.linalg.norm(p[1]-p[0])-min(.004,np.linalg.norm(v)))<2e-7
 else:
  assert len(p)==j+1 and np.array_equal(p[:-1],donor[:j])
  v=donor[j]-donor[j-1];t=float(np.dot(p[-1]-donor[j-1],v)/np.dot(v,v))
  assert -1e-5<=t<=1.00001 and np.linalg.norm(p[-1]-(donor[j-1]+t*v))<2e-7
  assert abs(p[-1,2]-floor)<2e-7
  expected=radii[:j+1].copy();f=np.linspace(0,1,min(4,len(expected)));expected[-len(f):]*=1-.99*f**1.4
  assert np.array_equal(r,expected)
manifest=json.loads((ROOT/'Exports'/candidate/'raw_control_manifest.json').read_text())
assert manifest['model_sha256']==after[0] and manifest['source_sha256']==before[0] and manifest['donor_sha256']==donorhash
assert cuts==manifest['trimmed_fibers']
result=dict(source=base,source_sha256=before[0],candidate=candidate,candidate_sha256=after[0],donor_sha256=donorhash,mesh_count=len(before[1]),meshes_uv_shape_keys_transforms_exact=True,other_native_geometry_exact=True,material_light_world_camera_display_exact=True,historical_curve_attributes_exact=True,protected_current_paths_radii_counts_exact=int(protected.sum()),restored_original_control_paths=int(rawmask.sum()),clipped_paths=cuts,restored_roots_exact_to_donor=True,source_root_delta_quantiles_m=np.quantile(rootdelta,[0,.5,1]).tolist(),raw_prefixes_exact_terminal_on_original_segment=True,intentional_terminal_taper_verified=True,original_posterior_support_render_hidden_only=True,scope='Independent saved-file structural comparison. Topology and some roots intentionally differ from current source. Does not prove art quality or continuous body/eye/clothing/animation collision safety.')
out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('RAW_CONTROL_AUDIT_PASS',candidate,flush=True)
