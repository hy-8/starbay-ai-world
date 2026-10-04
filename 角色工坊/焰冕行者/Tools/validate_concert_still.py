"""Read-only structural checks for a saved native-curve character still scene.

This reports file integrity only, never artistic approval or game readiness.
"""
import bpy,sys,json,hashlib,re
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
folder=ROOT/'Exports'/VERSION;path=folder/'Redline_Editorial.blend'
if not path.exists():path=folder/'Ember_Regent.blend'
report_path=folder/'structural_validation.json'
if report_path.exists():raise RuntimeError('Existing validation is preserved')
bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
errors=[];meshes=0;verts=0;grooms=[];shape_keys=[]
for o in bpy.data.objects:
    if o.hide_render:continue
    if o.type=='MESH':
        a=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',a)
        if not np.isfinite(a).all():errors.append('Nonfinite mesh: '+o.name)
        if o.data.shape_keys:
            for key in o.data.shape_keys.key_blocks:
                ka=np.empty(len(key.data)*3,np.float32);key.data.foreach_get('co',ka)
                valid=bool(np.isfinite(ka).all() and np.isfinite(key.value))
                if not valid:errors.append('Nonfinite shape key: '+o.name+'/'+key.name)
                shape_keys.append({'object':o.name,'key':key.name,'value':float(key.value),'points':len(key.data),'finite':valid})
        meshes+=1;verts+=len(o.data.vertices)
    elif o.type=='CURVES':
        cu=o.data;a=np.empty(len(cu.points)*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',a)
        r=np.empty(len(cu.points),dtype=np.float32);cu.attributes['radius'].data.foreach_get('value',r)
        if not np.isfinite(a).all() or not np.isfinite(r).all() or (r<=0).any():errors.append('Invalid hair: '+o.name)
        grooms.append({'object':o.name,'curves':len(cu.curves),'points':len(cu.points),'radius_min_m':float(r.min()),'radius_max_m':float(r.max())})
images=[]
for im in bpy.data.images:
    if im.source!='FILE':continue
    packed=bool(im.packed_file);exists=Path(bpy.path.abspath(im.filepath)).is_file()
    images.append({'name':im.name,'packed':packed,'local_source_exists':exists})
    if not packed and not exists:errors.append('Missing texture: '+im.name)
report={'version':VERSION,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'visible_mesh_objects':meshes,'source_mesh_vertices':verts,'native_grooms':grooms,'textures':images,'errors':errors,'structural_checks_passed':not errors,'artistic_status':'WIP, not approved, not reference quality','game_validation':'none; still scene only'}
report['relative_shape_key_checks']=shape_keys
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('STRUCTURAL_VALIDATION',not errors,len(grooms),meshes,flush=True)
if errors:raise RuntimeError(errors)
