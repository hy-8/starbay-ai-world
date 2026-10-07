"""Shorten camera-attributed part support into a close, flow-aligned scalp veil."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
component=a[a.index('--component')+1] if '--component' in a else 'posterior'
components={'posterior':'Original posterior coverage • surface-grown short fibers','bystedt':'Bystedt derivative • short scalp support','abhay':'Abhay flow derivative • real scalp sampled short support'}
assert component in components and all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
def paths(ob):
    cu=ob.data;n=np.array([c.points_length for c in cu.curves]);assert (n==n[0]).all() and np.array_equal(np.array(ob.matrix_world),np.eye(4))
    p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());return p.reshape(-1,int(n[0]),3).astype(float)
ob=bpy.data.objects[components[component]];cu=ob.data;raw=paths(ob);q=raw.copy();roots=raw[:,0]
mask=(roots[:,0]>-.026)&(roots[:,0]<.051)&(roots[:,2]>1.840)&(roots[:,1]>-.115)&(roots[:,1]<.095)
ids=np.flatnonzero(mask);assert len(ids)>100
main=paths(bpy.data.objects['Bystedt layercut derivative • native root reflow']);tree=KDTree(len(main))
for i,p in enumerate(main[:,0]):tree.insert(Vector(p),i)
tree.balance();body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
N=raw.shape[1];t=np.linspace(0,1,N);distances=[];before_lengths=[];after_lengths=[];controls_travel=[]
for i in ids:
    root=roots[i];_,j,distance=tree.find(Vector(root));donor=main[j];distances.append(float(distance))
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(donor,axis=0),axis=1))]
    original=float(np.linalg.norm(np.diff(raw[i],axis=0),axis=1).sum());before_lengths.append(original)
    L=min(original,.0045+.002*(.5+.5*np.sin(i*2.399963)),arc[-1]*.65);controls_travel.append(L)
    at=np.linspace(0,L,16);controls=np.column_stack([np.interp(at,arc,donor[:,k]) for k in range(3)])+root-donor[0]
    for k in range(1,16):
        hit,n,_,_=bv.find_nearest(Vector(controls[k]));assert hit is not None
        controls[k]=np.array(hit+n*(.00025+.00040*np.sin(np.pi*k/15)))
    controls[0]=root;u=t*15;ix=np.minimum(np.floor(u).astype(int),14);f=(u-ix)[:,None]
    ext=np.vstack([2*controls[0]-controls[1],controls,2*controls[-1]-controls[-2]])
    aa,bb,cc,dd=ext[ix],ext[ix+1],ext[ix+2],ext[ix+3]
    value=.5*(2*bb+(-aa+cc)*f+(2*aa-5*bb+4*cc-dd)*f*f+(-aa+3*bb-3*cc+dd)*f*f*f)
    value[0]=root;q[i]=value;after_lengths.append(float(np.linalg.norm(np.diff(value,axis=0),axis=1).sum()))
assert np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel());ob.data.update_tag()
attr='native_part_short_veil';previous=ob.data.attributes.get(attr)
if previous:ob.data.attributes.remove(previous)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','04_Back','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(render/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
quant=lambda v:np.quantile(v,[0,.5,.9,1]).tolist()
(out/'part_veil_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,component=component,changed_object=ob.name,
    selection_attribute=attr,changed_fibers=len(ids),nearest_actual_primary_root_quantiles_m=quant(distances),
    before_length_quantiles_m=quant(before_lengths),result_length_quantiles_m=quant(after_lengths),donor_control_travel_quantiles_m=quant(controls_travel),
    method='Observed upper/central part support rootsX(-26,+51)mm,Z>1.840m,Y(-115,+95)mm. True follicles retained; nearest current primary root supplies0-to-min(old length,4.5-6.5mm,65% donor arc) departure;16 actual scalp controls at0.25-0.65mm loft. Catmull interpolation retains original support point counts/radii. Control travel cap is not a strict final geometric length cap.',
    status='Actual drafts pending review; no art/continuous collision acceptance.'),indent=2),encoding='utf-8')
print('SHORT_PART_VEIL_SAVED',version,component,len(ids),flush=True)
