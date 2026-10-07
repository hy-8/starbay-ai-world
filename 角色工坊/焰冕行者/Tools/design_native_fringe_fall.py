"""Design smooth directional fringe guides instead of forced crossing reversals."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero(fringe)
features=(raw[ids][:,[0,8,24,40,64]]*np.array([.9,.7,.8,.7,1])[None,:,None]).reshape(len(ids),-1)
K=68;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
for _ in range(1,K):
    best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
centers=np.array(centers)
def assign():return np.argmin(np.maximum(0,(features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T),axis=1)
for _ in range(20):
    labels=assign()
    for k in range(K):
        if (labels==k).any():centers[k]=features[labels==k].mean(0)
labels=assign();t=np.linspace(0,1,65);u=t[:,None]
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
body=bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
mask=np.zeros(len(raw),bool);rows=[];repairs=0
for k in range(K):
    members=ids[labels==k]
    if len(members)<24:continue
    old=raw[members];c=old.mean(0);p0,p3=c[0],c[-1]
    direction=1 if (p3[0] if abs(p3[0])>.010 else p0[0])>0 else -1
    phase=k*2.3999632297
    # Distinct root/terminal groups fall to their own side. The upper arc has
    # one broad bend, without106's across-face sine reversal.
    p1=p0+np.array([direction*(.011+.006*(.5+.5*np.sin(phase))),-.026,.008])
    p1[2]=min(p1[2],1.885)
    p2=p3.copy()
    p2[0]+=direction*(.002+.005*(.5+.5*np.cos(phase*.71)))
    p2[1]-=.004
    p2[2]=p3[2]+.40*(p0[2]-p3[2])
    guide=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*p3
    # Preserve source intra-lock dispersion and the existing exact terminals.
    blend=.92*smooth((t-.055)/.22)
    values=old+(guide-c)[None]*blend[None,:,None]
    for i in range(len(members)):
        for j in range(6,64):
            hit,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-hit).dot(n)
            if dist<.025 and gap<.0012:
                values[i,j]+=np.array(n)*(.0015-gap);repairs+=1
    values[:,:6]=old[:,:6];values[:,-1]=old[:,-1]
    q[members]=values;mask[members]=True
    rows.append(dict(group=k,fibers=len(members),direction=direction,controls_m=[p0.tolist(),p1.tolist(),p2.tolist(),p3.tolist()],
        maximum_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert np.isfinite(q).all() and np.array_equal(q[:,:6],raw[:,:6]) and np.array_equal(q[:,-1],raw[:,-1])
assert np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_directional_fringe_fall'
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
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'fringe_fall_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,
 selection_attribute=attr,changed_fibers=int(mask.sum()),groups=rows,discrete_body_repairs=repairs,
 method='68 actual whole-path fringe groups, native_resculpted_fringe_sweeps region. Root-to-terminal cubic controls fall to own side with11-17mm upper-side displacement/8mm upper lift and40% descent second control,92% mean-flow replacement. Existing intra-lock section, first6 points and every exact terminal preserved; non-fringe/materials/other objects unchanged.',
 status='Actual drafts pending art review; no continuous/eye/animation collision assurance'),indent=2),encoding='utf-8')
print('DIRECTIONAL_FRINGE_FALL',version,int(mask.sum()),len(rows),flush=True)
