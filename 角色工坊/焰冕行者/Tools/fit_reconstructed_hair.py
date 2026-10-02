"""Fit raw reconstructed wig to real head, render four neutral review views.

Shape-only pass; not a finished realistic hair material or groom.
Blender arguments: -- new-version raw-version [--draft]
"""
import bpy
import json
import sys
import re
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
version, raw = args[:2]
draft = '--draft' in args
for value in [version, raw]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value): raise ValueError(value)
out = ROOT / 'Exports' / version
render = ROOT / 'Renders' / version
if out.exists() or render.exists(): raise RuntimeError('Fresh folders required')
out.mkdir(parents=True); render.mkdir(parents=True)
source = ROOT / 'Source/HairReconstruction' / raw / 'raw_hair.obj'
verts, faces = [], []
for line in source.read_text().splitlines():
    q = line.split()
    if q and q[0] == 'v': verts.append(tuple(map(float, q[1:4])))
    elif q and q[0] == 'f': faces.append([int(v.split('/')[0]) - 1 for v in q[1:]])
v = np.asarray(verts)
lo, hi = v.min(0), v.max(0)
print('RAW_BOUNDS', lo.tolist(), hi.tolist(), flush=True)
# Hunyuan OBJ uses Y-up, Z-front; target is Blender Z-up, -Y-front.
# Initial scalp fit is adjustable in the saved source, and must be reviewed.
p = np.empty_like(v)
p[:, 0] = (v[:, 0] - (hi[0] + lo[0]) / 2) * .245 / (hi[0] - lo[0])
p[:, 2] = 1.630 + (v[:, 1] - lo[1]) * .286 / (hi[1] - lo[1])
p[:, 1] = -.044 - (v[:, 2] - (hi[2] + lo[2]) / 2) * .252 / (hi[2] - lo[2])
if '--fit-back' in args:
    # Preserve the front while moving the reconstructed hollow wig's rear
    # shell clear of the actual cranium. Shift the part into asymmetry.
    clean = np.load(source.with_name('connected_hair.npz'))
    v = clean['vertices']; faces = clean['faces'].tolist()
    p = np.empty_like(v)
    p[:, 0] = (v[:, 0] - (hi[0] + lo[0]) / 2) * .245 / (hi[0] - lo[0])
    p[:, 2] = 1.630 + (v[:, 1] - lo[1]) * .286 / (hi[1] - lo[1])
    p[:, 1] = -.044 - (v[:, 2] - (hi[2] + lo[2]) / 2) * .252 / (hi[2] - lo[2])
    p[:, 1] += .043 * np.clip((p[:, 1] + .035) / .07, 0, 1)
    p[:, 0] += .020 * np.exp(-(p[:, 0] / .082)**2) * np.clip((p[:, 2] - 1.78) / .08, 0, 1)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'Exports/atelier09/Ember_Regent.blend'))
col = bpy.data.collections['05_Hair']
for ob in list(col.objects): bpy.data.objects.remove(ob, do_unlink=True)
me = bpy.data.meshes.new('Raw reconstructed wig triangles')
me.from_pydata(p.tolist(), [], faces); me.update()
ob = bpy.data.objects.new('Hunyuan reconstructed cherry wig - shape review', me)
col.objects.link(ob)
for poly in me.polygons: poly.use_smooth = True
mat = bpy.data.materials.new('Matte red shape review - not finished hair')
mat.use_nodes = True
bs = mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value = (.12, .012, .021, 1)
bs.inputs['Roughness'].default_value = .6
bs.inputs['Specular IOR Level'].default_value = .2
me.materials.append(mat)
stage = bpy.data.collections['90_Stage']
for o in list(stage.objects):
    if o.type in ['LIGHT', 'CAMERA']: bpy.data.objects.remove(o, do_unlink=True)
def area(name, loc, power, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.size = size
    o = bpy.data.objects.new(name, d); stage.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, -.025, 1.74)) - o.location).to_track_quat('-Z', 'Y').to_euler()
area('Neutral key', (-1.5, -2, 2.7), 115, 1.5)
area('Neutral fill', (1.5, -1.5, 1.9), 48, 1.5)
area('Neutral rim', (1, 1.7, 2.5), 90, 1.2)
scene = bpy.context.scene
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.055, .055, .055, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .3
scene.render.engine = 'CYCLES'; scene.cycles.samples = 48 if draft else 128
scene.cycles.use_denoising = True
pref = bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type = 'OPTIX'; pref.get_devices()
for d in pref.devices: d.use = d.type == 'OPTIX'
scene.cycles.device = 'GPU'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = -.25
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
scene.render.resolution_x = 1200; scene.render.resolution_y = 1400
scene.render.resolution_percentage = 70 if draft else 100
for name, loc in [('01_Front', (0, -4, 1.76)), ('02_ThreeQuarter', (.95, -3, 1.79)),
                  ('03_Side', (4, -.025, 1.76)), ('04_Back', (0, 4, 1.76))]:
    d = bpy.data.cameras.new(name); cam = bpy.data.objects.new(name, d); stage.objects.link(cam)
    cam.location = loc; cam.rotation_euler = (Vector((0, -.025, 1.745)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    d.type = 'ORTHO'; d.ortho_scale = .55; scene.camera = cam
    scene.render.filepath = str(render / (name + '.png')); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Ember_Regent.blend'))
report = {'version': version, 'raw_version': raw, 'vertices': len(p), 'faces': len(faces),
          'fit_bounds': [p.min(0).tolist(), p.max(0).tolist()], 'status': 'shape-only candidate requires review',
          'material': 'matte shape inspection only', 'hair_strands': False,
          'posterior_fit': '--fit-back' in args,
          'cleanup': 'largest connected component' if '--fit-back' in args else 'none'}
(out / 'groom_manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print('RECONSTRUCTED_SHAPE_REVIEW_SAVED', version, flush=True)
