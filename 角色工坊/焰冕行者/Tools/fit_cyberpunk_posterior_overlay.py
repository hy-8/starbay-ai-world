"""Preview a posterior-only layer from existing Bystedt authored short groom.

Source: Hair Styles by Daniel Bystedt, CC BY-SA; version unspecified in evidence.
Licensed source/derived geometry remains local. No source or candidate model save.
"""
import bpy,sys,re,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
central='--central-only' in a
replacement=a[a.index('--replace-projected')+1] if '--replace-projected' in a else None
if replacement:assert central and re.fullmatch('[A-Za-z0-9_-]+',replacement)
full_section='--full-section' in a
assert not full_section or replacement
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ARCHIVE/'Renders'/version;assert not out.exists()
asset=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend';source=ROOT/'Exports'/base/'Ember_Regent.blend'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();asset_hash=digest(asset);before=digest(source)
assert asset_hash=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
hair=bpy.data.objects['cyberpunk hair'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
cu=hair.evaluated_get(dg).data
xyz=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',xyz.ravel())
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
radii=np.full(len(cu.points),.0004,np.float32)
if cu.attributes.get('radius'):cu.attributes['radius'].data.foreach_get('value',radii)
m=np.array(hair.matrix_world);xyz=(xyz@m[:3,:3].T+m[:3,3])*.1;radii=np.maximum(np.minimum(radii*.1,.000045),.000001)
head=bpy.data.objects['head'];vertices=np.array([head.matrix_world@v.co for v in head.data.vertices],float)*.1
sb=BVHTree.FromPolygons([Vector(v) for v in vertices],[list(p.vertices) for p in head.data.polygons])
cs=np.array([0,-.063,float(vertices[:,2].max())-.100]);ct=np.array([0,-.044,1.771])
rotation=np.array(Matrix.Rotation(-1.1,3,'X'));mapped=ct+(xyz-cs)@rotation.T*1.06
paths=[]
for i in range(len(sizes)):
 q=mapped[off[i]:off[i+1]];old=xyz[off[i]:off[i+1]];arc=np.linalg.norm(np.diff(old,axis=0),axis=1).sum()
 if not (.035<=arc<=.150 and q[0,1]>.020 and 1.790<q[0,2]<1.870 and np.min(q[:,1])>.010 and np.min(q[:,2])>1.735):continue
 _,n,_,_=sb.find_nearest(Vector(old[0]));paths.append((i,q.copy(),rotation@np.array(n)))
assert paths,'No eligible short source paths'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
original=bpy.data.objects['Bystedt layercut derivative • native root reflow']
def native_hash():
 h=hashlib.sha256()
 for ob in sorted([o for o in bpy.data.objects if o.type=='CURVES'],key=lambda o:o.name):
  p=np.empty(len(ob.data.points)*3,np.float32);ob.data.attributes['position'].data.foreach_get('vector',p)
  r=np.empty(len(ob.data.points),np.float32);ob.data.attributes['radius'].data.foreach_get('value',r)
  h.update(ob.name.encode());h.update(p.tobytes());h.update(r.tobytes());h.update(np.array(ob.matrix_world).tobytes());h.update(np.array([c.points_length for c in ob.data.curves]).tobytes())
 return h.hexdigest()
native_before=native_hash();kept=[];output=[];outputr=[];rejected=0;lengths=[]
for i,q,normal in paths:
 hit,n,_,distance=bv.find_nearest(Vector(q[0]))
 if distance>.035:rejected+=1;continue
 orient=np.array(Vector(normal).rotation_difference(n).to_matrix())
 p=(q-q[0])@orient.T+np.array(hit+n*.0007)
 if p[:,1].min()<=.010 or p[:,2].min()<=1.735:rejected+=1;continue
 if central and (abs(p[0,0])>=.038 or p[0,2]<=1.810 or np.abs(p[:,0]).max()>=.055):rejected+=1;continue
 samples=np.vstack([p,(p[:-1]+p[1:])*.5]);gaps=[]
 for v in samples:
  h,nn,_,_=bv.find_nearest(Vector(v));gaps.append(float((Vector(v)-h).dot(nn)))
 if min(gaps)<.0002:rejected+=1;continue
 if central and max(gaps)>.020:rejected+=1;continue
 kept.append(i);output.append(p);outputr.append(np.minimum(radii[off[i]:off[i+1]],.000030) if central else radii[off[i]:off[i+1]]);lengths.append(float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()))
assert len(output)>100,'Insufficient intact collision-free grafts'
assert native_hash()==native_before
cu=bpy.data.hair_curves.new('Bystedt short swept posterior layer • local CC BY-SA derivative');cu.add_curves([len(p) for p in output])
cu.attributes['position'].data.foreach_set('vector',np.vstack(output).astype(np.float32).ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(outputr))
cu.materials.append(original.data.materials[0]);ob=bpy.data.objects.new('Bystedt short swept posterior overlay • preview',cu);bpy.context.scene.collection.objects.link(ob)
removed=[]
if replacement:
 selection=ARCHIVE/'Renders'/replacement
 assert json.loads((selection/'edit_id_manifest.json').read_text())['source_sha256']==before
 oldcu=original.data;oldcounts=np.array([c.points_length for c in oldcu.curves]);oldoff=np.r_[0,np.cumsum(oldcounts)]
 oldp=np.empty((len(oldcu.points),3),np.float32);oldcu.attributes['position'].data.foreach_get('vector',oldp.ravel())
 oldr=np.empty(len(oldcu.points),np.float32);oldcu.attributes['radius'].data.foreach_get('value',oldr)
 remove=np.zeros(len(oldcounts),bool);remove[np.load(selection/'local_projected_indices.npz')['selected']]=True
 remove&=oldp[oldoff[1:]-1,1]>.030
 for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips','native_released_tip_clusters']:
  flags=np.empty(len(oldcounts),bool);oldcu.attributes[key].data.foreach_get('value',flags);remove&=~flags
 removed=np.flatnonzero(remove).tolist();assert 0<len(removed)<(6000 if full_section else 2000)
 if full_section:
  original.data=oldcu.copy();masked=oldr.copy();masked[np.repeat(remove,oldcounts)]=1e-9
  original.data.attributes['radius'].data.foreach_set('value',masked);original.data.update_tag()
 else:
  retained=bpy.data.hair_curves.new('Unchanged retained primary strands • replacement preview');retained.add_curves(oldcounts[~remove].tolist())
  pointmask=np.repeat(~remove,oldcounts);retained.attributes['position'].data.foreach_set('vector',oldp[pointmask].ravel());retained.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',oldr[pointmask]);retained.materials.append(original.data.materials[0])
  retainedob=bpy.data.objects.new('Retained original hair • replacement preview',retained);bpy.context.scene.collection.objects.link(retainedob);retainedob.matrix_world=original.matrix_world
  original.hide_render=True
out.mkdir(parents=True);np.savez_compressed(out/'local_source_strands.npz',selected=np.array(kept))
if replacement:np.savez_compressed(out/'local_removed_existing.npz',selected=np.array(removed))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['04_Back','05_OppositeSide','02_ThreeQuarter']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before and digest(asset)==asset_hash
report=dict(source=base,source_sha256=before,source_unchanged=True,asset_sha256=asset_hash,asset_unchanged=True,source_style='cyberpunk hair',author='Daniel Bystedt',license='CC BY-SA; version unspecified in inspected evidence',model_saved=False,source_evaluated_curves=len(sizes),eligible_short_source_curves=len(paths),added_curves=len(output),rejected_grafts=rejected,added_curve_length_m_quantiles=np.quantile(lengths,[0,.5,1]).tolist(),original_native_geometry_unchanged_before_add=True,images_sha256=images,method='Evaluate existing authored short groom with original modifiers. Scale source units0.1,rotate-1.1rad about head center X,scale1.06. Source arc35..150mm,rotated rootY>20mm,Z1.790..1.870m;all controlsY>10mm,Z>1.735m. Whole-fiber rigid translation/normal alignment to retained scalp,root clearance0.7mm. Reject entire fiber if controls/midpoints gap<0.2mm or crosses posterior gate;do not point-project individual controls. Original groom untouched beneath added layer;current main hair material,source radii scaled and capped45microns. No continuous collision or art acceptance.')
(out/'posterior_overlay_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if central:
 report['central_only']=True
 report['method']+=' Narrow overlay: additionally fitted rootabsX<38mm,rootZ>1.810m,all controlabsX<55mm;reject entire strand if any checked signed body gap>20mm. New radii capped30microns. Original geometry still untouched.'
 (out/'posterior_overlay_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if replacement:
 report.update(replacement_selection=replacement,removed_existing_fibers=len(removed),all_original_hair_retained_in_render=False)
 if full_section:
  report.update(full_section=True,removal_mode='Preview-only1nanometer radius mask,not curve deletion;preserve original object and all curve indices')
  report['method']+=' Full-section preview override: inspected projected IDs intersecttipY>30mm,exclude accepted fringe/accent/released-tip groups;set selected radii to1nanometer in a copied datablock. All positions,counts,other radii,historical attributes,object/material/index identity retained. This is near-invisible radius suppression,not exact removal. No candidate saved.'
 else:
  report['method']+=' Replacement preview override: hide original primary object and render exact retained positions/counts/radii/matrix/material,omitting inspected projected fibers with tipY>30mm,excluding accepted fringe/accent/released-tip groups. Original underlying data block untouched but selected fibers intentionally absent from render. Companion donor layer unchanged. No candidate saved;temporary retained object does not copy historical curve attributes. Recreated object/indices may change Hair Info Random;not an exact shading control.'
 (out/'posterior_overlay_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SHORT_POSTERIOR_OVERLAY',version,len(output),flush=True)
