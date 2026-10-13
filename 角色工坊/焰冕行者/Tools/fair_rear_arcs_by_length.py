"""Preview measured-length circular bows in one inspected posterior lock."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
sub_locks='--sub-locks' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out=ARCHIVE/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());original=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
sel=ARCHIVE/'Renders'/selection;assert json.loads((sel/'edit_id_manifest.json').read_text())['source_sha256']==before
mask=np.zeros(len(sizes),bool);mask[np.load(sel/'local_projected_indices.npz')['selected']]=True
mask&=p[off[1:]-1,1]>.030
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips','native_released_tip_clusters']:
 flags=np.empty(len(mask),bool);cu.attributes[key].data.foreach_get('value',flags);mask&=~flags
lanes={}
if sub_locks:
 measured=[]
 for i in np.flatnonzero(mask):
  q=original[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
  measured.append((float(np.interp(.45*arc[-1],arc,q[:,0])),int(i)))
 for rank,(_,i) in enumerate(sorted(measured)):lanes[i]=min(5,int(6*rank/len(measured)))
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
stats=[]
for i in np.flatnonzero(mask):
 q=original[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 start=np.searchsorted(arc,.008,side='right')-1
 if start>=len(q)-4 or arc[-1]<.045:continue
 tail=q[start:];sarc=arc[start:]-arc[start];length=sarc[-1];t=sarc/length
 chord=tail[-1]-tail[0];distance=np.linalg.norm(chord)
 if distance<.010:continue
 along=chord/distance;linear=tail[0]+t[:,None]*chord
 residual=tail-linear;weights=np.sin(np.pi*t)
 normal=(residual*weights[:,None]).sum(0);normal-=along*np.dot(normal,along)
 outward=tail.mean(0)-np.array([0.,-.035,1.776]);outward-=along*np.dot(outward,along)
 outward/=max(np.linalg.norm(outward),1e-10)
 if np.linalg.norm(normal)<.0001:normal=outward
 normal/=max(np.linalg.norm(normal),1e-10)
 if normal@outward<0:normal=outward
 if sub_locks:
  # Artist-defined six neighboring sweep directions, ordered by source midshaft X.
  # Change the bow plane, not the haircut endpoints or root attachment.
  turn=[-.95,-.60,.80,.45,-.85,.65][lanes[int(i)]]
  normal=normal*np.cos(turn)+np.cross(along,normal)*np.sin(turn)
 ratio=max(1.,length/distance);low,high=.0001,2.6
 for _ in range(40):
  angle=(low+high)/2
  if angle/(2*np.sin(angle/2))<ratio:low=angle
  else:high=angle
 angle=(low+high)/2;radius=distance/(2*np.sin(angle/2));phase=(t-.5)*angle
 target=(tail[0]+tail[-1])/2+radius*np.sin(phase)[:,None]*along+radius*(np.cos(phase)-np.cos(angle/2))[:,None]*normal
 delta=np.zeros_like(q);delta[start:]=(target-tail)*smooth((sarc-.001)/.025)[:,None]
 delta[arc<=.008]=0;delta[-1]=0
 cap=min(1.,.025/max(np.linalg.norm(delta,axis=1).max(),1e-10));delta*=cap
 qs=np.vstack([q,(q[:-1]+q[1:])*.5]);ds=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(ds,axis=1)>1e-7
 qs=qs[moving];ds=ds[moving];limits=[min(.0003,gap(v))-1e-6 for v in qs];scale=1.
 for attempt in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(qs,ds,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale
 stats.append([int(i),angle,cap,scale,float(arc[-1]),float(np.linalg.norm(np.diff(p[off[i]:off[i+1]].astype(float),axis=0),axis=1).sum())])
assert len(stats)>0 and np.isfinite(p).all()
assert np.array_equal(p[off[:-1]],original[off[:-1]]) and np.array_equal(p[off[1:]-1],original[off[1:]-1])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
out.mkdir(parents=True);np.savez_compressed(out/'local_arc_stats.npz',stats=np.array(stats),selected=np.flatnonzero(mask))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['04_Back','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
st=np.array(stats)
report=dict(source=base,source_sha256=before,source_unchanged=True,selection=selection,model_saved=False,selected_fibers=int(mask.sum()),processed_fibers=len(stats),max_same_index_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),angle_quantiles_rad=np.quantile(st[:,1],[0,.5,1]).tolist(),whole_fiber_cap_quantiles=np.quantile(st[:,2],[0,.5,1]).tolist(),body_scale_quantiles=np.quantile(st[:,3],[0,.5,1]).tolist(),actual_arc_length_change_quantiles_m=np.quantile(st[:,5]-st[:,4],[0,.5,1]).tolist(),images_sha256=images,method='Inspected projected IDs intersect tipY>30mm and exclude accepted inner curtain/frontal sweeps/curved tips/released tip cluster. Circular-bow target from original root8mm suffix endpoints and measured suffix length. Bend plane follows weighted original residual unless inward,then use approximate head-radial outward. Solve central angle up to2.6rad;root25mm blend,whole-fiber25mm cap and sampled body-gap backtracking. Original roots,tips,counts,radii preserved;actual lengths can change under angle cap/root blend/guard,not claimed exact. No model save,not continuous collision or art acceptance.')
(out/'arc_fairing_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if sub_locks:
 report.update(sub_locks=True,sub_lock_count=6,sub_lock_bow_rotations_rad=[-.95,-.60,.80,.45,-.85,.65])
 report['method']+=' Six equal-count sections ordered by source45percent-arc X. Rotate each section bow plane about root-tip chord by explicit alternating angles;no strand randomness. Root8mm/tips retained;body guard and25mm whole-fiber cap still applied.'
 (out/'arc_fairing_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('MEASURED_ARC_PREVIEW',version,len(stats),flush=True)
