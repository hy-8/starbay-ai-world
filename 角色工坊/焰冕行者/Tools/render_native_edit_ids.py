"""Actual temporary edited/untouched hair IDs, with no saved-source mutation."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,attribute=a[:3]
edited_object=a[a.index('--object')+1] if '--object' in a else 'Bystedt layercut derivative • native root reflow'
crown='--crown-peaks' in a
front_views='--front-views' in a
rear_subset='--rear-subset' in a
projection_camera=a[a.index('--projection-camera')+1] if '--projection-camera' in a else '02_ThreeQuarter'
ellipse=[float(x) for x in a[a.index('--ellipse')+1].split(',')] if '--ellipse' in a else None
if ellipse:assert len(ellipse)==4 and ellipse[2]>0 and ellipse[3]>0 and not crown
assert not rear_subset or (not crown and not ellipse)
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Renders'/version
if out.exists():raise RuntimeError('Fresh ID renders required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
edited_ob=bpy.data.objects[edited_object];assert edited_ob.type=='CURVES' and not edited_ob.hide_render
def emission(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear();e=m.node_tree.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1);e.inputs['Strength'].default_value=1
 o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs[0]);return m
gray=emission('ID body',(.06,.06,.06));support=emission('ID support',(0,1,.08))
for ob in bpy.data.objects:
 if ob.type=='MESH' and not ob.hide_render:
  for slot in ob.material_slots:slot.material=gray
 elif ob.type=='CURVES' and not ob.hide_render and ob!=edited_ob:
  ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(support)
ob=edited_ob;cu=ob.data;mask=np.empty(len(cu.curves),bool)
counts=np.array([c.points_length for c in cu.curves]);N=int(counts[0]) if (counts==counts[0]).all() else None
if not crown and not ellipse:cu.attributes[attribute].data.foreach_get('value',mask)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
if rear_subset:
 starts=np.r_[0,np.cumsum(counts)[:-1]];ends=np.cumsum(counts)-1
 mask&=(p[starts,1]>-.030)&(p[ends,1]>.015)&(p[ends,2]<1.800)
if crown:mask=np.maximum.reduceat(p[:,2],np.r_[0,np.cumsum(counts)[:-1]])>1.875
if ellipse:
 cam=bpy.data.objects[projection_camera];view=np.array(cam.matrix_world.inverted());proj=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
 world=np.c_[p,np.ones(len(p))]@np.array(ob.matrix_world).T;local=world@view.T;clip=local@proj.T;ndc=clip[:,:3]/clip[:,3,None]
 xx=ndc[:,0]*.5+.5;yy=.5-ndc[:,1]*.5;cx,cy,rx,ry=ellipse
 hit=(((xx-cx)/rx)**2+((yy-cy)/ry)**2<1)&(local[:,2]<0)
 mask=np.add.reduceat(hit.astype(np.int32),np.r_[0,np.cumsum(counts)[:-1]])>=2
r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
for selected,color,name in [(True,(.04,.16,1),'Edited native shafts'),(False,(1,.03,.07),'Untouched native shafts')]:
 rows=mask==selected;points=np.repeat(rows,counts);new=bpy.data.hair_curves.new(name);new.add_curves(counts[rows].tolist());new.attributes['position'].data.foreach_set('vector',p[points].ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',r[points]);new.materials.append(emission(name,color))
 item=bpy.data.objects.new(name,new);bpy.context.scene.collection.objects.link(item);item.matrix_world=ob.matrix_world
ob.hide_render=True
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80;s.view_settings.view_transform='Standard';out.mkdir(parents=True)
if ellipse:np.savez_compressed(out/'local_projected_indices.npz',selected=np.flatnonzero(mask))
for name in (['02_ThreeQuarter','01_Front'] if front_views else ['04_Back','03_Side']):
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
selection_parameters=dict(projection_camera=projection_camera if ellipse else None,rear_subset=rear_subset,rear_subset_rule='attribute AND rootY>-30mm AND tipY>15mm AND tipZ<1.800m' if rear_subset else None)
(out/'selection_parameters.json').write_text(json.dumps(selection_parameters,indent=2),encoding='utf-8')
(out/'edit_id_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,edited_object=edited_object,points_per_curve=N,selection_attribute=None if crown or ellipse else attribute,selection_rule={'camera':projection_camera,'normalized_ellipse':ellipse,'minimum_projected_controls':2} if ellipse else 'Selected object shaft maximum z>1.875m' if crown else (dict(attribute=attribute,filter=selection_parameters['rear_subset_rule']) if rear_subset else attribute),legend={'blue':'High crown selected-object shafts' if crown else 'Edited selected-object curves','red':'Other selected-object shafts' if crown else 'Untouched selected-object curves','green':'All other visible native hair components','gray':'Body/clothes'},edited_fibers=int(mask.sum()),unselected_fibers=int((~mask).sum()),method='Exact temporary curve subsets with original radii/matrix, actual cameras, emission diagnostic only. Ellipse is projected controls, not continuous visibility proof.',status='Unreviewed actual component diagnostic'),indent=2),encoding='utf-8');print('NATIVE_EDIT_IDS_RENDERED',version,flush=True)
