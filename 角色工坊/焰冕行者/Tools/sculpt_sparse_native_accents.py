"""Sculpt sparse existing source-follicle locks, preserving surrounding groom.

Uses actual103 paths, not new detached root strips or a replaced whole canopy.
"""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);roots=raw[:,0];q=raw.copy()
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
# Different broad peak positions and lateral accents; never periodic curls.
design=[
 ([-.030,-.055,1.872],.009,-.004,.24),
 ([.013,-.065,1.877],.006,.005,.33),
 ([.030,-.070,1.868],.007,-.004,.21),
 ([-.020,-.010,1.878],.008,.003,.31),
 ([.020,.005,1.880],.007,-.004,.37),
 ([-.040,-.010,1.862],.005,-.004,.24),
 ([.039,-.028,1.873],.006,.004,.33),
 ([.000,-.025,1.883],.008,-.003,.20),
 ([.045,-.080,1.845],.004,.003,.27),
 ([-.055,-.060,1.850],.005,-.004,.30)]
mask=np.zeros(len(raw),bool);rows=[];repairs=0;t=np.linspace(0,1,65)
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
for k,(anchor,loft,sweep,peak) in enumerate(design):
 available=np.flatnonzero((~frame)&(~mask)&(roots[:,2]>1.840))
 distances=np.linalg.norm(roots[available]-np.array(anchor),axis=1)
 reference=available[np.argmin(distances)]
 # Avoid gathering neighboring roots whose strands travel in another direction.
 candidate=available[np.linalg.norm(roots[available]-roots[reference],axis=1)<.006]
 flow=np.sqrt(np.mean(np.sum((raw[candidate][:,[8,16,24,40]]-raw[reference,[8,16,24,40]])**2,axis=2),axis=1))
 ids=candidate[flow<.009]
 if len(ids)<25:continue
 old=raw[ids];c=old.mean(0);tangent=np.gradient(c,axis=0)
 tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
 _,nn,_,_=bv.find_nearest(Vector(c[0]));n=np.array(nn)
 across=np.zeros_like(tangent);prev=np.cross(n,tangent[0]);prev/=max(np.linalg.norm(prev),1e-9)
 for j in range(65):
  prev-=tangent[j]*np.dot(prev,tangent[j]);prev/=max(np.linalg.norm(prev),1e-9);across[j]=prev
 normal=np.cross(tangent,across)
 if np.dot(normal[0],n)<0:normal=-normal
 envelope=smooth(t/.12)*(1-smooth((t-.42)/.27));envelope[44:]=0
 crest=envelope*np.exp(-.5*((t-peak)/.20)**2)
 delta=old-c[None];width=np.sum(delta*across[None],axis=2)
 values=old-across[None]*(width*.50*envelope[None])[:,:,None]
 values+=normal[None]*(loft*crest)[None,:,None]
 values+=across[None]*(sweep*envelope)[None,:,None]
 for i in range(len(ids)):
  for j in range(1,44):
   if envelope[j]<.001:continue
   hit,norm,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(norm)
   if dist<.03 and gap<.0005:
    values[i,j]+=np.array(norm)*(.0007-gap);repairs+=1
 values[:,0]=old[:,0];values[:,44:]=old[:,44:];q[ids]=values;mask[ids]=True
 rows.append(dict(design=k,fibers=len(ids),anchor_nearest_root_distance_m=float(distances.min()),root_mean_m=c[0].tolist(),
  normal_loft_m=loft,lateral_sweep_m=sweep,peak_parameter=peak,maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all()
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[:,44:],raw[:,44:])
assert np.array_equal(q[frame],raw[frame]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_sparse_crown_accents';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'sparse_accents_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selection_attribute=attr,
 changed_fibers=int(mask.sum()),designed_locks=len(rows),groups=rows,discrete_body_repairs=repairs,
 method='Ten manually placed scalp anchor targets choose existing nonforeground primary follicles within6mm of closest actual root and9mm RMS whole-path proximity. Retained source centerpaths with50% transverse contraction,4-9mm broad normal crest and3-5mm asymmetric sweep fading bypoint44. No added geometry, whole-canopy replacement or new scalp roots; all point0/44-64/foreground/other objects/materials retained.',
 status='Actual drafts pending artistic review, not completion or continuous collision acceptance.'),indent=2),encoding='utf-8')
print('SPARSE_NATIVE_ACCENTS',version,int(mask.sum()),len(rows),flush=True)
