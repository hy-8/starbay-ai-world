"""Two localized long-part overlay prototypes on real source follicles."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
follow_support='--follow-support' in a
front_frame='--front-frame' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh transition prototype required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
support=bpy.data.objects['Abhay flow derivative • real scalp sampled short support'];cu=support.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());starts=np.array([c.first_point_index for c in cu.curves]);r=p[starts].astype(float)
sizes=np.array([c.points_length for c in cu.curves]);assert (sizes==sizes[0]).all();raw_support=p.reshape(-1,int(sizes[0]),3).astype(float)
if 'Abhay part transition • continuous overlay' in bpy.data.objects:raise RuntimeError('Use a source without this overlay')
eligible=np.flatnonzero((r[:,0]<-.010)&(r[:,0]>-.090)&(r[:,1]>-.115)&(r[:,1]<.025)&(r[:,2]>1.830));root=r[eligible];K=12
if front_frame:
 eligible=np.flatnonzero((r[:,0]>.028)&(r[:,0]<.080)&(r[:,1]<-.070)&(r[:,1]>-.135)&(r[:,2]>1.815));root=r[eligible];K=8
assert len(root)>100
centers=[root[len(root)//2]];best=np.full(len(root),np.inf)
for _ in range(1,K):best=np.minimum(best,np.sum((root-centers[-1])**2,axis=1));centers.append(root[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(root*root).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*root@centers.T),axis=1)
for _ in range(16):
 labels=assign()
 for k in range(K):
  if (labels==k).any():centers[k]=root[labels==k].mean(axis=0)
labels=assign();body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4));bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
camera=bpy.data.objects['02_ThreeQuarter'];M=np.array(camera.matrix_world.inverted());P=np.array(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=960,y=1120,scale_x=1,scale_y=1));clip=np.c_[centers,np.ones(K)]@M.T@P.T;xy=clip[:,:2]/clip[:,3,None];pixels=np.c_[(xy[:,0]*.5+.5)*960,(.5-xy[:,1]*.5)*1120]
scores={k:float(np.linalg.norm((pixels[k]-[550,365])/[960,1120])) for k in range(K)}
if follow_support:
 for k in range(K):
  path=raw_support[eligible[labels==k]].mean(axis=0);points=path[int(len(path)*.25):int(len(path)*.80)];projected=np.c_[points,np.ones(len(points))]@M.T@P.T;xy=projected[:,:2]/projected[:,3,None];screen=np.c_[(xy[:,0]*.5+.5)*960,(.5-xy[:,1]*.5)*1120];scores[k]=float(np.linalg.norm((screen-[550,365])/[960,1120],axis=1).min())
order=sorted([k for k in range(K) if (labels==k).sum()>60],key=lambda k:scores[k])[:2]
if front_frame:order=[k for k in range(K) if (labels==k).sum()>45]
t=np.linspace(0,1,65);allp=[];allr=[];rows=[];repairs=0
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for k in order:
 members=eligible[labels==k];roots=r[members];center=roots.mean(axis=0);phase=k*2.399963;end=np.array([-.098,center[1]+.020,1.765+.008*np.sin(phase)])
 controls=[]
 for u in np.linspace(0,1,20):
  target=center*(1-u)+end*u;target[0]-=.003*np.sin(2*np.pi*u)*np.sin(np.pi*u);target[1]+=.002*np.sin(np.pi*u+phase)*np.sin(np.pi*u)
  hit,n,_,dist=bv.find_nearest(Vector(target));on_head=np.array(hit+n*(.001+.010*np.sin(np.pi*u)**.8))
  free=smooth((u-.72)/.28);controls.append(on_head*(1-free)+target*free)
 controls=np.array(controls);controls[0]=center;u=t*19;ix=np.minimum(np.floor(u).astype(int),18);f=(u-ix)[:,None];ext=np.vstack([2*controls[0]-controls[1],controls,2*controls[-1]-controls[-2]])
 aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3];guide=.5*(2*bb+(-aa+cc)*f+(2*aa-5*bb+4*cc-dd)*f*f+(-aa+3*bb-3*cc+dd)*f*f*f)
 if follow_support:
  old=raw_support[members].mean(axis=0);guide=np.column_stack([np.interp(t,np.linspace(0,1,len(old)),old[:,ax]) for ax in range(3)])
  normals=np.array([bv.find_nearest(Vector(v))[1][:] for v in guide]);normals=np.vstack([normals[0],(normals[:-2]+normals[1:-1]+normals[2:])/3,normals[-1]]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-9)
  guide+=normals*(.0035*np.sin(np.pi*t)**1.1)[:,None];guide[:,2]-=.030*smooth((t-.65)/.35);guide[0]=center
 if front_frame:
  # Explicit temple-framing silhouettes, rather than another invisible
  # duplicate of the swept-back donor. Real positive-X follicle patches
  # were identified in the actual camera attribution probe57.
  end=np.array([.091+.006*np.sin(phase),-.130-.008*np.cos(phase),1.770+.012*np.sin(phase*.63)])
  c1=center+np.array([.010,-.018,.007])
  c2=np.array([.105,-.154,1.805+.006*np.cos(phase)])
  u=t[:,None]
  guide=(1-u)**3*center+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
  guide[:,0]+=.0015*np.sin(2*np.pi*t+phase)*np.sin(np.pi*t)
  guide[0]=center
 # Narrow only the free fan: its true entry roots still span the source patch.
 values=guide[None]+(roots-center)[:,None]*(1-.80*smooth((t-.08)/.92))[None,:,None]
 for local,i in enumerate(members):
  fiber_phase=i*2.399963;values[local,:,0]+=.0008*np.sin(np.pi*t)*np.sin(2*np.pi*t+fiber_phase);values[local,:,1]+=.0006*np.sin(np.pi*t)*np.cos(2*np.pi*t+fiber_phase)
  for j in range(1,65):
   hit,n,_,dist=bv.find_nearest(Vector(values[local,j]));gap=(Vector(values[local,j])-hit).dot(n)
   if dist<.025 and gap<.0005:values[local,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=roots;radius=.000032*(.78+.22*np.sin(members*1.618)**2)
 radii=radius[:,None]*(1-.93*t**2.8)[None];allp.append(values.astype(np.float32));allr.append(radii.astype(np.float32));rows.append(dict(patch=int(k),fibers=len(members),projected_root_center_pixels=pixels[k].tolist(),roi_distance_normalized=scores[k],length_quantiles_m=np.quantile(np.linalg.norm(np.diff(values,axis=1),axis=2).sum(axis=1),[0,.5,1]).tolist()))
q=np.concatenate(allp);rr=np.concatenate(allr);assert np.isfinite(q).all() and (rr>0).all()
new=bpy.data.hair_curves.new('Part transition prototype');new.add_curves([65]*len(q));new.attributes['position'].data.foreach_set('vector',q.ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rr.ravel());new.materials.append(bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0])
ob=bpy.data.objects.new('Abhay part transition • continuous overlay',new);bpy.context.scene.collection.objects.link(ob)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter','01_Front','03_Side']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
method=('Positive-X/front Abhay root area supported by actual camera probe57; up to8 real follicle patches with explicitly authored cubic temple-framing silhouettes, 1.770+-12mm free ends and patch-varying gentle curl' if front_frame else 'Two of12 Abhay root patches selected by actual middle-shaft camera footprint (point approximation, not ray visibility);existing mean support path lifted3.5mm along smoothed real-body normals, free last35% extended down30mm' if follow_support else 'Two of12 actual Abhay follicle patches nearest camera part ROI by projected roots;20 smooth real-body controls/1-11mm loft, free lower28% fall')
(out/'part_transition_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,added_object=ob.name,added_fibers=len(q),patches=rows,follow_support=follow_support,all_existing_hair_and_meshes_retained=True,discrete_body_repairs=repairs,method=method+';65-point continuous native shafts, physical25-32micron roots tapered ends;existing full coverage untouched',license='Derivative uses Abhay existing licensed follicles; source and derived geometry remain local',status='Actual drafts pending review',scope='Additive local prototype/discrete body points, not eye/continuous segment/clothing/animation or art acceptance'),indent=2),encoding='utf-8');print('PART_TRANSITION_SAVED',version,len(q),flush=True)
