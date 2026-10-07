"""Whole-path posterior ribbon resection, preserving real roots and fringe."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a[:3]
curl='--curl-family' in a
relax='--relax-tips' in a
transport='--transport-frames' in a
if relax and not curl:raise ValueError('Tip relaxation requires curl-family mode')
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh back-lock study')
source=ROOT/'Exports'/base/'Ember_Regent.blend';probe_file=ROOT/'Exports'/probe/'local_flow_groups.npz'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
groups=np.load(probe_file);ids=groups['ids'];labels=groups['labels'];assert np.array_equal(ids,np.flatnonzero(front<0))
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for g in np.unique(labels):
 members=ids[labels==g];old=raw[members];center=old.mean(axis=0)
 if len(members)<40 or center[0,1]<-.005 or center[-1,1]<.020:continue
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 normal=center-np.array([0,-.035,1.776]);normal-=tangent*np.sum(normal*tangent,axis=1)[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
 across=np.cross(tangent,normal)
 if transport:
  transported=np.zeros_like(across);previous=across[0].copy()
  for j in range(65):
   previous-=tangent[j]*np.dot(previous,tangent[j]);previous/=max(np.linalg.norm(previous),1e-9);transported[j]=previous
  across=transported;normal=np.cross(across,tangent)
 delta=old-center[None]
 along=np.sum(delta*tangent[None],axis=2);wide=np.sum(delta*across[None],axis=2);deep=np.sum(delta*normal[None],axis=2)
 width=float(np.median(np.quantile(wide,.95,axis=0)[16:49]-np.quantile(wide,.05,axis=0)[16:49]))
 depth=float(np.median(np.quantile(deep,.95,axis=0)[16:49]-np.quantile(deep,.05,axis=0)[16:49]))
 if width<.010:continue
 phase=float(g*2.399963);target_width=.007+.002*(.5+.5*np.cos(phase));target_depth=.0028
 ws=min(1,target_width/max(width,1e-9));ds=min(1,target_depth/max(depth,1e-9))
 weight=smooth((t-.12)/.30);taper=1-.55*smooth((t-.77)/.23)
 ww=wide*(1-weight[None]+ws*weight[None])*taper[None]
 dd=deep*(1-weight[None]+ds*weight[None])
 values=center[None]+tangent[None]*along[:,:,None]+across[None]*ww[:,:,None]+normal[None]*dd[:,:,None]
 # Small coherent separation between WHOLE path families, not independent
 # nearest-point snapping or replacement of long shafts by scalp arcs.
 values+=normal[None]*(.0025*np.sin(phase)*np.sin(np.pi*t)*weight)[None,:,None]
 values+=across[None]*(.0015*np.sin(2.4*np.pi*t+phase)*np.sin(np.pi*t)*weight)[None,:,None]
 if curl:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(center,axis=0),axis=1))]
  theta=2*np.pi*arc/.085+phase
  curl_weight=weight*(1-smooth((t-.68)/.32)) if relax else weight
  # Real 85mm wavelength, 6mm lateral/3mm depth loose bend. Independent
  # whole-family phase changes the common specular planes; the existing
  # center flow and longitudinal scatter are still present underneath.
  values+=across[None]*(.006*(np.sin(theta)-np.sin(phase))*curl_weight)[None,:,None]
  values+=normal[None]*(.003*(np.cos(theta)-np.cos(phase))*curl_weight)[None,:,None]
 for i in range(len(members)):
  for j in range(6,65):
   if values[i,j,2]<1.765:continue
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.020 and gap<.0004:values[i,j]+=np.array(n)*(.0006-gap);repairs+=1
 values[:,:4]=old[:,:4];q[members]=values;mask[members]=True
 rows.append(dict(group=int(g),fibers=len(members),before_mid_width_m=width,before_mid_depth_m=depth,target_mid_width_m=target_width,target_mid_depth_m=target_depth,max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());ob.data.attributes.new('native_back_resection','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['04_Back','05_OppositeSide','02_ThreeQuarter']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'back_resection_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),local_probe_sha256=hashlib.sha256(probe_file.read_bytes()).hexdigest(),changed_fibers=int(mask.sum()),families=rows,curl_family=curl,relaxed_tips=relax,transported_frames=transport,all_first_four_points_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,discrete_body_repairs=repairs,method='Whole-path posterior families (96 kmeans across five shaft samples, not root voxels); tangent-frame target middle7-9mm width/2.8mm depth, tapered end55%, small2.5mm depth/1.5mm cross separation, original trajectories/longitudinal scatter retained'+('; actual center arc-length85mm wavelength,6mm lateral/3mm depth loose curl with independent family phase' if curl else '')+('; relax added curl progressively over final32% of shaft, retaining existing free ends' if relax else '')+('; parallel-transported cross sections avoid radial-frame flips' if transport else ''),status='Actual drafts pending review',scope='Static localized design and discrete body points, not full segment/eye/clothing/animation collision or art acceptance'),indent=2),encoding='utf-8')
print('BACK_RESECTION_SAVED',version,int(mask.sum()),len(rows),flush=True)
