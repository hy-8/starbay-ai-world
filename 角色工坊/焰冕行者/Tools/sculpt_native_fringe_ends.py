"""Resection the free fringe below earlier elevation-limited studies."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a[:3];all_wide='--all-wide' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh fringe sculpture required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front);groups=np.load(ROOT/'Exports'/probe/'local_flow_groups.npz');ids=groups['ids'];labels=groups['labels'];assert np.array_equal(ids,np.flatnonzero(front>=0))
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4));bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
chosen=[10,11,16,19,22,26] if all_wide else [10,16];t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for g in chosen:
 members=ids[labels==g];old=raw[members];center=old.mean(axis=0);tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 across=np.zeros_like(tangent);previous=np.cross(tangent[0],[0,0,1]);previous/=max(np.linalg.norm(previous),1e-9)
 for j in range(65):previous-=tangent[j]*np.dot(previous,tangent[j]);previous/=max(np.linalg.norm(previous),1e-9);across[j]=previous
 normal=np.cross(across,tangent);delta=old-center[None];along=np.sum(delta*tangent[None],axis=2);wide=np.sum(delta*across[None],axis=2);deep=np.sum(delta*normal[None],axis=2)
 width=np.diff(np.quantile(wide,[.05,.95],axis=0),axis=0)[0];depth=np.diff(np.quantile(deep,[.05,.95],axis=0),axis=0)[0]
 free_width=float(np.median(width[49:]));free_depth=float(np.median(depth[49:]));phase=g*2.399963
 weight=smooth((t-.38)/.40);ws=np.minimum(1,.0035/np.maximum(width,1e-7));ds=np.minimum(1,.0025/np.maximum(depth,1e-7))
 values=center[None]+tangent[None]*along[:,:,None]+across[None]*(wide*(1-weight[None]+ws[None]*weight[None]))[:,:,None]+normal[None]*(deep*(1-weight[None]+ds[None]*weight[None]))[:,:,None]
 # Free-end flick changes the silhouette, while existing individual length
 # scatter stays along the measured growth direction. No z1.800 gate:
 # the visible free hair actually lies below that previous selection.
 flick=smooth((t-.55)/.45);values[:,:,0]+=.003*np.sin(phase)*flick[None];values[:,:,1]-=.0015*flick[None];values[:,:,2]+=.0035*np.cos(phase)*flick[None]
 for i in range(len(members)):
  for j in range(25,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.020 and gap<.0004:values[i,j]+=np.array(n)*(.0006-gap);repairs+=1
 values[:,:16]=old[:,:16];q[members]=values;mask[members]=True
 rows.append(dict(group=g,fibers=len(members),before_free_width_m=free_width,before_free_depth_m=free_depth,target_section_width_m=.0035,target_section_depth_m=.0025,max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.array_equal(q[:,:16],raw[:,:16]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());attr='native_fringe_end_sculpture';prior=ob.data.attributes.get(attr)
if prior:ob.data.attributes.remove(prior)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'fringe_end_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_fibers=int(mask.sum()),groups=rows,all_wide=all_wide,selection_attribute=attr,all_first_sixteen_points_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,discrete_body_repairs=repairs,method='Measured frontal whole-path families; parallel-transported section width3.5mm/depth2.5mm;shaft38%-78% gradual onset;free ends included regardless elevation;preserve longitudinal scatter with3mm lateral/3.5mm height end flick',status='Actual drafts pending review',scope='Static local geometry and discrete body protection, not all hair/eye/segment/clothing/animation or art acceptance'),indent=2),encoding='utf-8');print('FRINGE_END_SCULPTURE',version,int(mask.sum()),flush=True)
