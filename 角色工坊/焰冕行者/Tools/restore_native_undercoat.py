"""Restore inspected short real-scalp support beneath the native waves.

Preserves source meshes and full primary hairstyle; no scalp-colored solid cap.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version
if out.exists():raise RuntimeError('Fresh candidate only')
source=ROOT/'Exports/nativelobe04/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
main=bpy.data.objects['Bystedt layercut derivative • native root reflow'];mat=main.data.materials[0]
names=['Abhay flow derivative • real scalp sampled short support','Bystedt derivative • short scalp support','Original posterior coverage • surface-grown short fibers']
rows=[]
for name in names:
 ob=bpy.data.objects.get(name)
 if ob is None or ob.type!='CURVES':raise RuntimeError('Missing inspected real scalp component '+name)
 ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat)
 ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
 rows.append(dict(object=name,curves=len(ob.data.curves),geometry_unchanged=True,material_unified_with_primary=True))
out.mkdir(parents=True)
(out/'undercoat_manifest.json').write_text(json.dumps(dict(source='nativelobe04',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 primary_geometry_unchanged=True,restored_short_components=rows,method='Restore retained native short actual-scalp supports under the complete native waves; copy materials only',
 license='Bystedt CC BY-SA (version unspecified), Abhay BlenderKit Royalty Free (not CC0); original anatomical posterior short fibers',
 status='Unreviewed real 3D coverage candidate',scope='Visibility/material operation; no complete clothing/segments/animation collision proof'),indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
print('NATIVE_UNDERCOAT_RESTORED',version,flush=True)
