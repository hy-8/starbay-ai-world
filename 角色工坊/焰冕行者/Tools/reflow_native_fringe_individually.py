"""Individual scalp-tangent cubic fringe: avoid transferred section crossings."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,rd=ROOT/'Exports'/version,ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero(fringe)
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
u=np.linspace(0,1,65)[:,None]
repairs=relocated=lowered=0;lead_lengths=[]
def unit(x):return x/max(np.linalg.norm(x),1e-9)
for index in ids:
    old=raw[index];p0,p3=old[0].copy(),old[-1].copy()
    if p3[2]>p0[2]-.030:p3[2]=p0[2]-.035;lowered+=1
    hit,n,_,dist=bv.find_nearest(Vector(p3));gap=(Vector(p3)-hit).dot(n)
    if dist<.025 and gap<.0018:p3+=np.array(n)*(.0022-gap);relocated+=1
    hit,n,_,_=bv.find_nearest(Vector(p0));normal=np.array(n);chord=p3-p0
    tangent=chord-normal*chord.dot(normal)
    if np.linalg.norm(tangent)<.004:
        tangent=old[12]-p0;tangent-=normal*tangent.dot(normal)
    tangent=unit(tangent);length=float(np.clip(np.linalg.norm(chord)*.38,.023,.062))
    lead_lengths.append(length)
    relief=.004+.002*(.5+.5*np.sin(index*2.399963))
    p1=p0+tangent*length+normal*relief
    p2=p3-.28*chord
    values=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*p3
    # Each curve connects its OWN root/end. No mean lock, rolled section,
    # radial ranks or source scatter transport is used in the new geometry.
    correction=np.zeros((65,3))
    for j in range(1,64):
        hit,n,_,dist=bv.find_nearest(Vector(values[j]));gap=(Vector(values[j])-hit).dot(n)
        if dist<.025 and gap<.0008:
            correction[j]=np.array(n)*(.0011-gap);repairs+=1
    envelope=correction.copy();mag=np.linalg.norm(correction,axis=1)
    for j in range(1,64):
        lo,hi=max(1,j-4),min(64,j+5);w=np.maximum(0,1-np.abs(np.arange(lo,hi)-j)/5)
        scores=mag[lo:hi]*w;h=int(np.argmax(scores))
        if scores[h]>np.linalg.norm(envelope[j]):envelope[j]=correction[lo+h]*w[h]
    values+=envelope;values[0]=p0;values[-1]=p3;q[index]=values
assert np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~fringe],raw[~fringe])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_individual_fringe_fall';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',fringe);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'individual_fringe_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,
    selection_attribute=attr,changed_fibers=int(fringe.sum()),lowered_high_endpoints=lowered,
    designed_body_endpoint_relocations=relocated,intermediate_discrete_body_repairs=repairs,
    lead_length_range_m=[min(lead_lengths),max(lead_lengths)],
    method='Every actual current fringe shaft gets individual cubic guide from its own true root to own current end, high endpoints allowed to descend35mm belowroot and near-body endpoints allowed2.2mm clearance. Initial scalp-projected chord tangent23-62mm with4-6mm normal relief, second control28% backward alongown chord. No group mean or transported scatter. Radii/topology/non-fringe/materials/lighting retained. Discrete intermediate0.8/1.1mm body guard with4-point envelope, not continuous collision acceptance.',
    status='Actual drafts pending aesthetic inspection, no reference completion claim'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflect@cam.matrix_world@reflect
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('INDIVIDUAL_FRINGE_RENDERED',version,int(fringe.sum()),flush=True)
