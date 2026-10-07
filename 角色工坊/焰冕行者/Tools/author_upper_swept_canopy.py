"""Author nonperiodic upper-front canopy guides from actual scalp follicles."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]; version, base = a[:2]
hero_only = '--hero-only' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out, renders = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not renders.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']; cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
raw = p.reshape(-1, 65, 3).astype(float); q = raw.copy(); r = raw[:, 0]
frame = np.empty(len(raw), bool)
cu.attributes['native_front_frame_sculpture'].data.foreach_get('value', frame)
eligible = np.flatnonzero((~frame)&(r[:, 2]>1.840)&(r[:, 1]<.025)&(r[:, 1]>-.108)&(np.abs(r[:, 0])<.073))
if hero_only:
    eligible = np.flatnonzero((~frame)&(r[:, 2]>1.862)&(r[:, 1]<.035)&(r[:, 1]>-.099)&(np.abs(r[:, 0])<.046))
root = r[eligible]; K = 36 if hero_only else 64
# Cluster follicles separately on either side of the designed offset part.
features = root.copy(); features[:, 0] += np.where(root[:, 0] < -.008, -.08, .08)
centers = [features[len(features)//2]]; best = np.full(len(features), np.inf)
for _ in range(1, K):
    best = np.minimum(best, np.sum((features-centers[-1])**2, axis=1))
    centers.append(features[np.argmax(best)])
centers = np.array(centers)
def assign():
    return np.argmin(np.maximum(0, (features*features).sum(1)[:,None]+(centers*centers).sum(1)[None]-2*features@centers.T), axis=1)
for _ in range(24):
    labels = assign()
    for k in range(K):
        if (labels==k).any(): centers[k] = features[labels==k].mean(0)
labels = assign()
body = bpy.data.objects['CC0 male body • retained topology']
assert np.array_equal(np.array(body.matrix_world), np.eye(4))
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, 65); u = t[:,None]
def smooth(x):
    x=np.clip(x,0,1); return x*x*(3-2*x)
rows=[]; mask=np.zeros(len(raw),bool); repairs=0
for k in range(K):
    ids = eligible[labels==k]
    if len(ids)<35: continue
    roots=r[ids]; c=roots.mean(0); side=-1 if c[0]<-.008 else 1
    phi=k*2.399963; seed=np.sin(phi)
    height=float(np.clip((c[2]-1.840)/.045,0,1))
    depth=float(np.clip((c[1]+.108)/.133,0,1))
    _, n, _, _ = bv.find_nearest(Vector(c)); normal=np.array(n)
    # Each lock has a single broad swept C/S silhouette. No repeated sine curl.
    heading=np.array([side*.8,-.9,.18]); heading-=normal*np.dot(heading,normal)
    heading/=max(np.linalg.norm(heading),1e-9)
    c1=c+heading*.018+normal*(.009+.003*(.5+.5*seed))
    end=np.array([side*(.079+.010*seed+.010*depth), -.140+.048*depth+.008*np.cos(phi),
                  1.790+.043*height+.010*np.cos(phi*.73)])
    c2=np.array([side*(.098+.008*np.cos(phi)), -.160+.045*depth,
                 max(end[2]+.027, 1.857+.009*seed)])
    if hero_only:
        # Limited crown hero locks fall toward the forehead rather than all
        # forming one smooth side-combed canopy. Existing98 coverage remains.
        c1=c+heading*.021+normal*(.012+.006*(.5+.5*seed))
        end=np.array([side*(.026+.052*(.5+.5*seed)), -.163-.009*np.cos(phi),
                      1.777+.037*(.5+.5*np.sin(phi*.73))+.014*depth])
        c2=np.array([end[0]+side*(.012+.011*np.cos(phi)), -.175+.015*depth,
                     1.838+.021*seed])
    guide=(1-u)**3*c+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
    values=guide[None]+(roots-c)[:,None]*(1-.82*smooth((t-.06)/.84))[None,:,None]
    for local,i in enumerate(ids):
        fiberseed=np.sin(i*2.399963)
        # Irregular tips and modest internal separation without new guide waves.
        values[local,:,2]+=.005*fiberseed*smooth((t-.50)/.50)
        values[local,:,0]+=.0007*fiberseed*np.sin(np.pi*t)
        for j in range(1,65):
            hit, nn, _, dist=bv.find_nearest(Vector(values[local,j]))
            gap=(Vector(values[local,j])-hit).dot(nn)
            if dist<.03 and gap<.0005:
                values[local,j]+=np.array(nn)*(.0007-gap); repairs+=1
    values[:,0]=roots; q[ids]=values; mask[ids]=True
    rows.append(dict(group=k,fibers=len(ids),root_center_m=c.tolist(),control1_m=c1.tolist(),control2_m=c2.tolist(),end_m=end.tolist(),
        maximum_displacement_m=float(np.linalg.norm(values-raw[ids],axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all()
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[frame],raw[frame]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_authored_upper_canopy'
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);renders.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','01_Front','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'upper_canopy_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selection_attribute=attr,
    eligible_fibers=len(eligible),changed_fibers=int(mask.sum()),edited_groups=len(rows),groups=rows,discrete_body_repairs=repairs,
    hero_only=hero_only,
    method=('Limited high central crown rootsZ>1.862m, absX<46mm, Y(-99,+35)mm;36 follicle groups,12-18mm normal departure, staggered front-falling tips, original surrounding98 hair retained' if hero_only else 'New full65-point upper-front canopy, actual follicles;64 scalp clusters split across offset partX=-8mm, minimum35 fibers. Scalp-tangent cubic first control, single broad swept silhouettes, root-height/depth staggered tips')+',82% root scatter taper,5mm irregular terminal scatter; no periodic curls. Roots/explicit foreground/other components/materials/lights retained.',
    status='Actual draft awaiting artistic review, no continuous collision or completion acceptance.'),indent=2),encoding='utf-8')
print('UPPER_CANOPY_AUTHORED',version,int(mask.sum()),flush=True)
