"""Trim a visually inspected outer accent using retained mixed control prefixes."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,idsversion=a[:3]
save='--save-archive' in a;save_only='--save-only' in a;assert not save_only or save
attribute=a[a.index('--attribute')+1] if '--attribute' in a else 'native_trimmed_outer_accent'
assert re.fullmatch('[A-Za-z0-9_]+',attribute)
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
idroot=ROOT/'Renders'/idsversion;idmanifest=json.loads((idroot/'edit_id_manifest.json').read_text());assert idmanifest['source_sha256']==digest
selected=np.load(idroot/'local_projected_indices.npz')['selected'];ellipse=idmanifest['selection_rule']['ThreeQuarter_normalized_ellipse']
out=ROOT/'Renders'/version;assert not out.exists()
md=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
if save:assert not md.exists() and not (ROOT/'Exports'/version).exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert attribute not in cu.attributes,'Use a fresh operation attribute to preserve historical selections'
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());r=np.empty(len(p),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
cam=bpy.data.objects['02_ThreeQuarter'];view=np.array(cam.matrix_world.inverted());proj=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
world=np.c_[p,np.ones(len(p))]@np.array(ob.matrix_world).T;local=world@view.T;clip=local@proj.T;ndc=clip[:,:3]/clip[:,3,None]
xx=ndc[:,0]*.5+.5;yy=.5-ndc[:,1]*.5;cx,cy,rx,ry=ellipse;hit=(((xx-cx)/rx)**2+((yy-cy)/ry)**2<1)&(local[:,2]<0)
accepted=np.empty(len(sizes),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',accepted)
paths=[];radii=[];mask=np.zeros(len(sizes),bool);selectedset=set(selected.tolist());cuts=[];skipped=[]
for i in range(len(sizes)):
 path=p[off[i]:off[i+1]].copy();rad=r[off[i]:off[i+1]].copy()
 if i in selectedset and not accepted[i]:
  matches=np.flatnonzero(hit[off[i]:off[i+1]]);j=int(matches[0])
  if j>=3:
   oldlength=np.linalg.norm(np.diff(path,axis=0),axis=1).sum();path=path[:j];rad=rad[:j]
   taper=np.linspace(0,1,min(4,len(rad)-1));rad[-len(taper):]*=1-.99*taper**1.4
   cuts.append(float(oldlength-np.linalg.norm(np.diff(path,axis=0),axis=1).sum()));mask[i]=True
  else:skipped.append(i)
 paths.append(path);radii.append(rad)
new=bpy.data.hair_curves.new('Mixed native controls with trimmed outer accent');new.add_curves([len(x) for x in paths]);new.attributes['position'].data.foreach_set('vector',np.concatenate(paths).ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(radii));new.materials.append(cu.materials[0])
for attr in cu.attributes:
 if attr.domain!='CURVE':continue
 field,width,dtype={'BOOLEAN':('value',1,bool),'INT':('value',1,np.int32),'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[attr.data_type]
 values=np.empty(len(attr.data)*width,dtype);attr.data.foreach_get(field,values);target=new.attributes.get(attr.name) or new.attributes.new(attr.name,attr.data_type,'CURVE');target.data.foreach_set(field,values)
new.attributes.new(attribute,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data=new
modelhash=None
if save:
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ([] if save_only else ['02_ThreeQuarter','03_Side']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,source_unchanged=True,model_saved=save,model_sha256=modelhash,archive_model_path=str(md/'Ember_Regent.blend') if save else None,operation_attribute=attribute,source_id_version=idsversion,selection_ellipse=ellipse,selected_fibers=len(selected),trimmed_fibers=int(mask.sum()),too_early_to_trim=len(skipped),accepted_fringe_selected=int(accepted[selected].sum()),polyline_cut_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist() if cuts else [],images_sha256=images,method='Trim inspected projected outer accent to last original control before first ellipse entry, only if at least3 controls remain. Retain complete source control prefix/root, taper last<=4 radii without altering first radius. All other geometry/materials retained. Screen projection is a selection device, not continuous visibility or collision proof.')
(out/'outer_accent_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(md/'outer_accent_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('OUTER_ACCENT_TRIM',version,int(mask.sum()),flush=True)
