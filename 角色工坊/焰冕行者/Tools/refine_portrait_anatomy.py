"""Fresh, modest anatomical sculpture study on the retained CC0 face.

Keeps UVs and topology; edits actual mesh and follows brows/lashes. Does not
replace the face with a generated portrait or claim animation readiness.
"""
import bpy, sys, re, math, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)

def gauss(x,center,width):return math.exp(-((x-center)/width)**2)
def sculpt(p,accessory=False):
    x,y,z=p
    if z<1.61 or y>-.08:return p.copy()
    front=max(0.,min(1.,(-y-.08)/.050))
    eye=gauss(abs(x),.034,.018)
    dz=(-.0015*gauss(z,1.757,.007)+.0005*gauss(z,1.741,.005))*eye*front
    dz+=.0007*gauss(abs(x),.052,.010)*gauss(z,1.750,.012)*front
    # Subtle brow lowering adds focus without an exaggerated frown.
    dz-=.0009*gauss(abs(x),.028,.022)*gauss(z,1.779,.006)*front
    if accessory:return Vector((x,y,z+dz))
    slim=.038*gauss(z,1.693,.029)*front
    nose=.045*gauss(z,1.730,.025)*gauss(x,0,.019)*front
    nx=x*(1-slim-nose)
    ny=y+.0011*gauss(abs(x),.054,.018)*gauss(z,1.697,.017)*front
    ny-=.0013*gauss(abs(x),.049,.020)*gauss(z,1.720,.014)*front
    ny-=.0008*gauss(x,0,.024)*gauss(z,1.639,.013)*front
    return Vector((nx,ny,z+dz))

body=bpy.data.objects['CC0 male body • retained topology']
changed=0
for v in body.data.vertices:
    before=v.co.copy();v.co=sculpt(before)
    changed+=(v.co-before).length>1e-7
body.data.update()
for ob in bpy.data.collections['01_Body'].objects:
    if ob.hide_render or ob==body or 'high-poly' in ob.name:continue
    if ob.type=='MESH' and 'eyebrow' in ob.name:
        for v in ob.data.vertices:v.co=sculpt(v.co,True)
        ob.data.update()
    if ob.type=='CURVE' and 'eyelash' in ob.name.lower():
        for sp in ob.data.splines:
            for pt in sp.points:pt.co=(*sculpt(Vector(pt.co[:3]),True),pt.co.w)

scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192
scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.resolution_percentage=80 if '--draft' in args else 100
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            changed_body_vertices=changed,method='Actual local anatomical face sculpture; retained UV/topology, unchanged eyeball geometry, brow/lash following',
            status='unreviewed anatomical study; no artistic or motion acceptance',
            license='Retained CC0 body and original sculpture; hair components retain their own licenses',
            collision_scope='No exhaustive eyelid/eyeball or motion intersection test')
(out/'anatomy_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('ANATOMY_STUDY_RENDERED',version,changed,flush=True)
