"""Stagger existing fringe tips by measured polyline distance, no new locks."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
outer_tail='--outer-tail' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float)
selected=np.empty(len(raw),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',selected)
if outer_tail:
    cam=bpy.data.objects['02_ThreeQuarter']
    M=np.array(cam.matrix_world.inverted());P=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
    clip=np.c_[raw[:,-1],np.ones(len(raw))]@M.T@P.T
    xy=clip[:,:2]/clip[:,3,None];uv=np.c_[xy[:,0]*.5+.5,.5-xy[:,1]*.5]
    selected=(uv[:,0]<.225)&(uv[:,1]>.45)&(uv[:,1]<.57)
ids=np.flatnonzero(selected);assert len(ids)>100
# Reproducible individual variation, not a common terminal plane or group tip.
rng=np.random.default_rng(184);jitter=rng.random(len(raw))
mask=selected & (jitter>.15);q=raw.copy();cuts=[]
if outer_tail:mask=selected
for i in np.flatnonzero(mask):
    old=raw[i];s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
    assert np.all(np.diff(s)>0)
    # Preserve crown and the first half of the approved curtain arc exactly.
    tail=s[-1]-s[32]
    cut=min(.009+.009*jitter[i],tail*.45) if outer_tail else min(.0008+.0052*jitter[i]**1.4,tail*.18)
    u=np.clip((s-s[32])/tail,0,1);target=s-cut*u*u*(3-2*u)
    assert np.all(np.diff(target)>0)
    for axis in range(3):q[i,:,axis]=np.interp(target,s,old[:,axis])
    q[i,:33]=old[:33];cuts.append(cut)
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[:,:33],raw[:,:33])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_projected_outer_tip_trim' if outer_tail else 'native_accepted_fringe_tip_feathering'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
record=dict(source=base,source_sha256=digest,selected_fibers=int(mask.sum()),candidate_curtain_fibers=int(selected.sum()),selection_attribute=attr,preserved_prefix_points=33,polyline_trim_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist(),max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method='Measured source-polyline arclength remapping after point32. Seed184,15 percent untouched accents,0.8-6mm source-path trim limited to18 percent of remaining path. No shared endpoint plane. Own flow and first33 points retained; original radii/topology unchanged. Not continuous collision or exact spline-arclength proof.',status='Actual two-view study awaiting review')
if outer_tail:
    record['method']='Camera02_ThreeQuarter projected terminalU<.225,V(.45,.57),all primary families eligible. Not visibility proof. Seed184 individual9-18mm source-polyline trimming,limited45 percent afterpoint32,first33 points/radii/topology retained. Same smooth own-path remap; no new geometry. No collision acceptance.'
    record['candidate_curtain_fibers']=None
(out/'tip_feather_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('ACCEPTED_FRINGE_FEATHERED',version,int(mask.sum()),flush=True)
