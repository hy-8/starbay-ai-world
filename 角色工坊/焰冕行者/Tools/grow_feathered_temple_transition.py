"""Grow original short temporal transition fibers on the retained scalp surface."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
layered='--layered' in a
upper='--upper' in a
preview='--preview' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
name='Original upper temple transition • scalp-grown fibers' if upper else 'Original feathered temple transition • scalp-grown fibers';assert name not in bpy.data.objects
body=bpy.data.objects['CC0 male body • retained topology'];assert np.allclose(np.array(body.matrix_world),np.eye(4))
dg=bpy.context.evaluated_depsgraph_get();bv=BVHTree.FromObject(body,dg)
ev=body.evaluated_get(dg);mesh=ev.to_mesh();mesh.calc_loop_triangles()
v=np.array([x.co[:] for x in mesh.vertices]);tri=np.array([x.vertices[:] for x in mesh.loop_triangles]);xyz=v[tri];c=xyz.mean(1)
n=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);area=np.linalg.norm(n,axis=1)/2;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
mask=(np.abs(c[:,0])>.032)&(c[:,1]>-.112)&(c[:,1]<-.045)&(c[:,2]>1.790)&(c[:,2]<1.864)&(n[:,2]>-.1)
if upper:mask=(np.abs(c[:,0])>.016)&(c[:,1]>-.115)&(c[:,1]<-.040)&(c[:,2]>1.820)&(c[:,2]<1.893)&(n[:,2]>.15)
if pilot:mask&=c[:,0]>0
xyz=xyz[mask];area=area[mask];assert len(xyz)>20
rng=np.random.default_rng(211213);count=(2600 if pilot else 5200) if layered else (1800 if pilot else 3600);N=36;t=np.linspace(0,1,N)
if upper:count=4200 if pilot else 8400
samples=[]
while len(samples)<count:
 ids=rng.choice(len(xyz),size=count,p=area/area.sum());b=rng.random((count,2));b[b.sum(1)>1]=1-b[b.sum(1)>1]
 pts=xyz[ids,0]+b[:,0,None]*(xyz[ids,1]-xyz[ids,0])+b[:,1,None]*(xyz[ids,2]-xyz[ids,0])
 # Feather density over a measured anatomical ellipse; no hard rectangular hairline.
 r2=((pts[:,1]+.083)/.025)**2+((pts[:,2]-1.826)/.034)**2
 if upper:r2=((pts[:,1]+.079)/.031)**2+((pts[:,2]-1.855)/.029)**2
 probability=np.clip(1-r2,0,1)**.8
 samples.extend(pts[rng.random(count)<probability])
samples=np.array(samples[:count]);paths=np.empty((count,N,3),np.float32);gaps=[];lengths=[]
for i,sample in enumerate(samples):
 hit,normal,_,_=bv.find_nearest(Vector(sample));paths[i,0]=hit+normal*.0005;gaps.append(.0005)
 heading=Vector((float(np.sign(sample[0])*.04),.84,-.42+.18*np.sin(sample[1]*120+sample[2]*70)))
 heading-=normal*heading.dot(normal);heading.normalize()
 length=rng.uniform(.043,.071) if layered else rng.uniform(.023,.045)
 lift=rng.uniform(.0035,.0080) if layered else rng.uniform(.0018,.0045);position=hit
 if upper:length=rng.uniform(.036,.062);lift=rng.uniform(.003,.007)
 for j in range(1,N):
  candidate=position+heading*(length/(N-1));nh,nn,_,_=bv.find_nearest(candidate)
  heading-=nn*heading.dot(nn);heading.normalize();position=nh
  paths[i,j]=nh+nn*(.0005+lift*np.sin(np.pi*t[j])+.0011*t[j]**2)
 lengths.append(float(np.linalg.norm(np.diff(paths[i],axis=0),axis=1).sum()))
ev.to_mesh_clear();assert np.isfinite(paths).all()
cu=bpy.data.hair_curves.new('Original feathered short temple transition');cu.add_curves([N]*count)
cu.attributes['position'].data.foreach_set('vector',paths.ravel())
radius=rng.uniform(.000024,.000035,(count,1))*(1-.997*t[None,:]**2.3)**.7
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.astype(np.float32).ravel())
cu.materials.append(bpy.data.objects['Bystedt layercut derivative • native root reflow'].data.materials[0])
ob=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(ob)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True)
if not preview:bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
method='Area sample actual body scalp; feathered density ellipse in YZ centered(-.083,1.826)m with radii(.025,.034)m. Original backward/downward surface-transport flow,23-45mm step budget,1.8-4.5mm lift,24-35um base radius taper. Existing objects unchanged; not a solid cap or image edit. Root offset0.5mm; sampled surface guard is not continuous collision proof.'
if layered:method=method.replace('23-45mm step budget,1.8-4.5mm lift','43-71mm step budget,3.5-8mm lift')
if upper:method='Original area-sampled upper temporal support, density ellipseYZ(-.079,1.855)m,radii(.031,.029)m; backward/down surface transport,36-62mm step budget,3-7mm lift. Root offset0.5mm; same primary material. Existing geometry untouched. Based on actual component ID of sparse upper transition; sampled surface transport is not continuous collision proof.'
(out/'temple_transition_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,added_object=name,additional_fibers=count,points_per_curve=N,pilot=pilot,layered=layered,upper=upper,model_saved=not preview,length_quantiles_m=np.quantile(lengths,[0,.5,1]).tolist(),method=method),indent=2),encoding='utf-8')
if not pilot:
 cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in (['03_Side','02_ThreeQuarter'] if pilot else ['03_Side','05_OppositeSide','02_ThreeQuarter']):
 s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('FEATHERED_TEMPLE_RENDERED',version,count,flush=True)
