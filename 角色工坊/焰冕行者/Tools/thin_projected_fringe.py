"""Delete a reproducible subset of an observed dense fringe lock."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
rate = float(a[a.index('--rate')+1]) if '--rate' in a else .75
center_x = float(a[a.index('--center-x')+1]) if '--center-x' in a else .588
radius_x = float(a[a.index('--radius-x')+1]) if '--radius-x' in a else .022
assert .4 < center_x < .7 and .005 < radius_x < .05
assert 0 < rate <= 1 and all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
out,rd = ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
cu = ob.data
p = np.empty((len(cu.points),3),np.float32)
cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw = p.reshape(-1,65,3)
fringe = np.empty(len(raw),bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
cam = bpy.data.objects['02_ThreeQuarter']
M = np.array(cam.matrix_world.inverted())
P = np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
flat = raw.reshape(-1,3)
clip = np.c_[flat,np.ones(len(flat))]@M.T@P.T
xy = clip[:,:2]/clip[:,3,None]
pixel = np.c_[xy[:,0]*.5+.5,.5-xy[:,1]*.5].reshape(-1,65,2)
inside = np.sum(((pixel-np.array([center_x,.400]))/np.array([radius_x,.115]))**2,axis=2)<1
mask = fringe & (inside[:,10:62].sum(axis=1)>=12)
selected = np.flatnonzero(mask)
remove = selected[np.random.default_rng(175).random(len(selected))<rate]
keep = np.ones(len(raw),bool)
keep[remove] = False
ob.data = cu.copy()
ob.data.remove_curves(indices=remove.tolist())
new = np.empty((len(ob.data.points),3),np.float32)
ob.data.attributes['position'].data.foreach_get('vector',new.ravel())
assert np.array_equal(new.reshape(-1,65,3),raw[keep])
out.mkdir(parents=True)
rd.mkdir(parents=True)
np.savez_compressed(out/'local_retained_indices.npz',retained=np.flatnonzero(keep))
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x,s.render.resolution_y = 1200,1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'thinning_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selected_fibers=len(selected),deleted_fibers=len(remove),remaining_total_fibers=int(keep.sum()),requested_rate=rate,seed=175,ellipse_center=[center_x,.400],ellipse_radii=[radius_x,.115],method='Current fringe,>=12 points10:61 in camera02 ellipse,geometric projection not depth/visibility proof. Delete reproducible random subset; all remaining positions/radii/attributes retained by Blender remove_curves. Actual geometry deletion, no alpha/light/image manipulation.',status='Actual two-view study pending art review'),indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('THIN_FRINGE_RENDERED',version,len(remove),flush=True)
