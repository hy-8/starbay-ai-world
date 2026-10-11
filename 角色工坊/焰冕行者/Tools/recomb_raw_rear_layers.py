"""Scalp-transport study for mixed-control posterior fibers; fresh archive only."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
pilot='--pilot' in a;save='--save-archive' in a;feathered='--feathered' in a;smooth_scalp='--smooth-scalp' in a
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ARCHIVE/'Renders'/version;md=ARCHIVE/'Exports'/version
assert not out.exists() and (not save or not md.exists())
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];roots=p[off[:-1]];tips=p[off[1:]-1]
mask=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',mask)
mask&=(tips[:,1]>.015)&(tips[:,2]<1.800)&(roots[:,1]>-.030)
if pilot:mask&=roots[:,0]<-.005
ids=np.flatnonzero(mask);assert len(ids)>100
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4)) and np.array_equal(np.array(ob.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def nearest(point):return bv.find_nearest(point)
if smooth_scalp:
 evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
 vertices=np.array([v.co[:] for v in mesh.vertices]);normals=np.array([v.normal[:] for v in mesh.vertices]);triangles=np.array([t.vertices[:] for t in mesh.loop_triangles])
 surface=BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True)
 def nearest(point):
  h,flat,index,distance=surface.find_nearest(point)
  v=vertices[triangles[index]];ab=v[1]-v[0];ac=v[2]-v[0];ah=np.array(h)-v[0]
  d00=ab@ab;d01=ab@ac;d11=ac@ac;d20=ah@ab;d21=ah@ac;den=d00*d11-d01*d01
  if abs(den)<1e-20:return h,flat,index,distance
  b=(d11*d20-d01*d21)/den;c=(d00*d21-d01*d20)/den;weights=np.clip([1-b-c,b,c],0,1);weights/=weights.sum()
  normal=weights@normals[triangles[index]];normal/=max(np.linalg.norm(normal),1e-10)
  return h,Vector(normal),index,distance
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
lengths=[];rng=np.random.default_rng(93119);jitter=rng.uniform(-1,1,len(sizes))
groups=None;centers=None;group_scales=[]
if feathered:
 rr=roots[ids].astype(float);centers=[rr[len(rr)//2]]
 distance=np.sum((rr-centers[0])**2,axis=1)
 for _ in range((36 if pilot else 96)-1):
  centers.append(rr[np.argmax(distance)]);distance=np.minimum(distance,np.sum((rr-centers[-1])**2,axis=1))
 centers=np.array(centers)
 for _ in range(12):
  groups=np.argmin(np.sum((rr[:,None,:]-centers[None,:,:])**2,axis=2),axis=1)
  for k in range(len(centers)):
   if np.any(groups==k):centers[k]=rr[groups==k].mean(axis=0)
 labels=np.zeros(len(sizes),int);labels[ids]=groups
for i in ids:
 path=old[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];q=path.copy();root=path[0]
 phase=root[0]*310+root[1]*180+root[2]*190
 endpoint_z=1.748+.012*np.sin(phase)+.004*jitter[i]
 if feathered:
  center=centers[labels[i]];phase=center[0]*310+center[1]*180+center[2]*190
  endpoint_z=1.740+.60*max(0,root[2]-1.770)+.012*np.sin(phase)+.003*jitter[i]
 budget=min(arc[-1],max(.025,(root[2]-endpoint_z)*1.18))
 mapped=np.minimum(arc,.008)+np.maximum(arc-.008,0)*max(.001,budget-.008)/max(1e-9,arc[-1]-.008)
 for j in range(1,len(path)):
  if arc[j]<=.008:continue
  hit,normal,_,_=nearest(Vector(q[j-1]));heading=Vector(path[j]-path[j-1]);heading-=normal*heading.dot(normal)
  t=float(np.clip(mapped[j]/max(budget,1e-8),0,1));weight=float(smooth((mapped[j]-.008)/.024))
  goal=Vector((.22*np.sin(phase)+.12*np.sin(t*3.14+phase),.18,-1));goal-=normal*goal.dot(normal)
  if heading.length<1e-9 or goal.length<1e-9:continue
  heading.normalize();goal.normalize();direction=heading*(1-weight)+goal*weight
  if direction.length<1e-9:continue
  direction.normalize();nh,nn,_,_=nearest(hit+direction*float(mapped[j]-mapped[j-1]))
  oh,on,_,_=nearest(Vector(path[j]));oldgap=max(.00055,float((Vector(path[j])-oh).dot(on)))
  lift=(.005+.003*(.5+.5*np.sin(phase)))*(.4+.6*np.sin(np.pi*t)**2)
  if feathered:lift=.005+(.008+.009*(.5+.5*np.sin(phase)))*max(0.,np.sin(np.pi*t))**1.2+.006*t**3
  gap=oldgap*(1-weight)+lift*weight
  q[j]=nh+nn*gap
 p[off[i]:off[i+1]]=q
 lengths.append([float(arc[-1]),float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum())])
if feathered:
 # Group only the newly transported flow, not the prior wide donor ribbons.
 transported=p.copy();u=np.linspace(0,1,65);sampled=[]
 for i in ids:
  q=transported[off[i]:off[i+1]];t=np.linspace(0,1,len(q));sampled.append(np.column_stack([np.interp(u,t,q[:,j]) for j in range(3)]))
 sampled=np.array(sampled);guides=np.array([sampled[groups==k].mean(axis=0) for k in range(len(centers))])
 for index,i in enumerate(ids):
  q=transported[off[i]:off[i+1]].astype(float);t=np.linspace(0,1,len(q));guide=np.column_stack([np.interp(t,u,guides[groups[index],:,j]) for j in range(3)])
  tangent=np.gradient(q,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-10)
  delta=guide-q;delta-=tangent*np.sum(delta*tangent,axis=1)[:,None]
  path=old[off[i]:off[i+1]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  blend=.70*smooth((arc-.008)/.025)*(.6+.4*t)
  delta*=blend[:,None];mag=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.008/np.maximum(mag,1e-10))[:,None]
  # Whole-curve backtracking avoids pointwise kinks.
  samples=np.vstack([q,(q[:-1]+q[1:])*.5]);steps=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(steps,axis=1)>1e-8
  samples=samples[moving];steps=steps[moving];threshold=[]
  for point in samples:
   h,n,_,_=bv.find_nearest(Vector(point));threshold.append(min(.00025,float((Vector(point)-h).dot(n)))-1e-6)
  scale=1.
  for trial in range(7):
   valid=True
   for point,limit in zip(samples+steps*scale,threshold):
    h,n,_,_=bv.find_nearest(Vector(point))
    if float((Vector(point)-h).dot(n))<limit:valid=False;break
   if valid:break
   scale*=.5
  else:scale=0.
  p[off[i]:off[i+1]]=q+delta*scale
  group_scales.append(scale)
assert np.isfinite(p).all() and np.array_equal(old[off[:-1]],p[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();modelhash=None
if save:
 cu.attributes.new('native_rear_scalp_transport','BOOLEAN','CURVE').data.foreach_set('value',mask)
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
out.mkdir(parents=True);images={}
for shot in (['04_Back','05_OppositeSide'] if pilot else ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']):
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
m=dict(source=base,source_sha256=digest,source_unchanged=True,pilot=pilot,feathered=feathered,guide_groups=len(centers) if feathered else None,selected_fibers=len(ids),model_saved=save,model_sha256=modelhash,length_before_after_quantiles_m=np.quantile(lengths,[0,.5,1],axis=0).tolist(),length_statistics_before_optional_grouping=feathered,max_same_index_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),images_sha256=images,method='Original mixed control counts/radii/root8mm retained. Integrate projected downward tangent after24mm blend with coherent root-field lateral flow; normal clearance transitions to2-8mm varying by path/root. Arc budget=min(original,max25mm,(rootZ-(1.748+12mm*sin(rootphase)+4mm*jitter))*1.18). No claim of final length equal budget or continuous collision. Materials,front curtain and other objects unchanged. Actual art review required.')
if feathered:m['feathered_override']='36/96 farthest-point+12 Lloyd root groups;tip targetZ1.740+.60*max(0,rootZ-1.770)+12mm*sin(groupPhase)+3mm*jitter;lift5mm+(8..17mm)*sin(pi*t)^1.2+6mm*t^3. On new transported scaffold only,70percent transverse guide contraction ramp after8mm over25mm and capped8mm. Whole-curve body backtracking on controls/midpoints,not continuous collision.'
if feathered:m.update(group_scales_quantiles=np.quantile(group_scales,[0,.5,1]).tolist(),zero_scale_groups_fibers=int(np.count_nonzero(np.array(group_scales)==0)),group_body_guard='Changed controls/midpoints preserve min(previous scaffold gap,0.25mm) minus1micron. Exact root samples excluded from displacement guard.')
m.update(smooth_scalp=smooth_scalp,scalp_normal_method='Barycentric interpolated evaluated vertex normals on actual triangulated body' if smooth_scalp else 'BVH face normals')
(out/'scalp_transport_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
if save:(md/'scalp_transport_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('REAR_SCALP_TRANSPORT_RENDERED',version,len(ids),flush=True)
