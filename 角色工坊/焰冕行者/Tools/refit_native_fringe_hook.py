"""Local foreground end study from inspected source-camera ROIs.

Projection is selection guidance, not an occlusion or causal proof.
"""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];probe='--probe' in a
roi_hit_only='--roi-hit-only' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
ids=np.flatnonzero(fringe);hits=np.zeros(len(raw),bool)
rois=[('02_ThreeQuarter',(.572,.479),(.020,.018)),('01_Front',(.645,.477),(.018,.019))]
scene=bpy.context.scene
for camera,center,radius in rois:
    cam=bpy.data.objects[camera]
    for i in ids:
        for j in range(56,65):
            v=world_to_camera_view(scene,cam,ob.matrix_world@Vector(raw[i,j]))
            if v.z>0 and ((v.x-center[0])/radius[0])**2+((1-v.y-center[1])/radius[1])**2<=1:
                hits[i]=True;break
diff=np.diff(raw[:,55:],axis=1);unit=diff/np.maximum(np.linalg.norm(diff,axis=2)[:,:,None],1e-10)
turn=np.degrees(np.arccos(np.clip(np.sum(unit[:,:-1]*unit[:,1:],axis=2),-1,1)))
peak=turn.max(1);mask=fringe&hits&(peak>35);selected=np.flatnonzero(mask)
if roi_hit_only:mask=fringe&hits;selected=np.flatnonzero(mask)
report=dict(source=base,source_sha256=digest,roi_definition=rois,
    terminal_roi_fibers=int((fringe&hits).sum()),selected_turn_fibers=int(mask.sum()),
    roi_terminal_turn_quantiles_deg=np.quantile(peak[fringe&hits],[0,.5,.9,.99,1]).tolist() if hits.any() else [],
    criterion='Current fringe terminal points56-64 in either inspected camera ellipse and last9-point maxturn>35deg. Projection/turn statistics are not occlusion, sole visible-hook attribution or continuous collision proof.')
if roi_hit_only:
    report['criterion']='Current fringe terminal points56-64 in either inspected camera ellipse, without turn gate. A local endpoint-spacing counterexample after140 found zero high-turn shafts. Projection is not an occlusion or crowding cause proof.'
if probe:
    output=ROOT/'Exports'/(version+'.json');assert not output.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    output.write_text(json.dumps(report,indent=2),encoding='utf-8');print('FRINGE_HOOK_PROBED',int(mask.sum()),flush=True)
    raise SystemExit(0)
out,rd=ROOT/'Exports'/version,ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
assert 0<len(selected)<1000,(len(selected),report)
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());repairs=0
u=np.linspace(0,1,13)[:,None]
for i in selected:
    p0=raw[i,52].copy();end=raw[i,64].copy()+np.array([0.,-.004,-.003])
    if roi_hit_only:end+=np.array([.002*np.sin(i*2.399963),0.,.002*np.cos(i*2.399963)])
    hit,n,_,dist=bv.find_nearest(Vector(end));gap=(Vector(end)-hit).dot(n)
    if dist<.025 and gap<.0025:end+=np.array(n)*(.003-gap)
    chord=end-p0;length=np.linalg.norm(chord);direction=chord/max(length,1e-9)
    tangent=raw[i,52]-raw[i,48];tangent/=max(np.linalg.norm(tangent),1e-9)
    if tangent.dot(direction)<.35:tangent=direction
    p1=p0+tangent*length*.33;p2=end-direction*length*.24
    q[i,52:]=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*end
    for j in range(53,64):
        hit,n,_,dist=bv.find_nearest(Vector(q[i,j]));gap=(Vector(q[i,j])-hit).dot(n)
        if dist<.025 and gap<.0012:q[i,j]+=np.array(n)*(.0016-gap);repairs+=1
assert np.array_equal(q[:,:53],raw[:,:53]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_local_fringe_end_release' if roi_hit_only else 'native_local_fringe_hook_release'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400;scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
report.update(selection_attribute=attr,changed_fibers=int(mask.sum()),intermediate_body_repairs=repairs,
    method='Only actual ROI/turn-selected fringe tails refit frompoint52 into individual tangent/chord cubic. Endpoint allowed4mm forward/3mm down and3mm signed body point clearance. Exact points0-52/radii/topology/unselected/materials/lighting preserved. Intermediate point guard is not continuous collision proof.',
    status='Actual drafts pending aesthetic inspection, not reference complete')
if roi_hit_only:report['endpoint_spacing_method']='Actual ROI-hit shafts only, additional deterministic+-2mm lateral/vertical endpoint stagger. No claim that140 showed sharp turns or proved all dark-tip visibility causes.'
(out/'hook_release_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();scene.collection.objects.link(cam);cam.name='05_OppositeSide'
reflect=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflect@cam.matrix_world@reflect
for shot in ['02_ThreeQuarter','01_Front','03_Side','05_OppositeSide']:
    scene.camera=bpy.data.objects[shot];scene.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('LOCAL_FRINGE_HOOK_REFIT',version,int(mask.sum()),flush=True)
