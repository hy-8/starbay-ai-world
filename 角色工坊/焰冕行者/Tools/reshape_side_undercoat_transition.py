"""Medium side transition layer on existing support follicles, using main paths."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
component=a[a.index('--component')+1] if '--component' in a else 'abhay'
components={'abhay':'Abhay flow derivative • real scalp sampled short support','posterior':'Original posterior coverage • surface-grown short fibers','bystedt':'Bystedt derivative • short scalp support'}
assert component in components
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
def paths(ob):
 n=np.array([c.points_length for c in ob.data.curves]);assert (n==n[0]).all()
 p=np.empty((len(ob.data.points),3),np.float32);ob.data.attributes['position'].data.foreach_get('vector',p.ravel())
 assert np.array_equal(np.array(ob.matrix_world),np.eye(4));return p.reshape(-1,int(n[0]),3).astype(float)
ob=bpy.data.objects[components[component]];cu=ob.data;raw=paths(ob);q=raw.copy()
main=paths(bpy.data.objects['Bystedt layercut derivative • native root reflow'])
tree=KDTree(len(main))
for i,p in enumerate(main[:,0]):tree.insert(Vector(p),i)
tree.balance()
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
r=raw[:,0];mask=(r[:,0]>.008)&(r[:,2]>1.795)&(r[:,1]<.025)
ids=np.flatnonzero(mask);N=raw.shape[1];t=np.linspace(0,1,N);distances=[];lengths=[];repairs=0
for i in ids:
 old=raw[i];root=old[0];_,j,dist=tree.find(Vector(root));donor=main[j];distances.append(float(dist))
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(donor,axis=0),axis=1))]
 # Existing donor topology supplies the entire side flow, including its bends.
 # Root translation fades so the new short support joins the main flow.
 original_length=np.linalg.norm(np.diff(old,axis=0),axis=1).sum()
 length=min(.105,max(original_length,.65*arc[-1]));length=min(length,.88*arc[-1])
 at=t*length;value=np.column_stack([np.interp(at,arc,donor[:,k]) for k in range(3)])
 fade=np.clip(at/.025,0,1);fade=fade*fade*(3-2*fade)
 value+=(root-donor[0])[None]*(1-fade[:,None])
 # A very small deterministic phase variation; no density increase.
 phase=float(j*2.399963)
 for k in range(1,N):
  hit,n,_,dist=bv.find_nearest(Vector(value[k]));assert hit is not None
  normal=np.array(n);gap=(Vector(value[k])-hit).dot(n)
  if dist<.022 and gap<.0007:value[k]+=normal*(.0007-gap);repairs+=1
  value[k]+=normal*(.00035*np.sin(2*np.pi*at[k]/.045+phase)*np.sin(np.pi*t[k]))
 value[0]=root;q[i]=value;lengths.append(float(np.linalg.norm(np.diff(value,axis=0),axis=1).sum()))
assert len(ids)>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_medium_side_support';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'side_transition_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,component=component,changed_fibers=len(ids),selection_attribute=attr,nearest_donor_root_distance_quantiles_m=np.quantile(distances,[0,.5,.9,1]).tolist(),result_length_quantiles_m=np.quantile(lengths,[0,.5,.9,1]).tolist(),discrete_body_repairs=repairs,all_roots_exact=True,unselected_support_exact=True,main_and_other_hair_exact=True,method='Positive-X upper side '+component+' support follows actual nearest primary donor over65% donor arc, donor travel capped105mm/88% donor; final geometric arc may be longer after root offset/body repairs. Root translation fades over25mm;0.35mm small variation, discrete0.7mm body guard. Existing main/support radii, topology, materials and lights unchanged. This changes support length/shape, not dynamics.',status='Three actual drafts pending review; not artistic or continuous collision acceptance'),indent=2),encoding='utf-8')
print('SIDE_TRANSITION_SAVED',version,len(ids),flush=True)
