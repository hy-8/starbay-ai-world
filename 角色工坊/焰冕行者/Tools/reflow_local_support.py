"""Recomb inspected rear support stripe along the scalp; retain exact frontal hair."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
save='--save-archive' in a;save_only='--save-only' in a
short='--short' in a
scalp_fit='--scalp-fit' in a
assert not save_only or save
source=ROOT/'Exports'/base/'Ember_Regent.blend';out=ROOT/'Renders'/version
modeldir=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
assert not out.exists() and (not save or not modeldir.exists())
digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
name='Abhay flow derivative • real scalp sampled short support';ob=bpy.data.objects[name];cu=ob.data
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());original=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];roots=p[off[:-1]]
mask=np.zeros(len(sizes),bool);mask[np.load(ROOT/'Renders'/selection/'local_projected_indices.npz')['selected']]=True
mask&=(roots[:,0]<-.015)&(roots[:,1]>-.025)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
ids=np.flatnonzero(mask);assert 0<len(ids)<5003
minimum_gap=1.;lengths=[]
for i in ids:
 old=original[off[i]:off[i+1]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))];q=old.copy()
 target_length=min(float(arc[-1]),.045,max(.014,float(old[0,2]-1.790))) if short else float(arc[-1])
 mapped_arc=np.minimum(arc,.008)+np.maximum(arc-.008,0)*(target_length-.008)/max(float(arc[-1])-.008,1e-9)
 for j in range(1,len(old)):
  if arc[j]<=.008:continue
  hit,normal,_,dist=bv.find_nearest(Vector(q[j-1]));heading=Vector(old[j]-old[j-1]);heading-=normal*heading.dot(normal)
  goal=Vector((0,.20,-1));goal-=normal*goal.dot(normal)
  if heading.length<1e-9 or goal.length<1e-9:continue
  heading.normalize();goal.normalize();weight=float(smooth((mapped_arc[j]-.008)/.014))
  direction=heading*(1-weight)+goal*weight
  if direction.length<1e-9:continue
  direction.normalize();step=float(mapped_arc[j]-mapped_arc[j-1]);nh,nn,_,_=bv.find_nearest(hit+direction*step)
  oh,on,_,_=bv.find_nearest(Vector(old[j]));gap=max(.00055,float((Vector(old[j])-oh).dot(on)))
  if scalp_fit:gap=gap*(1-weight)+min(gap,.003)*weight
  q[j]=nh+nn*gap;minimum_gap=min(minimum_gap,gap)
 p[off[i]:off[i+1]]=q
 lengths.append([float(arc[-1]),float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum())])
assert np.isfinite(p).all() and np.array_equal(p[off[:-1]],original[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();modelhash=None
if save:
 cu.attributes.new('native_recombed_rear_support','BOOLEAN','CURVE').data.foreach_set('value',mask)
 modeldir.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=hashlib.sha256((modeldir/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
out.mkdir(parents=True);images={}
if not save_only:
 for shot in ['04_Back','05_OppositeSide','02_ThreeQuarter']:
  s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,source_unchanged=True,selection=selection,object=name,model_saved=save,model_sha256=modelhash,archive_model_path=str(modeldir/'Ember_Regent.blend') if save else None,selected_fibers=len(ids),max_same_index_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),length_before_after_quantiles_m=np.quantile(lengths,[0,.5,1],axis=0).tolist(),generated_normal_gap_min_m=minimum_gap,images_sha256=images,method='Inspected back-projected Abhay subset intersect rootX<-15mm and rootY>-25mm. Exact root and original first8mm controls. Subsequent original segment steps smoothly turn over14mm toward projected downward/backward tangent;project each generated point on actual body and retain its original positive normal offset,min0.55mm. Point counts,radii,all other objects unchanged. Discrete scalp projection,not continuous collision or artistic acceptance.')
(out/'support_reflow_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
manifest.update(short_arc_budget=short,minimum_generated_z_m=float(p[np.repeat(mask,sizes),2].min()),maximum_generated_z_m=float(p[np.repeat(mask,sizes),2].max()),short_arc_method='Integration budget min(original arc,45mm,max(14mm,rootZ-1.790m)),first8mm unchanged. Original radius samples and normal offset retained;actual resulting arc may differ from step budget.' if short else None)
manifest.update(scalp_fit=scalp_fit,scalp_fit_method='Over same14mm smooth arc transition,blend original positive normal offset toward max3mm. Exact first8mm retained;transition points can exceed3mm. Not an all-points3mm clamp.' if scalp_fit else None)
(out/'support_reflow_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(modeldir/'support_reflow_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('LOCAL_SUPPORT_REFLOW',version,len(ids),flush=True)
