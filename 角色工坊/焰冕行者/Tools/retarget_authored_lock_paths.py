"""Small real-geometry retarget study using existing Bystedt CC BY-SA short hair.
No new layers, deletion, downloads, or complete-model saves. Source geometry local.
"""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
no_outward='--no-outward' in a
additional=a[a.index('--also-selection')+1] if '--also-selection' in a else None
if additional:assert re.fullmatch('[A-Za-z0-9_-]+',additional)
save='--save' in a;save_only='--save-only' in a
assert not save_only or save
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out=ARCHIVE/'Renders'/version;assert not out.exists()
modeldir=ARCHIVE/'Exports'/version
if save:assert not modeldir.exists()
asset=ROOT/'Source/BlenderHairStyles/Bystedt_HairStyles.blend';source=ROOT/'Exports'/base/'Ember_Regent.blend'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ah=digest(asset);before=digest(source)
assert ah=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
ob=bpy.data.objects['cyberpunk hair'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();cu=ob.evaluated_get(dg).data
xyz=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',xyz.ravel())
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)];m=np.array(ob.matrix_world)
xyz=(xyz@m[:3,:3].T+m[:3,3])*.1
head=bpy.data.objects['head'];top=max((head.matrix_world@v.co).z for v in head.data.vertices)*.1
cs=np.array([0,-.063,top-.100]);ct=np.array([0,-.044,1.771]);rotation=np.array(Matrix.Rotation(-1.1,3,'X'))
mapped=ct+(xyz-cs)@rotation.T*1.06
donors=[]
for i in range(len(sizes)):
 q=mapped[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 if .045<arc[-1]<.160 and np.linalg.norm(q[-1]-q[0])>.030:donors.append((i,q,arc))
tree=KDTree(len(donors))
for i,(_,q,_) in enumerate(donors):tree.insert(Vector(q[0]),i)
tree.balance()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];assert np.allclose(np.array(ob.matrix_world),np.eye(4));cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
sel=ARCHIVE/'Renders'/selection;assert json.loads((sel/'edit_id_manifest.json').read_text())['source_sha256']==before
selected=np.load(sel/'local_projected_indices.npz')['selected']
if additional:
 second=ARCHIVE/'Renders'/additional
 assert json.loads((second/'edit_id_manifest.json').read_text())['source_sha256']==before
 selected=np.union1d(selected,np.load(second/'local_projected_indices.npz')['selected'])
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 flags=np.empty(len(sizes),bool);cu.attributes[key].data.foreach_get('value',flags);assert not flags[selected].any()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
def frame(path,normal):
 chord=path[-1]-path[0];distance=np.linalg.norm(chord);along=chord/distance
 across=normal-along*(normal@along)
 if np.linalg.norm(across)<1e-6:across=np.cross(along,[0,0,1])
 across/=max(np.linalg.norm(across),1e-9)
 return np.column_stack([along,across,np.cross(along,across)]),distance
stats=[]
for i in selected:
 q=old[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 if arc[-1]<.04 or np.linalg.norm(q[-1]-q[0])<.02:continue
 candidates=sorted(tree.find_n(Vector(q[0]),8),key=lambda x:x[2]);_,j,_=candidates[int(i)%len(candidates)]
 donor_id,d,da=donors[j];dt=da/da[-1]
 source_normal=(d-(d[0]+dt[:,None]*(d[-1]-d[0]))).mean(0)
 if np.linalg.norm(source_normal)<1e-5:source_normal=d[len(d)//2]-ct
 sf,sl=frame(d,source_normal)
 target_normal=q[len(q)//2]-ct;tf,tl=frame(q,target_normal)
 local=(d-d[0])@sf*(tl/sl);t=arc/arc[-1]
 target=q[0]+np.column_stack([np.interp(t,dt,local[:,k]) for k in range(3)])@tf.T
 delta=(target-q)*smooth((arc-.008)/.025)[:,None];delta[arc<=.008]=0;delta[-1]=0
 if no_outward:
  normals=np.array([bv.find_nearest(Vector(v))[1] for v in q])
  outward=float(np.einsum('ij,ij->i',delta,normals).max())
  raise_z=float(delta[:,2].max())
  delta*=min(1.,.0015/max(outward,1e-9),.001/max(raise_z,1e-9))
 delta*=min(1.,.025/max(np.linalg.norm(delta,axis=1).max(),1e-9))
 qs=np.vstack([q,(q[:-1]+q[1:])*.5]);ds=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(ds,axis=1)>1e-7
 qs=qs[moving];ds=ds[moving];limits=[min(.0003,gap(v))-1e-6 for v in qs];scale=1.
 for trial in range(7):
  if all(gap(v+d*scale)>=g for v,d,g in zip(qs,ds,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale;stats.append([int(i),donor_id,scale,float(np.linalg.norm(delta*scale,axis=1).max())])
assert np.isfinite(p).all() and np.array_equal(p[off[:-1]],old[off[:-1]]) and np.array_equal(p[off[1:]-1],old[off[1:]-1])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();out.mkdir(parents=True)
np.savez_compressed(out/'local_graft_mapping.npz',stats=np.array(stats))
modelhash=None
if save:
 modeldir.mkdir(parents=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True)
 modelhash=digest(modeldir/'Ember_Regent.blend')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for dev in pref.devices:dev.use=dev.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
images={}
shots=['02_ThreeQuarter','03_Side','04_Back']
if '--all-views' in a:
 cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
 shots+=['05_OppositeSide','01_Front']
for shot in shots:
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before and digest(asset)==ah
report=dict(source=base,source_sha256=before,asset_sha256=ah,source_and_asset_unchanged=True,author='Daniel Bystedt',license='CC BY-SA; version unspecified in source evidence',selection=selection,selected_fibers=len(selected),processed_fibers=len(stats),body_scales=np.quantile(np.array(stats)[:,2],[0,.5,1]).tolist(),max_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),model_saved=False,images_sha256=images,method='Existing evaluated cyberpunk strands selected from eight nearest approximate mapped roots. Retarget each authored chord frame to original root/tip and outward radial bow plane, resample by original normalized arc; root8mm/25mm ramp,whole-fiber25mm displacement cap and discrete control/midpoint body gap backtracking. No additional hair layer,all roots/tips/counts/radii preserved. Individual arc lengths may change; not continuous collision or art acceptance.')
report['no_outward']=no_outward
report['additional_selection']=additional
report.update(model_saved=save,model_sha256=modelhash,positions_sha256=hashlib.sha256(p.tobytes()).hexdigest())
if no_outward:report['method']+=' Before25mm cap,apply one factor per whole fiber limiting displacement along original sampled body normals to1.5mm outward and positive Z to1mm. This is a control-point directional limit,not a continuous surface envelope.'
(out/'retarget_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if save:(modeldir/'retarget_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ROOTED_AUTHORED_RETARGET_PREVIEW',version,len(stats),flush=True)
