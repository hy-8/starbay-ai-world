"""Probe or soften the actual swept upper locks' terminal turns locally."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,reference=a[:3]
probe='--probe' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
name='Bystedt layercut derivative • native root reflow';hashes={}
def load(v):
    path=ROOT/'Exports'/v/'Ember_Regent.blend';hashes[v]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    cu=bpy.data.objects[name].data;p=np.empty((len(cu.points),3),np.float32)
    cu.attributes['position'].data.foreach_get('vector',p.ravel())
    return p.reshape(-1,65,3).astype(float)
previous=load(reference);raw=load(base)
ob=bpy.data.objects[name];cu=ob.data
swept=np.empty(len(raw),bool);cu.attributes['native_authored_swept_upper'].data.foreach_get('value',swept)
def turns(paths):
    step=np.diff(paths,axis=1);step/=np.maximum(np.linalg.norm(step,axis=2)[:,:,None],1e-9)
    return np.degrees(np.arccos(np.clip(np.sum(step[:,:-1]*step[:,1:],axis=2),-1,1)))
oldturn=turns(previous);newturn=turns(raw)
# Above-head new local end reversals are one diagnostic, not a guarantee of
# which curves actually make the visible silhouette arcs.
peak=(newturn[:,43:]>70)&(newturn[:,43:]>oldturn[:,43:]+25)&(raw[:,44:64,2]>1.845)
mask=swept&peak.any(1)
report=dict(source=base,source_sha256=hashes[base],reference=reference,reference_sha256=hashes[reference],
    swept_fibers=int(swept.sum()),new_high_terminal_turn_fibers=int(mask.sum()),
    terminal_turn_quantiles_deg=np.quantile(newturn[swept,43:],[0,.5,.9,.99,1]).tolist(),
    source_terminal_turn_quantiles_deg=np.quantile(oldturn[swept,43:],[0,.5,.9,.99,1]).tolist(),
    definition='New terminal turns above70deg and25deg above125, at vertexZ>1.845m afterpoint43. Geometry statistic only, no all-view visibility/continuous collision or art proof.')
if probe:
    path=ROOT/'Exports'/(version+'.json');assert not path.exists()
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('SWEPT_END_PROBE',json.dumps(report),flush=True)
else:
    out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
    assert not out.exists() and not renders.exists() and mask.any()
    # Editing full eligible upper end paths, with peak diagnosis included,
    # avoids letting individual bad points remain between corrected samples.
    candidates=swept&(raw[:,-1,2]>1.745)
    ids=np.flatnonzero(candidates);q=raw.copy()
    body=bpy.data.objects['CC0 male body • retained topology']
    assert np.array_equal(np.array(body.matrix_world),np.eye(4))
    bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
    repairs=0
    for index in ids:
        p0=raw[index,42].copy();end=raw[index,-1].copy()
        # Keep126's outward tip location; remove section-induced late reversal
        # using a monotone chord-directed derivative at the released suffix.
        chord=end-p0;distance=np.linalg.norm(chord);direction=chord/max(distance,1e-9)
        initial=raw[index,44]-raw[index,38]
        initial/=max(np.linalg.norm(initial),1e-9)
        if initial.dot(direction)<.35:initial=direction
        p1=p0+initial*distance*.30;p2=end-direction*distance*.25
        u=np.linspace(0,1,23)[:,None]
        q[index,42:]=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end
        offset=np.zeros((65,3))
        for j in range(43,65):
            hit,n,_,dist=bv.find_nearest(Vector(q[index,j]));gap=(Vector(q[index,j])-hit).dot(n)
            if dist<.025 and gap<.0006:offset[j]=np.array(n)*(.0009-gap);repairs+=1
        envelope=offset.copy();mag=np.linalg.norm(offset,axis=1)
        for j in range(43,65):
            lo,hi=max(43,j-3),min(65,j+4);weights=np.maximum(0,1-np.abs(np.arange(lo,hi)-j)/4)
            scores=mag[lo:hi]*weights;h=int(np.argmax(scores))
            if scores[h]>np.linalg.norm(envelope[j]):envelope[j]=offset[lo+h]*weights[h]
        q[index]+=envelope
    assert np.isfinite(q).all() and np.array_equal(q[:,:43],raw[:,:43])
    assert np.array_equal(q[~candidates],raw[~candidates])
    ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
    attr='native_softened_swept_ends';assert not ob.data.attributes.get(attr)
    ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',candidates);ob.data.update_tag()
    out.mkdir(parents=True);renders.mkdir(parents=True)
    s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='OPTIX';pref.get_devices()
    for device in pref.devices:device.use=device.type=='OPTIX'
    s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
    s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
    cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
    ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
    for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
        s.camera=bpy.data.objects[shot];s.render.filepath=str(renders/(shot+'.png'));bpy.ops.render.render(write_still=True)
    report.update(selection_attribute=attr,changed_fibers=len(ids),discrete_body_repairs=repairs,
        method='Actual126 swept upper shafts withendZ>1.745m, individually reconstruct42-64 suffix into average-tangent/chord-directed cubic. First43 points/fringe/other shafts/materials/radii remain; original126 endpoint retained unless discrete body envelope changes it. Reference125 loaded for turn diagnosis, not geometry donor.',
        status='Actual drafts pending art review; no continuous or dynamic collision proof')
    (out/'swept_ends_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('SOFTENED_SWEPT_ENDS',version,len(ids),flush=True)
for v,h in hashes.items():assert hashlib.sha256((ROOT/'Exports'/v/'Ember_Regent.blend').read_bytes()).hexdigest()==h
