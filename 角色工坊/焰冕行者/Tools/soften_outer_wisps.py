"""Local, smooth silhouette combing; preserve accepted fringe and real roots."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
probe='--probe' in a
source=ROOT/'Exports'/base/'Ember_Regent.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float)
protected=np.zeros(len(raw),bool)
for name in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
    values=np.empty(len(raw),bool);cu.attributes[name].data.foreach_get('value',values);protected|=values
cam=bpy.data.objects['02_ThreeQuarter']
M=np.array(cam.matrix_world.inverted());P=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
flat=raw.reshape(-1,3);clip=np.c_[flat,np.ones(len(flat))]@M.T@P.T
xy=clip[:,:2]/clip[:,3,None]
uv=np.c_[xy[:,0]*.5+.5,.5-xy[:,1]*.5].reshape(-1,65,2)
center=np.array([.231,.407]);radii=np.array([.026,.029])
dist2=np.sum(((uv-center)/radii)**2,axis=2)
mask=(np.sum(dist2[:,12:]<1,axis=1)>=3)&~protected
ids=np.flatnonzero(mask)
assert 0<len(ids)<2000,len(ids)
record=dict(source=base,source_sha256=digest,selected_fibers=len(ids),selection='Non-fringe, excluding accepted inner curtain; at least3 points12:64 in camera ellipse center(.231,.407),radii(.026,.029). Projection is not visibility proof.',root_quantiles=np.quantile(raw[ids,0],[0,.5,1],axis=0).tolist(),tip_quantiles=np.quantile(raw[ids,-1],[0,.5,1],axis=0).tolist())
if probe:
    out=ROOT/'Exports'/(version+'.json');assert not out.exists()
    out.write_text(json.dumps(record,indent=2),encoding='utf-8');print('WISP_PROBE',json.dumps(record),flush=True);sys.exit(0)
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
q=raw.copy();right=np.array(cam.matrix_world)[:3,0];up=np.array(cam.matrix_world)[:3,1]
u=np.clip((np.linspace(0,1,65)-11/64)/(1-11/64),0,1)
rootfade=np.minimum(u/.2,1);rootfade=rootfade*rootfade*(3-2*rootfade)
for i in ids:
    # Broad Gaussian field relaxes the isolated bow toward the existing mass.
    weight=np.exp(-dist2[i]/2.5)*rootfade
    q[i]+=weight[:,None]*(right*.012-up*.003)
q[:,:12]=raw[:,:12]
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[protected],raw[protected])
assert np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_outer_wisp_relaxation';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
record.update(selection_attribute=attr,preserved_prefix_points=12,accepted_fringe_exact=True,max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method='Smooth Gaussian camera-local12mm inward/3mm downward field; first12 points and accepted fringe exactly preserved. Other geometry/material/light unchanged. No continuous collision claim.',status='Actual two-view study, pending visual review')
(out/'outer_wisp_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('OUTER_WISPS_RENDERED',version,len(ids),flush=True)
