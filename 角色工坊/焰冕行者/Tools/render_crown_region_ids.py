"""Read-only actual region IDs for the saved continuation groom."""
import bpy, sys, re, json, hashlib, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]; version, base = a
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a)
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
for item in bpy.data.objects:
    if item.type == 'CURVES': item.hide_render = True
    elif item.type == 'MESH' and not item.hide_render:
        for slot in item.material_slots: slot.material = neutral
legend = []
regions = [('foreground61', front, (1, .03, .06, 1)), ('side86', side, (.03, .3, 1, 1)),
           ('remaining_upper_crown', crown, (.03, 1, .06, 1)),
           ('other_primary', ~(front | side | crown), (1, .55, .03, 1))]
for name, mask, color in regions:
    data = bpy.data.hair_curves.new(name); data.add_curves([65] * int(mask.sum()))
    data.attributes['position'].data.foreach_set('vector', p[mask].ravel())
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', r[mask].ravel())
    data.materials.append(material(color, name + ' ID'))
    item = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(item); item.matrix_world = ob.matrix_world
    legend.append(dict(region=name, fibers=int(mask.sum()), color=list(color), root_mean_m=p[mask, 0].mean(axis=0).tolist()))
s = bpy.context.scene; pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'; pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'; s.cycles.samples = 32; s.cycles.use_denoising = False
s.view_settings.view_transform = 'Standard'; s.render.resolution_x, s.render.resolution_y = 1200, 1400; s.render.resolution_percentage = 80
out.mkdir(parents=True); images = {}
for name in ['02_ThreeQuarter', '01_Front']:
    s.camera = bpy.data.objects[name]; path = out / (name + '.png'); s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); images[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
(out / 'region_id_manifest.json').write_text(json.dumps(dict(source=base, source_sha256=digest, source_unchanged=True,
    legend=legend, images_sha256=images, scope='Actual saved primary region emission IDs; support hidden temporarily. No source save or final-appearance acceptance.'), indent=2), encoding='utf-8')
print('CROWN_REGION_IDS', version, flush=True)
