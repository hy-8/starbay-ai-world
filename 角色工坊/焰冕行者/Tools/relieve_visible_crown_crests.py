"""Restore only camera-observed overraised crown curls from protected donor."""
import bpy, sys, re, json, hashlib, numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:]; version,base,donor=a[:3]
front_part='--front-part' in a
both_views='--both-views' in a
coherent_groups='--coherent-groups' in a
if both_views and front_part:raise ValueError('Choose both views or one front view')
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
assert not out.exists() and not render.exists()
name='Bystedt layercut derivative • native root reflow'
def read(ver):
    path=ROOT/'Exports'/ver/'Ember_Regent.blend'; digest=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);cu=bpy.data.objects[name].data
    p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
    return path,digest,p.reshape(-1,65,3).copy()
donorpath,donorhash,old=read(donor);source,digest,raw=read(base)
ob=bpy.data.objects[name];cu=ob.data;loft=np.empty(len(raw),bool)
cu.attributes['native_layered_root_lofts'].data.foreach_get('value',loft)
assert np.array_equal(old[:,0],raw[:,0]) and np.array_equal(old[:,44:],raw[:,44:])
s=bpy.context.scene; cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
probe_camera=bpy.data.objects['01_Front'] if front_part else cam
M=np.array(probe_camera.matrix_world.inverted());P=np.array(probe_camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
def project(paths):
    points=paths[:,:44].reshape(-1,3);clip=np.c_[points,np.ones(len(points))]@M.T@P.T;xy=clip[:,:2]/clip[:,3,None]
    return np.c_[(xy[:,0]*.5+.5)*1200,(.5-xy[:,1]*.5)*1400].reshape(-1,44,2)
pixels=project(raw);prior=project(old)
center=[535,348] if front_part else [480,395]; radii=[70,42] if front_part else [140,55]
lift_pixels=12 if front_part else 10
roi=(((pixels-center)/radii)**2).sum(axis=2)<1
lifted=(prior[:,:,1]-pixels[:,:,1])>lift_pixels
mask=loft & ((roi & lifted).sum(axis=1)>=2)
if both_views:
    probe_camera=bpy.data.objects['01_Front'];M=np.array(probe_camera.matrix_world.inverted())
    P=np.array(probe_camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
    front_pixels=project(raw);front_prior=project(old)
    front_roi=(((front_pixels-[535,348])/[70,42])**2).sum(axis=2)<1
    front_lifted=(front_prior[:,:,1]-front_pixels[:,:,1])>12
    mask|=loft & ((front_roi & front_lifted).sum(axis=1)>=2)
point_selected=int(mask.sum());closed_groups=[]
if coherent_groups:
    # Reproduce90's exact source-path partition; edit whole coherent locks,
    # avoiding a few elevated fibers left standing inside a partly restored lock.
    frame=np.empty(len(raw),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
    roots=old[:,0];eligible=np.flatnonzero((~frame)&(roots[:,2]>1.830)&(roots[:,1]<.065))
    features=(old[eligible].astype(float)[:,[0,8,16,24,40]]*np.array([.7,.9,1.,1.,.4])[None,:,None]).reshape(len(eligible),-1)
    K=150;centers=[features[len(features)//2]];best=np.full(len(features),np.inf)
    for _ in range(1,K):
        best=np.minimum(best,np.sum((features-centers[-1])**2,axis=1));centers.append(features[np.argmax(best)])
    centers=np.array(centers)
    def assign():return np.argmin(np.maximum(0,(features*features).sum(axis=1)[:,None]+(centers*centers).sum(axis=1)[None]-2*features@centers.T),axis=1)
    for _ in range(24):
        labels=assign()
        for k in range(K):
            if (labels==k).any():centers[k]=features[labels==k].mean(axis=0)
    labels=assign();closed=np.zeros(len(raw),bool)
    for k in range(K):
        ids=eligible[labels==k]
        if len(ids)>=30 and mask[ids].mean()>=.30:
            closed[ids]=True;closed_groups.append(dict(group=k,fibers=len(ids),initial_roi_fraction=float(mask[ids].mean())))
    assert np.array_equal(loft[eligible],np.array([int((labels==k).sum())>=30 for k in labels]))
    mask=closed
assert mask.sum()>10 and mask.sum()<loft.sum()*(.60 if coherent_groups else .40)
q=raw.copy();q[mask]=old[mask]
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[:,44:],raw[:,44:]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.ravel());ob.data.update_tag()
attr='native_visible_crest_relief';previous=ob.data.attributes.get(attr)
if previous:ob.data.attributes.remove(previous)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
# The opposite diagnostic camera is temporary: restore the original object set
# before saving, then add it back for actual opposite-side draft renders.
bpy.data.objects.remove(cam,do_unlink=True)
out.mkdir(parents=True);render.mkdir(parents=True)
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(render/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donorpath.read_bytes()).hexdigest()==donorhash
(out/'crest_relief_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,donor=donor,donor_sha256=donorhash,
    selection_attribute=attr,eligible_lofted_fibers=int(loft.sum()),changed_fibers=int(mask.sum()),
    both_views=both_views,coherent_groups=coherent_groups,point_roi_selected_fibers=point_selected,closed_groups=closed_groups,
    roi=dict(camera='01_Front' if front_part else '05_OppositeSide',resolution=[1200,1400],ellipse_center_pixels=center,ellipse_radii_pixels=radii,
    minimum_screen_lift_pixels=lift_pixels,minimum_points=2,source='Manually inspected actual92 front render; ellipse covers left-of-part raised crest' if front_part else 'Manually inspected actual90 opposite render; ellipse covers conspicuous raised crown loops'),
    secondary_roi=dict(camera='01_Front',resolution=[1200,1400],ellipse_center_pixels=[535,348],ellipse_radii_pixels=[70,42],minimum_screen_lift_pixels=12,minimum_points=2) if both_views else None,
    donor_full_paths_exact=True,all_roots_exact=True,all_points44_through64_exact=True,unselected_primary_exact=True,
    method=f'Only already lofted shafts with at least2 saved first44 points in the observed {"opposite+front" if both_views else "front part" if front_part else "opposite crest"} ellipse and required upward displacement versus86 are candidates.'+(' Reproduce90 source whole-path150-group partition; restore entire minimum30-fiber groups with>=30% ROI membership, avoiding partial-lock leftovers.' if coherent_groups else ' Restore selected individual shafts.')+' Restored full paths exactly match86; all other lofts and complete tails retained.',
    status='Actual drafts pending review; camera-point ROI is not ray visibility or artistic/continuous collision acceptance.'),indent=2),encoding='utf-8')
print('VISIBLE_CREST_RELIEF',version,int(mask.sum()),flush=True)
