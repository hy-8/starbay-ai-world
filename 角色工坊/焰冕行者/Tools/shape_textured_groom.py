"""Local textured-card versus native-fiber comparison from real geometry.

Ddr Rcs Royalty Free side/rear derivatives stay local. Bystedt CC BY-SA
short frontal support keeps separate credits. Fresh static candidates only.
"""
import bpy, bmesh, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--')+1:]
version, source_version, frontal_version = args[:3]
DRAFT = '--draft' in args
if not all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in args[:3]): raise ValueError(args)
out, render = ROOT/'Exports'/version, ROOT/'Renders'/version
if out.exists() or render.exists(): raise RuntimeError('Fresh output required')
out.mkdir(parents=True); render.mkdir(parents=True)
source = ROOT/'Exports'/source_version/'Ember_Regent.blend'
frontal = ROOT/'Exports'/frontal_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
hair = bpy.data.objects['Ddr Rcs hair-card derivative • actual fitted geometry']
me = hair.data
xyz = np.array([v.co[:] for v in me.vertices], float)
factor = np.array([v.color_srgb[0] for v in me.attributes['Factor'].data])
parent = np.arange(len(xyz))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
for edge in me.edges:
    a,b = (find(int(i)) for i in edge.vertices)
    if a != b: parent[b] = a
groups = {}
for i in range(len(xyz)): groups.setdefault(find(i), []).append(i)
body = bpy.data.objects['CC0 male body • retained topology']
bpy.context.view_layer.update(); bv = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
rng = np.random.default_rng(100606)
remove = []; changed = xyz.copy(); retained = 0; repairs = 0
for ids0 in groups.values():
    ids = np.asarray(ids0); values = np.round(factor[ids], 6); unique = np.unique(values)
    rows = [xyz[ids[values==u]].mean(axis=0) for u in unique]
    rows = np.asarray(rows)
    root, end = rows[0], rows[-1]
    front = end[1] < -.100 and end[2] > 1.700
    front |= root[1] < -.072 and root[2] < 1.822
    if front or len(rows) < 4:
        remove.extend(ids0); continue
    retained += 1
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(rows, axis=0), axis=1))]
    keep = np.r_[True, np.diff(arc) > 1e-7]; arc = arc[keep]; rows = rows[keep]; u = unique[keep]
    if len(arc) < 4 or arc[-1] < .006: continue
    long = end[2] < 1.73
    rear = end[1] > -.020
    desired = rng.uniform(1.606, 1.717) if rear else rng.uniform(1.685, 1.759)
    limit = float(np.clip((root[2]-desired)/max(root[2]-end[2], .001), .43, .96)) if long else 1.
    q = np.interp(factor[ids], u, arc)
    base = np.stack([np.interp(q, arc, rows[:,j]) for j in range(3)], axis=1)
    cropped = np.stack([np.interp(q*limit, arc, rows[:,j]) for j in range(3)], axis=1)
    t = q/max(arc[-1], 1e-8)
    phase = rng.uniform(0, 2*np.pi)
    # Low-frequency lock waves, independently phased; keep original UVs
    # traversing the full painted alpha tip despite shortened spatial length.
    if long:
        cropped[:,0] += rng.uniform(.004, .013)*np.sin(t*rng.uniform(1.5, 2.6)*np.pi+phase)*np.sin(np.pi*t)
        cropped[:,1] += rng.uniform(.005, .011)*np.sin(t*2*np.pi+phase)*np.sin(np.pi*t)
        if rear: cropped[:,1] += .008*t**3
    delta = xyz[ids]-base
    taper = 1-.55*t**1.55
    shaped = cropped+delta*taper[:,None]
    for j,p in enumerate(shaped):
        hit,n,face,dist = bv.find_nearest(Vector(p)); gap = (Vector(p)-hit).dot(n)
        if gap < .0008 and dist < .035:
            shaped[j] = np.array(hit+n*.001); repairs += 1
    changed[ids] = shaped
me.vertices.foreach_set('co', changed.astype(np.float32).ravel()); me.update()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in remove], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
for poly in me.polygons: poly.use_smooth=True
for mat in me.materials:
    for node in mat.node_tree.nodes:
        if node.type != 'GROUP' or not node.node_tree.name.startswith('HairShaderMain'): continue
        for key,value in [('Base Color',(.18,.014,.021,1)), ('Root Color',(.038,.002,.003,1)), ('Tip Color',(.22,.022,.026,1)), ('Root Color Mix Factor',.25), ('SpecRoughness',.35)]:
            socket=node.inputs.get(key)
            if socket and not socket.is_linked: socket.default_value=value
collection=bpy.data.collections.new('05_Textured_Regional_Comparison'); bpy.context.scene.collection.children.link(collection)
names=['Authored spatial fringe • actual scalp root patches','Bystedt derivative • short scalp support']
with bpy.data.libraries.load(str(frontal),link=False) as (available,loaded):
    if not all(n in available.objects for n in names): raise RuntimeError('Frontal components missing')
    loaded.objects=names
for ob in loaded.objects:
    collection.objects.link(ob); ob.hide_render=False; ob.hide_viewport=False
credits=bpy.data.texts.new('TEXTURED_REGIONAL_CREDITS')
credits.write('Rear textured cards derived from Female Shaggy Mullet Haircut by Ddr Rcs, BlenderKit Royalty Free. Retained UV alpha, shortened and waved actual geometry, adapted red shader. Original and derivative geometry kept local. Front authored actual scalp patches; short support adapted from Daniel Bystedt Hair Styles, CC BY-SA, inspected version unspecified. Static unapproved comparison.\n')
scene=bpy.context.scene; pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX'; pref.get_devices()
for d in pref.devices: d.use=d.type=='OPTIX'
scene.cycles.device='GPU'; scene.cycles.samples=64 if DRAFT else 192
scene.cycles.use_denoising=False; scene.cycles.transparent_max_bounces=24; scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200; scene.render.resolution_y=1400; scene.render.resolution_percentage=80 if DRAFT else 100
report=dict(version=version,source=source_version,frontal_source=frontal_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256(frontal.read_bytes()).hexdigest(),processing_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),retained_cards=retained,deleted_vertices=len(remove),body_clearance_repairs=repairs,visible_hair='Actual textured side/rear mesh cards plus native frontal fibers',texture_policy='Original packed alpha and UV preserved; geometry derivatives local',license='Ddr Rcs Royalty Free cards; Bystedt CC BY-SA short scalp support',draft=DRAFT,status='unreviewed actual comparison',collision_scope='nearest body only; clothing and animation not verified')
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('TEXTURED_REGIONAL_RENDERED',version,retained,flush=True)
