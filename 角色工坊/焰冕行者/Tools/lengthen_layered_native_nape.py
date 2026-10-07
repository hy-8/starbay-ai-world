"""Lengthen actual posterior shafts into a staggered concert wolf-cut silhouette."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
collar_aware = '--collar-aware' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
cu=ob.data
p=np.empty((len(cu.points),3),np.float32)
cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();r=raw[:,0]
fringe=np.empty(len(raw),bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
# Real posterior long hair only, avoiding the fringe and low-root short supports.
ids=np.flatnonzero((~fringe)&(r[:,1]>-.018)&(raw[:,-1,2]<1.760)&
                  (raw[:,-1,2]>1.640)&(r[:,2]>1.735))
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
garments=[]
if collar_aware:
    for name in ['Tailored standing rear collar', 'Fitted CC0 male_elegantsuit01']:
        garment=bpy.data.objects[name]
        mesh=garment.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        garments.append(BVHTree.FromPolygons([garment.matrix_world@v.co for v in mesh.vertices],
            [list(poly.vertices) for poly in mesh.polygons]))
        garment.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
t=np.linspace(0,1,65)
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
flow=smooth((t-.28)/.72)
repairs=0
collar_repairs=0
extension=[]
for index in ids:
    old=raw[index];root=r[index]
    # Smooth root-space variation creates distinct long/short layers.
    ph=root[0]*58+root[1]*31
    length=.030+.040*(.5+.5*np.sin(ph))
    side=np.sign(old[-1,0])
    value=old.copy()
    value[:,2]-=length*flow
    value[:,0]+=side*(.003+.006*(.5+.5*np.cos(ph)))*np.sin(np.pi*t)*flow
    value[:,1]+=(.005+.007*(.5+.5*np.cos(ph*.71)))*flow
    # Loose terminal direction: each original shaft keeps its smooth local path.
    value[:,0]+=.0015*np.sin(index*2.399963)*smooth((t-.74)/.26)
    for j in range(6,65):
        hit,n,_,dist=bv.find_nearest(Vector(value[j]));gap=(Vector(value[j])-hit).dot(n)
        if dist<.03 and gap<.001:
            value[j]+=np.array(n)*(.0013-gap);repairs+=1
    if collar_aware:
        required=np.zeros(65)
        for j in range(6,65):
            if value[j,2]>1.670:continue
            for collider in garments:
                hit,n,_,dist=collider.ray_cast(Vector((value[j,0],.5,value[j,2])),Vector((0,-1,0)),1.)
                if hit is not None and value[j,1]<hit.y+.003:
                    required[j]=max(required[j],hit.y+.003-value[j,1])
        # Expand the clearance envelope along the shaft, avoiding a sudden bend
        # at the garment's uppermost polygon. All constrained points still clear.
        envelope=required.copy()
        for shift in range(1,9):
            envelope[:-shift]=np.maximum(envelope[:-shift],required[shift:]*(1-shift/10))
            envelope[shift:]=np.maximum(envelope[shift:],required[:-shift]*(1-shift/10))
        envelope[:6]=0
        value[:,1]+=envelope
        collar_repairs+=int((required>0).sum())
    value[:6]=old[:6];q[index]=value;extension.append(length)
mask=np.zeros(len(raw),bool);mask[ids]=True
assert len(ids)>100 and np.isfinite(q).all() and np.array_equal(q[:,:6],raw[:,:6])
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[fringe],raw[fringe])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_layered_nape_extension'
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','03_Side','05_OppositeSide','04_Back']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'nape_length_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,
 selection_attribute=attr,changed_fibers=len(ids),designed_extension_quantiles_m=np.quantile(extension,[0,.5,1]).tolist(),
 final_tip_z_quantiles_m=np.quantile(q[ids,-1,2],[0,.5,1]).tolist(),discrete_body_repairs=repairs,
 collar_aware=collar_aware,garment_ray_clearance_points=collar_repairs,
 method='Actual posterior roots Y>-18mm/Z>1.735m, tips1.640-1.760m excluding106 frontal sweeps. Root-space30-70mm downward layered extension, loose rearward/lateral terminal flow. First6 points/source follicle/radii/topology/materials and other components retained. Old short-nape1.640m gate is deliberately not an aesthetic requirement.'+(' Optional collar-aware mode casts from positiveY against world-space evaluated collar/suit meshes; 3mm rear-surface point clearance with8-point expanded offset envelope. This is a discrete static guard, not continuous or dynamic collision.' if collar_aware else ''),
 status='Drafts pending artistic review; no continuous body/clothing/motion collision claim'),indent=2),encoding='utf-8')
print('LAYERED_NAPE_LENGTHENED',version,len(ids),flush=True)
