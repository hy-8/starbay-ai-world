"""Read-only actual region IDs for the saved continuation groom."""
import bpy, sys, re, json, hashlib, numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]; version, base = a[:2]
loft_states = '--loft-states' in a; support_ids = '--support-ids' in a
fan_states = '--fan-states' in a
posterior_states = '--posterior-states' in a
free_states = '--free-states' in a
fine_states = '--fine-states' in a
assert sum([fan_states, loft_states, posterior_states, free_states, fine_states]) <= 1, 'Choose one region scheme'
shots = a[a.index('--cameras')+1].split(',') if '--cameras' in a else ['02_ThreeQuarter', '01_Front']
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
assert shots and all(v in ['01_Front','02_ThreeQuarter','03_Side','04_Back','05_OppositeSide'] for v in shots)
out = ROOT / 'Renders' / version; assert not out.exists()
source = ROOT / 'Exports' / base / 'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']; cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel()); p = p.reshape(-1, 65, 3)
r = np.empty(len(cu.points), np.float32)
cu.attributes['radius'].data.foreach_get('value', r); r = r.reshape(-1, 65)
def flag(name):
    values = np.empty(len(p), bool); cu.attributes[name].data.foreach_get('value', values); return values
front = flag('native_front_frame_sculpture'); side = flag('native_relaxed_side_locks')
crown = (~front) & (~side) & (p[:, 0, 2] > 1.830) & (p[:, 0, 1] < .065)
def material(color, name):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    n = nt.nodes.new('ShaderNodeEmission'); n.inputs['Color'].default_value = color
    output = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(n.outputs[0], output.inputs['Surface']); return mat
neutral = material((.065, .065, .065, 1), 'Neutral body')
supports=[item for item in bpy.data.objects if item.type=='CURVES' and item!=ob and not item.hide_render]
for item in bpy.data.objects:
    if item.type == 'CURVES': item.hide_render = True
    elif item.type == 'MESH' and not item.hide_render:
        for slot in item.material_slots: slot.material = neutral
legend = []
regions = [('foreground61', front, (1, .03, .06, 1)), ('side86', side, (.03, .3, 1, 1)),
           ('remaining_upper_crown', crown, (.03, 1, .06, 1)),
           ('other_primary', ~(front | side | crown), (1, .55, .03, 1))]
if loft_states:
    loft=flag('native_layered_root_lofts');relief=flag('native_visible_crest_relief')
    assert not (front&loft).any() and not (relief&~loft).any()
    regions=[('foreground61',front,(1,.03,.06,1)),('retained_root_lofts90',loft&~relief,(.03,.3,1,1)),
             ('restored_root_locks86',relief,(.03,1,.06,1)),('other_primary',~(front|loft),(1,.55,.03,1))]
if fan_states:
    fringe=flag('native_resculpted_fringe_sweeps')
    fan=flag('native_transported_fan_crown')
    assert not (fringe&fan).any()
    regions=[('actual_resculpted_fringe106',fringe,(1,.03,.06,1)),
             ('actual_fan_crown113',fan,(.03,.3,1,1)),
             ('other_primary',~(fringe|fan),(.03,1,.06,1))]
if posterior_states:
    fringe=flag('native_resculpted_fringe_sweeps')
    posterior=flag('native_staggered_posterior_layers')
    assert not (fringe&posterior).any()
    regions=[('actual_fringe_region',fringe,(1,.03,.06,1)),
             ('actual_posterior118_region',posterior,(.03,.3,1,1)),
             ('other_primary',~(fringe|posterior),(.03,1,.06,1))]
if free_states:
    fringe=flag('native_resculpted_fringe_sweeps')
    free=flag('native_unranked_free_sections')
    assert not (fringe&free).any()
    regions=[('actual_fringe_region',fringe,(1,.03,.06,1)),
             ('actual_unranked123_region',free,(.03,.3,1,1)),
             ('other_primary',~(fringe|free),(.03,1,.06,1))]
if fine_states:
    fringe=flag('native_resculpted_fringe_sweeps')
    fine=flag('native_descending_fine_locks')
    assert not (fringe&fine).any()
    regions=[('actual_fringe_region',fringe,(1,.03,.06,1)),
             ('actual_descending133_region',fine,(.03,.3,1,1)),
             ('other_primary',~(fringe|fine),(.03,1,.06,1))]
for name, mask, color in regions:
    data = bpy.data.hair_curves.new(name); data.add_curves([65] * int(mask.sum()))
    data.attributes['position'].data.foreach_set('vector', p[mask].ravel())
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', r[mask].ravel())
    data.materials.append(material(color, name + ' ID'))
    item = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(item); item.matrix_world = ob.matrix_world
    legend.append(dict(region=name, fibers=int(mask.sum()), color=list(color), root_mean_m=p[mask, 0].mean(axis=0).tolist()))
if support_ids:
    for item,color in zip(supports,[(0,1,1,1),(.7,.05,1,1),(1,.03,.65,1)]):
        item.hide_render=False;item.data.materials.clear();item.data.materials.append(material(color,item.name+' ID'))
        legend.append(dict(region=item.name,fibers=len(item.data.curves),color=list(color),role='support native curves'))
s = bpy.context.scene; pref = bpy.context.preferences.addons['cycles'].preferences
if '05_OppositeSide' in shots:
    cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
    ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
pref.compute_device_type = 'OPTIX'; pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'; s.cycles.samples = 32; s.cycles.use_denoising = False
s.view_settings.view_transform = 'Standard'; s.render.resolution_x, s.render.resolution_y = 1200, 1400; s.render.resolution_percentage = 80
out.mkdir(parents=True); images = {}
for name in shots:
    s.camera = bpy.data.objects[name]; path = out / (name + '.png'); s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); images[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
(out / 'region_id_manifest.json').write_text(json.dumps(dict(source=base, source_sha256=digest, source_unchanged=True,
    legend=legend, images_sha256=images, loft_states=loft_states,fan_states=fan_states,posterior_states=posterior_states,free_states=free_states,fine_states=fine_states,support_ids=support_ids,
    scope='Actual saved region emission IDs; '+('all3 original native support objects included with separate IDs' if support_ids else 'support hidden temporarily')+'. No source save or final-appearance acceptance.'), indent=2), encoding='utf-8')
print('CROWN_REGION_IDS', version, flush=True)
