"""Own-strand fringe endpoint redesign; actual editable curves, no image substitution."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
pilot = '--pilot' in a
free_flow = '--free-root-flow' in a
feather = '--feather-tips' in a
trimmed = '--trimmed-feather' in a
front_upper = '--front-upper' in a
assert not trimmed or feather
prefix = 1 if free_flow else 6
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
out, rd = ROOT/'Exports'/version, ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
assert np.array_equal(np.array(ob.matrix_world), np.eye(4))
cu = ob.data
p = np.empty((len(cu.points),3),np.float32)
cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw = p.reshape(-1,65,3).astype(float)
mask = np.empty(len(raw),bool)
cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',mask)
fringe_count = int(mask.sum())
upper_count = 0
if front_upper:
    upper = np.empty(len(raw),bool)
    cu.attributes['native_descending_fine_locks'].data.foreach_get('value',upper)
    upper &= (raw[:,0,1] < -.015) & (raw[:,-1,1] < -.080)
    upper_count = int((upper & ~mask).sum())
    mask |= upper
if pilot: mask &= raw[:,0,0] > 0
ids = np.flatnonzero(mask)
bv = BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
q = raw.copy()
t = np.linspace(0,1,65)
blend = np.clip((t-t[5])/.24,0,1)
blend = blend*blend*(3-2*blend)
if free_flow: blend[:] = 1
repairs = endpoint_repairs = 0
def unit(v): return v/max(np.linalg.norm(v),1e-9)
for i in ids:
    old = raw[i]
    root = old[0]
    end = old[-1].copy()
    # Contract the inherited curtain opening; front clearance is independent
    # of its old endpoint. Correlated variation avoids per-strand white noise.
    end[0] *= (.75 if trimmed else .68) if feather else .78
    end[1] -= .010
    end[2] += .005*np.sin(root[0]*95+root[1]*50)
    if feather:
        rng = np.random.default_rng(17000+int(i))
        # Each individual hair has a modest length/width stagger, so inherited
        # shared pointed tips no longer all reconnect to a single spike.
        end += np.array([rng.uniform(-.0006,.0006),rng.uniform(-.0005,.0005),rng.uniform(.002,.014) if trimmed else rng.uniform(-.005,.008)])
        if trimmed and abs(end[0]) < .065: end[2] = max(end[2],1.755)
    hit, normal, _, distance = bv.find_nearest(Vector(end))
    gap = (Vector(end)-hit).dot(normal)
    if distance < .025 and gap < .002:
        end += np.array(normal)*(.0025-gap)
        endpoint_repairs += 1
    hit, normal, _, _ = bv.find_nearest(Vector(root))
    normal = np.array(normal)
    chord = end-root
    tangent = unit(chord-normal*np.dot(chord,normal))
    lead = float(np.clip(np.linalg.norm(chord)*.32,.024,.045))
    c1 = root+tangent*lead+normal*(.009 if free_flow else .004)
    # Downward finishing tangent: no forced reconnection to old grouped tips.
    c2 = end+np.array([-.10*chord[0],.009 if free_flow else .002,.026])
    u = t[:,None]
    guide = (1-u)**3*root+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end
    values = old*(1-blend[:,None])+guide*blend[:,None]
    correction = np.zeros_like(values)
    for j in range(prefix,65):
        hit, nn, _, distance = bv.find_nearest(Vector(values[j]))
        gap = (Vector(values[j])-hit).dot(nn)
        if distance < .025 and gap < .001:
            correction[j] = np.array(nn)*(.0015-gap)
            repairs += 1
    # Smooth correction field, no isolated surface kinks.
    for axis in range(3):
        correction[:,axis] = np.convolve(np.pad(correction[:,axis],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
    values += correction
    values[:prefix] = old[:prefix]
    q[i] = values
assert np.isfinite(q).all() and np.array_equal(q[:,:prefix],raw[:,:prefix]) and np.array_equal(q[~mask],raw[~mask])
ob.data = cu.copy()
ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr = 'native_soft_part_redesign'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
ob.data.update_tag()
out.mkdir(parents=True)
rd.mkdir(parents=True)
s = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'
pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = 96
s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1200,1400
s.render.resolution_percentage = 80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'soft_part_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,pilot=pilot,free_root_flow=free_flow,feather_tips=feather,trimmed_feather=trimmed,front_upper=front_upper,original_fringe_count=fringe_count,additional_upper_count=upper_count,selection_attribute=attr,changed_fibers=len(ids),preserved_prefix_points=prefix,endpoints_released=True,endpoint_repairs=endpoint_repairs,intermediate_discrete_repairs=repairs,method='Current fringe'+(' plus actual upper attribute withrootY<-15mm/endY<-80mm.' if front_upper else '.')+' Own strand cubic, endpointX*'+(('0.75,seeded independent X+-0.6mm/Y+-0.5mm/Z(+2,+14)mm tip stagger;innerX<65mm tipZ>=1.755m before body guard' if trimmed else '0.68,seeded independent X+-1.8mm/Y+-1mm/Z(-5,+8)mm tip stagger') if feather else '0.78')+'/forward10mm/root-field Z stagger5mm; scalp tangent24-45mm/downward26mm terminal control; '+('root alone preserved,9mm normal relief and9mm terminal Y offset.' if free_flow else '6points preserved,4mm normal relief/2mm terminal Y offset,smooth join afterpoint5.')+' Original radii/topology retained. Sampled body guard, not continuous collision proof.',status='Actual geometry study awaiting art review'),indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
    s.camera = bpy.data.objects[shot]
    s.render.filepath = str(rd/(shot+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('SOFT_PART_RENDERED',version,len(ids),flush=True)
