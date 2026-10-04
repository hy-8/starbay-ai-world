"""Retain whole rear-flow locks and taper their real native fibers.

Fresh static study. Local Ddr Rcs geometry derivatives stay local; preserve
BlenderKit Royalty Free and Bystedt CC BY-SA component credits.
"""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--')+1:]
version, side_version, front_version = args[:3]
DRAFT = '--draft' in args
SCISSOR = '--scissor-layers' in args
LEAN = '--lean-wolf' in args
STAGGER = '--stagger-locks' in args
FEATHER = '--feather-tips' in args
TIP_CLUMP=float(args[args.index('--tip-clump')+1]) if '--tip-clump' in args else .65
if not .50<=TIP_CLUMP<=.97:raise ValueError('Tip clump must be .50..97')
SOFT_TIPS='--soft-tip-spread' in args
DRY='--dry-groom' in args
NAPE_WAVE='--nape-s-waves' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in args[:3]):
    raise ValueError('Invalid versions')
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists():
    raise RuntimeError('Fresh versions required')
out.mkdir(parents=True); render.mkdir(parents=True)
source = ROOT/'Exports'/side_version/'Ember_Regent.blend'
frontal = ROOT/'Exports'/front_version/'Ember_Regent.blend'
records = json.loads((source.parent/'licensed_groom_design.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
original = bpy.data.objects['Licensed Ddr Rcs derivative • actual native curves']
cu = original.data
sizes = [len(c.points) for c in cu.curves]
if len(set(sizes)) != 1: raise RuntimeError('Expected uniform source fibers')
N = sizes[0]
raw = np.empty(len(cu.points)*3, np.float32)
cu.attributes['position'].data.foreach_get('vector', raw)
raw = raw.reshape(-1, N, 3)
rad = np.empty(len(cu.points), np.float32)
cu.attributes['radius'].data.foreach_get('value', rad)
rad = rad.reshape(-1, N)
if sum(r['fibers'] for r in records) != len(raw):
    raise RuntimeError('Guide provenance does not cover fibers exactly')
body = bpy.data.objects['CC0 male body • retained topology']
bpy.context.view_layer.update()
bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
t = np.linspace(0, 1, N)
rng = np.random.default_rng(100515)
tip_rng = np.random.default_rng(100604)
strands, radii = [], []
offset = 0; removed = 0; retained = 0; clearance_repairs = 0
for record in records:
    count = record['fibers']
    group = raw[offset:offset+count].astype(float)
    group_rad = rad[offset:offset+count].copy()
    offset += count
    if not count: continue
    center = np.median(group, axis=0)
    root, end = center[0], center[-1]
    # Front bangs replaced as whole locks. Crown roots feeding rear locks
    # survive: a root-height cut removed the entire back scalp in study 01.
    front = record['kind'] == 'asymmetric extended wavy bang'
    front |= end[1] < -.132 and end[2] > 1.725
    if LEAN:
        front |= end[1] < -.098 and root[1] < -.034 and end[2] > 1.700
    if front:
        removed += count
        continue
    if SCISSOR and root[1] < -.070 and root[2] < 1.821:
        # Remove the source haircut's abrupt short temple card fans. These
        # have hard upper edges even after conversion; authored temple locks
        # cover this region instead of retaining those triangular stumps.
        removed += count
        continue
    retained += 1
    shaped = center.copy()
    long_lock = end[2] < 1.758
    if long_lock:
        posterior = end[1] > -.008
        side = 1 if root[0] > 0 else -1
        target = end.copy()
        if posterior:
            if SCISSOR:
                # Upper layers stop above the nape; lower roots retain the
                # length. This opens discrete overlapping silhouettes rather
                # than a continuous full-length back curtain.
                h = np.clip((root[2]-1.735)/.130, 0, 1)
                target[2] = (1.599+.096*h if LEAN else 1.603+.136*h)+rng.uniform(-.021, .022)
                if STAGGER:
                    target[2] = rng.uniform(1.625, 1.754) if rng.random() < .58 else rng.uniform(1.603, 1.677)
            else:
                target[2] = rng.uniform(1.595, 1.690)
            target[0] *= rng.uniform(.78, .99)
            target[1] += rng.uniform(.007, .019)
        else:
            target[2] = rng.uniform(1.670, 1.757)
            target[0] += side*rng.uniform(.002, .009)
        start = rng.uniform(.05, .44) if STAGGER else .32
        env = np.maximum(0, (t-start)/(1-start))**1.65
        shaped += (target-end)[None, :]*env[:, None]
        phase = rng.uniform(0, 2*np.pi) if STAGGER else rng.uniform(-.65, .65)
        amp = rng.uniform(.004, .010) if LEAN else (rng.uniform(.006, .015) if SCISSOR else rng.uniform(.005, .013))
        shaped[:, 0] += side*amp*np.sin(t*rng.uniform(1.7, 2.8)*np.pi+phase)*np.sin(np.pi*t)
        shaped[:, 1] += rng.uniform(.002, .007)*np.sin(t*2.1*np.pi+phase)*np.sin(np.pi*t)
        if SCISSOR and posterior:
            shaped[:, 1] += (rng.uniform(.003, .007) if LEAN else rng.uniform(.008, .015))*np.sin(t*2.6*np.pi+phase)*np.sin(np.pi*t)
            shaped[:, 1] -= (rng.uniform(.004, .008) if LEAN else 0)*np.sin(np.pi*t)
            shaped[:, 2] += rng.uniform(.003, .006)*np.sin(t*2.2*np.pi)*np.sin(np.pi*t)
        if NAPE_WAVE and posterior:
            # A coherent lower-neck S bend, fading continuously at both ends.
            # Spatial height weighting keeps the upper scalp coverage intact.
            q=np.clip((1.755-shaped[:,2])/.150,0,1)
            phase=(retained%5-2)*.18
            wave=np.sin(q*1.65*np.pi+phase)*np.sin(np.pi*q)
            shaped[:,1]+=.012*wave
            shaped[:,0]+=side*.005*wave
    tangent = np.gradient(shaped, axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-8)
    radial = shaped-np.array([0, -.044, 1.771])
    normal = radial-tangent*np.sum(radial*tangent, axis=1)[:, None]
    normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-8)
    # Preserve root coverage, narrow each distinct lock toward its tip.
    taper = 1-(TIP_CLUMP if FEATHER else .95)*np.maximum(0, (t-.18)/.82)**1.25
    for s, r in zip(group, group_rad):
        s = shaped+(s-center)*taper[:, None]
        s += normal*(rng.normal(0, .0010)*np.sin(np.pi*t))[:, None]
        if long_lock and rng.random() < .7:
            cut = rng.uniform(.84, 1.)
            s = np.stack([np.interp(t*cut, t, s[:, j]) for j in range(3)], axis=1)
        if FEATHER and long_lock:
            # A separate RNG preserves earlier authored lock placement.
            tip_delta=tip_rng.normal(0,np.array([.0024,.0020,.0012])*(.5 if SOFT_TIPS else 1),3)
            s+=tip_delta[None,:]*t[:,None]**3
            bend=np.clip((t-.52)/.48,0,1)
            s+=normal*(.0035*np.sin(1.35*np.pi*bend)*bend)[:,None]
        for j, p in enumerate(s):
            hit, n, face, dist = bv.find_nearest(Vector(p))
            gap = (Vector(p)-hit).dot(n)
            if j == 0 or (gap < .0007 and dist < .04):
                s[j] = np.array(hit+n*(.0005 if j == 0 else .0009))
                clearance_repairs += j != 0
            elif LEAN and p[1] > .005 and p[2] > 1.72 and gap > .007 and dist < .065:
                # Reduce rear bulb volume while retaining the actual guide
                # topology and a positive separation. Blend spatially: a
                # hard z-plane created a false horizontal haircut ledge.
                w = np.clip((p[2]-1.72)/.075, 0, 1)
                w *= np.clip((p[1]-.005)/.045, 0, 1)
                w = w*w*(3-2*w)
                s[j] = np.array(hit)+(p-np.array(hit))*(gap-.50*w*(gap-.007))/gap
        strands.append(s.astype(np.float32)); radii.append(r)
original.hide_render = True; original.hide_viewport = True
col = bpy.data.collections.new('05_Whole_Lock_Regional_Groom')
bpy.context.scene.collection.children.link(col)
new = bpy.data.hair_curves.new('Ddr Rcs whole rear locks • tapered layered derivative')
new.add_curves([N]*len(strands))
new.attributes['position'].data.foreach_set('vector', np.asarray(strands).ravel())
new.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.asarray(radii).ravel())
new.materials.append(cu.materials[0])
ob = bpy.data.objects.new('Ddr Rcs derivative • whole rear locks', new); col.objects.link(ob)
names = ['Authored spatial fringe • actual scalp root patches', 'Bystedt derivative • short scalp support']
with bpy.data.libraries.load(str(frontal), link=False) as (available, loaded):
    if not all(n in available.objects for n in names): raise RuntimeError('Frontal geometry missing')
    loaded.objects = names
for ob in loaded.objects:
    col.objects.link(ob); ob.hide_render=False; ob.hide_viewport=False
if DRY:
    # Match the visible regional components' roughness without recoloring.
    for groom in bpy.data.objects:
        if groom.type!='CURVES' or groom.hide_render:continue
        for slot,mat in enumerate(groom.data.materials):
            if not mat or not mat.node_tree:continue
            mat=mat.copy();groom.data.materials[slot]=mat
            for node in mat.node_tree.nodes:
                if node.type=='BSDF_HAIR_PRINCIPLED':
                    node.inputs['Roughness'].default_value=.42
                    node.inputs['Radial Roughness'].default_value=.48
credits = bpy.data.texts.new('WHOLE_LOCK_GROOM_CREDITS')
credits.write('Ddr Rcs Female Shaggy Mullet Haircut: BlenderKit Royalty Free. Side/rear native fibers shortened, layered, waved and tapered; source/derived geometry kept local, not an asset pack. Front locally authored; short scalp support retains Daniel Bystedt CC BY-SA, version unspecified in evidence. All historical hidden objects retained. Static unapproved study.\n')
scene = bpy.context.scene
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'; pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
scene.cycles.device='GPU'; scene.cycles.samples=64 if DRAFT else 192
scene.cycles.use_denoising=False; scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200; scene.render.resolution_y=1400
scene.render.resolution_percentage=80 if DRAFT else 100
report = dict(version=version, source=side_version, frontal_source=front_version,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    frontal_sha256=hashlib.sha256(frontal.read_bytes()).hexdigest(),
    method='Whole-lock endpoint/flow selection, native fiber taper, layered nape and mild spatial waves',
    retained_locks=retained, native_side_rear_fibers=len(strands), discarded_front_fibers=removed,
    body_clearance_repairs=clearance_repairs, draft=DRAFT, scissor_layers=SCISSOR, lean_wolf=LEAN, stagger_locks=STAGGER,
    processing_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    license='Ddr Rcs Royalty Free derivative + Bystedt CC BY-SA short frontal support; not CC0',
    status='unreviewed actual geometry', collision_scope='Nearest body checks; clothing and animation not verified')
report['relaxed_clump_tip_spread']=FEATHER
report.update(tip_clump_strength=TIP_CLUMP if FEATHER else .95,soft_tip_spread=SOFT_TIPS)
report.update(dry_groom_roughness=DRY,visible_hair_roughness=.42 if DRY else 'retained component settings',visible_radial_roughness=.48 if DRY else 'retained component settings')
report['continuous_lower_nape_s_bends']=NAPE_WAVE
(out/'groom_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front', '02_ThreeQuarter', '03_Side', '04_Back']:
    scene.camera=bpy.data.objects[name]; scene.render.filepath=str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('WHOLE_LOCK_GROOM_RENDERED', version, len(strands), flush=True)
