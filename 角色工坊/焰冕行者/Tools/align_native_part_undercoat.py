"""Lie short part support beneath the nearest actual long shaft's scalp flow."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
posterior='--posterior' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',s) for s in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh part study required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
def paths(ob):
 n=np.array([c.points_length for c in ob.data.curves]);assert (n==n[0]).all()
 p=np.empty((len(ob.data.points),3),np.float32);ob.data.attributes['position'].data.foreach_get('vector',p.ravel())
 assert np.array_equal(np.array(ob.matrix_world),np.eye(4));return p.reshape(-1,int(n[0]),3).astype(float)
ob=bpy.data.objects['Original posterior coverage • surface-grown short fibers' if posterior else 'Bystedt derivative • short scalp support'];cu=ob.data;raw=paths(ob);q=raw.copy()
main=paths(bpy.data.objects['Bystedt layercut derivative • native root reflow'])
tree=KDTree(len(main))
for i,p in enumerate(main[:,0]):tree.insert(Vector(p),i)
tree.balance()
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
r=raw[:,0];mask=(r[:,2]>1.838)&(r[:,0]>-.022)&(r[:,0]<.050)&(r[:,1]>-.110)&(r[:,1]<.010)
if posterior:mask=(r[:,2]>1.834)&(r[:,1]>-.030)
ids=np.flatnonzero(mask);N=raw.shape[1];t=np.linspace(0,1,N);distances=[];lengths=[]
for i in ids:
 old=raw[i];root=old[0];_,j,dist=tree.find(Vector(root));donor=main[j];distances.append(float(dist))
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(donor,axis=0),axis=1))]
 L=np.linalg.norm(np.diff(old,axis=0),axis=1).sum();L=min(L,arc[-1]*.80)
 # Use the existing long-hair trajectory to choose its direction, not a new
 # crown guide. Place the short undercoat close to the actual head surface.
 at=np.linspace(0,L,16)
 controls=np.column_stack([np.interp(at,arc,donor[:,k]) for k in range(3)])+root-donor[0]
 for k in range(1,16):
  hit,n,_,distance=bv.find_nearest(Vector(controls[k]))
  assert hit is not None
  controls[k]=np.array(hit+n*(.0008+.0012*np.sin(np.pi*k/15)))
 controls[0]=root
 u=t*15;ix=np.minimum(np.floor(u).astype(int),14);f=(u-ix)[:,None]
 ex=np.vstack([2*controls[0]-controls[1],controls,2*controls[-1]-controls[-2]])
 aa,bb,cc,dd=ex[ix],ex[ix+1],ex[ix+2],ex[ix+3]
 value=.5*(2*bb+(-aa+cc)*f+(2*aa-5*bb+4*cc-dd)*f*f+(-aa+3*bb-3*cc+dd)*f*f*f)
 value[0]=root;q[i]=value;lengths.append(float(np.linalg.norm(np.diff(value,axis=0),axis=1).sum()))
assert len(ids)>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_part_undercoat','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for n in ['02_ThreeQuarter','05_OppositeSide']:
 s.camera=bpy.data.objects[n];s.render.filepath=str(render/(n+'.png'));bpy.ops.render.render(write_still=True)
report=dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_object=ob.name,changed_fibers=len(ids),posterior=posterior,nearest_long_root_distance_quantiles_m=np.quantile(distances,[0,.5,.9,1]).tolist(),result_length_quantiles_m=np.quantile(lengths,[0,.5,.9,1]).tolist(),all_roots_exact=True,unselected_support_exact=True,all_other_hair_exact=True,method=('Upper posterior original short coverage' if posterior else 'Central upper-part Bystedt short support')+' follows nearest actual primary trajectory, original support length controls travel, 16 real scalp controls with 0.8-2mm loft; main hairstyle/materials/lights unchanged',status='Actual renders pending review',scope='Discrete short support placement, not complete segments/eyes/clothing/animation collision or art acceptance')
(out/'part_undercoat_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PART_UNDERCOAT_SAVED',version,len(ids),flush=True)
