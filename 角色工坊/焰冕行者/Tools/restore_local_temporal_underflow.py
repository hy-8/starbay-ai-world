"""Restore a local portion of proven source coverage beneath the new side locks."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,donor=a[:3]
layered_floor='--layered-floor' in a
long_lock_floor='--long-lock-floor' in a
front_foundation='--front-foundation' in a
if front_foundation:layered_floor=True
if long_lock_floor:layered_floor=True
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:3])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
name='Bystedt layercut derivative • native root reflow'
def load(v):
 path=ROOT/'Exports'/v/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 ob=bpy.data.objects[name];cu=ob.data;p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
 return path,digest,p.reshape(-1,65,3).copy()
donorpath,donorhash,old=load(donor);source,digest,current=load(base);ob=bpy.data.objects[name];cu=ob.data
assert np.array_equal(current[:,0],old[:,0]);selected=np.empty(len(current),bool);cu.attributes['native_relaxed_side_locks'].data.foreach_get('value',selected)
camera=bpy.data.objects['03_Side'];M=np.array(camera.matrix_world.inverted());P=np.array(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
def footprint(paths):
 points=paths[:,:40].reshape(-1,3);clip=np.c_[points,np.ones(len(points))]@M.T@P.T;xy=clip[:,:2]/clip[:,3,None]
 pixels=np.c_[(xy[:,0]*.5+.5)*1200,(.5-xy[:,1]*.5)*1400].reshape(-1,40,2)
 distance=(((pixels-[560,615])/[88,63])**2).sum(axis=2)
 return (distance<1).sum(axis=1),distance.min(axis=1)
old_count,old_dist=footprint(old);new_count,new_dist=footprint(current)
eligible=np.flatnonzero(selected&(old_count>=4)&(new_count<old_count*.65))
# Interleaved shafts leave the authored curls intact while returning a thin
# local backing. Full old paths come from the exact protected donor file.
ids=eligible[eligible%3!=0]
if layered_floor:
 eligible=np.flatnonzero(selected);ids=eligible[eligible%4==0]
 if long_lock_floor:ids=eligible[eligible%5<2]
 if front_foundation:eligible=np.flatnonzero(selected&(current[:,0,1]<-.020));ids=eligible
assert len(ids)>50
mask=np.zeros(len(current),bool);mask[ids]=True;q=current.copy();q[ids]=old[ids]
assert np.array_equal(q[:,0],current[:,0]) and np.array_equal(q[~mask],current[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.ravel());ob.data.update_tag()
attr='native_temporal_coverage_restore';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for shot in ['03_Side','02_ThreeQuarter','01_Front']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(render/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest and hashlib.sha256(donorpath.read_bytes()).hexdigest()==donorhash
method=('Keep exact longer authored donor81 paths on already edited front-facing rootsY<-20mm; leave tiered82 back-facing paths. This anatomically ordered front/back mixture avoids thinning the temple while preserving rear tier scatter. Original total strand density retained.' if front_foundation else 'Retain about60% tiered short canopy and restore index-interleaved40% exact longer authored donor paths as a curved foundation. Selected hair index modulo5<2; actual count recorded. Original total strand density retained.' if long_lock_floor else 'Keep about75% newly authored side locks and restore index-interleaved25% exact donor full paths as distributed foundation. Original total strand density retained.' if layered_floor else 'Select already reshaped shafts with>=4 old first40 points inside side-view ellipse and new point count<65% old;restore2/3 index-interleaved exact donor paths. Screen-point attribution only, not ray visibility.')
(out/'coverage_restore_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,donor=donor,donor_sha256=donorhash,eligible_shafts=len(eligible),changed_fibers=len(ids),selection_attribute=attr,layered_floor=layered_floor,long_lock_floor=long_lock_floor,front_foundation=front_foundation,roi=None if layered_floor else dict(camera='03_Side',resolution=[1200,1400],center_pixels=[560,615],ellipse_radii_pixels=[88,63],selected_from='Manually observed sparse temple in actual82 side render'),all_roots_exact=True,donor_paths_exact=True,unselected_primary_exact=True,method=method+' No new source/geometry density/material/light changes; no continuous collision proof.',status='Actual drafts pending review; not artistic/continuous collision acceptance'),indent=2),encoding='utf-8')
print('TEMPORAL_UNDERFLOW_RESTORED',version,len(ids),len(eligible),flush=True)
