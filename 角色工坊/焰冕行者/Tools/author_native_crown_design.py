"""Retarget actual crown follicles to distinct hand-authored long-layer guides."""
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
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero((~frame)&(~fringe)&(r[:,2]>1.840)&(r[:,1]<.055)&(r[:,1]>-.105)&(np.abs(r[:,0])<.079))
design=[
 [[.012,-.045,1.875],[-.008,-.068,1.891],[-.040,-.108,1.883],[-.068,-.145,1.847],[-.050,-.164,1.788],[-.037,-.151,1.774]],
 [[-.021,-.055,1.872],[-.044,-.084,1.883],[-.074,-.120,1.851],[-.083,-.133,1.811],[-.094,-.111,1.785]],
 [[-.045,-.030,1.863],[-.066,-.059,1.875],[-.093,-.075,1.838],[-.102,-.054,1.784],[-.108,-.028,1.770]],
 [[-.006,.002,1.880],[-.024,-.035,1.894],[-.058,-.079,1.871],[-.073,-.094,1.826],[-.060,-.069,1.787]],
 [[.020,-.083,1.862],[.039,-.109,1.879],[.065,-.140,1.845],[.055,-.159,1.800],[.034,-.154,1.770]],
 [[.046,-.053,1.863],[.063,-.073,1.878],[.087,-.101,1.853],[.096,-.111,1.810],[.091,-.089,1.779]],
 [[.029,-.007,1.878],[.050,-.034,1.891],[.078,-.069,1.876],[.105,-.086,1.833],[.098,-.056,1.787]],
 [[.002,.033,1.879],[-.025,.009,1.892],[-.060,-.019,1.867],[-.079,.008,1.819],[-.074,.045,1.764]],
 [[-.050,.022,1.864],[-.079,.001,1.877],[-.095,.019,1.835],[-.104,.054,1.785],[-.093,.077,1.747]],
 [[.057,.026,1.863],[.083,.005,1.877],[.108,.028,1.833],[.103,.059,1.778],[.091,.082,1.750]]]
anchors=np.array([g[0] for g in design]);distance=np.linalg.norm(r[ids,None]-anchors[None],axis=2)
labels=np.argmin(distance,axis=1);t=np.linspace(0,1,65)
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());mask=np.zeros(len(raw),bool);rows=[];repairs=0
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
for k,knots in enumerate(design):
 members=ids[labels==k]
 if not len(members):continue
 controls=np.array(knots,float);u=t*(len(controls)-1);ix=np.minimum(np.floor(u).astype(int),len(controls)-2);f=(u-ix)[:,None]
 ex=np.vstack([2*controls[0]-controls[1],controls,2*controls[-1]-controls[-2]])
 aa,bb,cc,dd=ex[ix],ex[ix+1],ex[ix+2],ex[ix+3]
 guide=.5*(2*bb+(-aa+cc)*f+(2*aa-5*bb+4*cc-dd)*f*f+(-aa+3*bb-3*cc+dd)*f*f*f)
 # Every real follicle retains its own root, with a broad transition into guide.
 root_delta=r[members]-controls[0]
 values=guide[None]+root_delta[:,None]*(1-.83*smooth((t-.05)/.78))[None,:,None]
 for i,index in enumerate(members):
  seed=np.sin(index*2.399963)
  values[i,:,2]+=.007*seed*smooth((t-.55)/.45)
  values[i,:,0]+=.001*seed*np.sin(np.pi*t)
  for j in range(1,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
   if dist<.03 and gap<.0005:
    values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=r[members];q[members]=values;mask[members]=True
 rows.append(dict(guide=k,fibers=len(members),maximum_displacement_m=float(np.linalg.norm(values-raw[members],axis=2).max())))
assert np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
assert np.array_equal(q[frame|fringe],raw[frame|fringe]) and (q[:,-1,2]<1.640).sum()==0
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_hand_designed_crown';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'crown_design_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selection_attribute=attr,
 changed_fibers=int(mask.sum()),designed_guides=len(rows),groups=rows,discrete_body_repairs=repairs,
 method='Actual upper-crown follicles (Z>1.840m,Xabs<79mm,Y(-105,+55)mm), excluding all106 foreground. Ten hand-authored asymmetric5/6-knot Catmull guide paths with varied crests/side and front terminal positions.83% root scatter taper and7mm tip scatter, source follicles/radii/topology/other hair/materials retained.',
 status='Actual drafts pending artistic review; geometry guard not art/continuous collision acceptance.'),indent=2),encoding='utf-8')
print('HAND_DESIGNED_CROWN',version,int(mask.sum()),flush=True)
