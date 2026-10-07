"""Local part undercoat follows continuous existing side-hair segments."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
layered='--layered' in a
front_roi='--front-roi' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh bridge study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
def paths(ob):
 cu=ob.data;n=np.array([c.points_length for c in cu.curves]);assert (n==n[0]).all() and np.array_equal(np.array(ob.matrix_world),np.eye(4))
 p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());return p.reshape(-1,int(n[0]),3).astype(float)
ob=bpy.data.objects['Abhay flow derivative • real scalp sampled short support'];cu=ob.data;raw=paths(ob);q=raw.copy();r=raw[:,0];N=raw.shape[1]
main=paths(bpy.data.objects['Bystedt layercut derivative • native root reflow']);candidates=np.flatnonzero((main[:,-1,0]<-.060)&(main[:,-1,2]<1.820)&(main[:,-1,1]>-.090))
if front_roi:
 candidates=np.flatnonzero((main[:,0,0]>.025)&(main[:,0,0]<.073)&(main[:,0,1]<-.065)&(main[:,0,1]>-.125)&(main[:,0,2]>1.830))
assert len(candidates)>100
lookup=[(int(i),j) for i in candidates for j in range(0,49,4)];tree=KDTree(len(lookup))
if front_roi:lookup=[(int(i),0) for i in candidates];tree=KDTree(len(lookup))
for k,(i,j) in enumerate(lookup):tree.insert(Vector(main[i,j]),k)
tree.balance();body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
eligible=(r[:,0]<-.008)&(r[:,0]>-.090)&(r[:,1]>-.115)&(r[:,1]<.050)&(r[:,2]>1.824)
if front_roi:eligible=(r[:,0]>.025)&(r[:,0]<.080)&(r[:,1]<-.060)&(r[:,1]>-.135)&(r[:,2]>1.810)
mask=np.zeros(len(raw),bool);rows=[];repairs=0;distances=[];lengths=[]
for i in np.flatnonzero(eligible):
 if layered and i%3!=0:continue
 root=r[i];direction=raw[i,-1]-root;direction/=max(np.linalg.norm(direction),1e-9);options=[]
 for _,k,dist in tree.find_n(Vector(root),32):
  donor,j=lookup[k];path=main[donor,j:];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  if arc[-1]<.030:continue
  forward=path[min(6,len(path)-1)]-path[0];forward/=max(np.linalg.norm(forward),1e-9)
  options.append((dist+.008*(1-np.dot(direction,forward)),dist,donor,j,arc))
  if front_roi:options[-1]=(dist,dist,donor,j,arc)
 if not options:continue
 _,distance,donor,j,arc=min(options,key=lambda x:x[0])
 if distance>.030:continue
 path=main[donor,j:];phase=i*2.399963;L=min(arc[-1]*.88,.048+.018*(.5+.5*np.sin(phase)))
 if front_roi:
  if distance>.009:continue
  L=min(arc[-1]*.78,.068+.016*(.5+.5*np.sin(phase)))
 at=np.linspace(0,L,N);v=np.column_stack([np.interp(at,arc,path[:,k]) for k in range(3)])
 # One continuous donor trajectory: translate its entry to the real follicle,
 # then fade that translation over24mm. This never independently snaps to
 # the changing nearest hair point field (the rejected29 route).
 fade=np.clip(1-at/.024,0,1);fade=fade*fade*(3-2*fade);v+=(root-path[0])[None]*fade[:,None]
 for k in range(1,N):
  hit,n,_,dist=bv.find_nearest(Vector(v[k]));gap=(Vector(v[k])-hit).dot(n)
  if dist<.022 and gap<.0010:v[k]+=np.array(n)*(.0013-gap);repairs+=1
 v[0]=root;q[i]=v;mask[i]=True;distances.append(float(distance));lengths.append(float(np.linalg.norm(np.diff(v,axis=0),axis=1).sum()))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());attr='native_part_bridge'
prior=ob.data.attributes.get(attr)
if prior:ob.data.attributes.remove(prior)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
method=('Positive-X/front Abhay zone informed by camera probe57; nearest of32 actual authored primary root trajectories, at most9mm root distance;68-84mm travel capped at78% remaining donor arc' if front_roi else 'Abhay upper-negative-X part support; closest of32 existing continuous long-side trajectory entries with direction penalty;48-66mm travel capped at88% remaining donor arc')
(out/'part_bridge_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,changed_fibers=int(mask.sum()),eligible_fibers=int(eligible.sum()),layered=layered,front_roi=front_roi,preserved_original_fraction=2/3 if layered else None,candidate_primary_shafts=len(candidates),selection_attribute=attr,entry_distance_quantiles_m=np.quantile(distances,[0,.5,.9,1]).tolist(),result_length_quantiles_m=np.quantile(lengths,[0,.5,.9,1]).tolist(),discrete_body_repairs=repairs,all_roots_exact=True,unselected_support_exact=True,other_native_objects_exact=True,method=method+';entry translation fades over24mm;'+('only index%3==0 selected, remaining2/3 untouched coverage;' if layered else '')+'no raw donor indices uploaded',status='Actual drafts pending review',scope='Static local shape and discrete body point checks, not full segment/eye/clothing/motion or art acceptance'),indent=2),encoding='utf-8');print('PART_BRIDGE_SAVED',version,int(mask.sum()),flush=True)
