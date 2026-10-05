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
AUDIT_CUT='--audit-cut' in sys.argv[sys.argv.index('--')+1:]
AUDIT_FRINGE='--audit-fringe' in sys.argv[sys.argv.index('--')+1:]
if AUDIT_FRINGE and not AUDIT_CUT:raise ValueError('Fringe subset audit requires source-paired cut audit')
report_path=folder/('groom_cut_validation.json' if AUDIT_CUT else 'structural_validation.json')
if report_path.exists():raise RuntimeError('Existing validation is preserved')
def cut_snapshot():
    meshes={};grooms={}
    for ob in bpy.data.objects:
        if ob.hide_render:continue
        matrix=np.array(ob.matrix_world,np.float32).tobytes()
        if ob.type=='MESH':
            a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
            blob=a.tobytes()+matrix+repr([tuple(f.vertices) for f in ob.data.polygons]).encode()
            for layer in ob.data.uv_layers:blob+=np.array([x.uv[:] for x in layer.data],np.float32).tobytes()
            if ob.data.shape_keys:
                for key in ob.data.shape_keys.key_blocks:
                    a=np.empty(len(key.data)*3,np.float32);key.data.foreach_get('co',a)
                    blob+=a.tobytes()+repr((key.name,float(key.value))).encode()
            meshes[ob.name]=hashlib.sha256(blob).hexdigest()
        elif ob.type=='CURVES':
            sizes=[len(c.points) for c in ob.data.curves]
            if len(set(sizes))!=1:raise RuntimeError('Cut audit requires uniform curve point counts')
            p=np.empty(len(ob.data.points)*3,np.float32);ob.data.attributes['position'].data.foreach_get('vector',p)
            r=np.empty(len(ob.data.points),np.float32);ob.data.attributes['radius'].data.foreach_get('value',r)
            p=p.reshape(-1,sizes[0],3);r=r.reshape(-1,sizes[0])
            grooms[ob.name]=dict(roots=p[:,0].copy(),root_radii=r[:,0].copy(),matrix=matrix,
                sha256=hashlib.sha256(p.tobytes()+r.tobytes()+matrix).hexdigest(),
                radii_sha256=hashlib.sha256(r.tobytes()).hexdigest())
            if AUDIT_FRINGE and ob.name.startswith('Authored frontal revision'):
                design=json.loads((ROOT/'Exports/spatialfringe17/authored_fringe_design.json').read_text(encoding='utf-8'))
                if sum(row['assigned_visible_fibers'] for row in design)!=len(p):raise RuntimeError('Frontal region counts differ')
                ids={'crown':[],'fringe':[]};offset=0;spread=[]
                for row in design:
                    count=row['assigned_visible_fibers'];key='crown' if 'segmented crown' in row['name'] else 'fringe'
                    ids[key].extend(range(offset,offset+count))
                    if key=='fringe':
                        group=p[offset:offset+count]
                        median=np.median(group,axis=0)
                        j=np.array([0,int(.5*(group.shape[1]-1)),group.shape[1]-1])
                        spread.append(np.quantile(np.linalg.norm(group[:,j]-median[None,j],axis=2),.9,axis=0))
                    offset+=count
                grooms[ob.name]['region_sha256']={key:hashlib.sha256(p[index].tobytes()+r[index].tobytes()+matrix).hexdigest() for key,index in ids.items()}
                grooms[ob.name]['fringe_group_spread90_quantiles_m']=np.quantile(np.array(spread),[0,.5,1],axis=0).tolist()
                grooms[ob.name]['region_counts']={key:len(index) for key,index in ids.items()}
    return meshes,grooms
if AUDIT_CUT:
    cut_manifest=json.loads((folder/'shag_cut_manifest.json').read_text(encoding='utf-8'))
    cut_source=ROOT/'Exports'/cut_manifest['source']/'Ember_Regent.blend'
    if hashlib.sha256(cut_source.read_bytes()).hexdigest()!=cut_manifest['source_sha256']:raise RuntimeError('Declared cut source changed')
    bpy.ops.wm.open_mainfile(filepath=str(cut_source),use_scripts=False)
    source_meshes,source_grooms=cut_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
errors=[];meshes=0;verts=0;grooms=[];shape_keys=[]
if AUDIT_CUT:
    candidate_meshes,candidate_grooms=cut_snapshot()
    modified={row['object'] for row in cut_manifest['components']}
    checks=dict(all_visible_meshes_uvs_shape_keys_and_transforms_unchanged=source_meshes==candidate_meshes,
                native_groom_object_set_unchanged=set(source_grooms)==set(candidate_grooms),
                all_native_groom_transforms_unchanged=all(source_grooms[n]['matrix']==candidate_grooms[n]['matrix'] for n in source_grooms),
                all_native_groom_roots_exactly_unchanged=all(np.array_equal(source_grooms[n]['roots'],candidate_grooms[n]['roots']) for n in source_grooms),
                all_native_root_radii_exactly_unchanged=all(np.array_equal(source_grooms[n]['root_radii'],candidate_grooms[n]['root_radii']) for n in source_grooms),
                unmodified_native_grooms_exactly_unchanged=all(source_grooms[n]['sha256']==candidate_grooms[n]['sha256'] for n in set(source_grooms)-modified))
    if cut_manifest.get('added_visible_meshes'):
        declared=set(cut_manifest['added_visible_meshes'])
        added=set(candidate_meshes)-set(source_meshes)
        checks.pop('all_visible_meshes_uvs_shape_keys_and_transforms_unchanged')
        checks['retained_visible_meshes_uvs_shape_keys_and_transforms_unchanged']=all(candidate_meshes.get(n)==sha for n,sha in source_meshes.items())
        checks['added_visible_mesh_set_exactly_declared']=added==declared and declared.isdisjoint(source_meshes)
    for key,passed in checks.items():
        if not passed:errors.append('Cut invariant failed: '+key)
    if cut_manifest.get('radii_unchanged'):
        checks['all_native_groom_radii_exactly_unchanged']=all(source_grooms[n]['radii_sha256']==candidate_grooms[n]['radii_sha256'] for n in source_grooms)
        if not checks['all_native_groom_radii_exactly_unchanged']:errors.append('Declared unchanged native radii differ')
    if AUDIT_FRINGE:
        frontal=next(name for name in source_grooms if name.startswith('Authored frontal revision'))
        unchanged_region='crown' if cut_manifest.get('fringe_fiber_fields_reset') else 'fringe' if cut_manifest.get('full_crown_flow_rebuilt') or cut_manifest.get('crown_spatial_field') else None
        if unchanged_region is None:raise RuntimeError('Declare an isolated fringe or crown rebuild for subset audit')
        region_passed=source_grooms[frontal]['region_sha256'][unchanged_region]==candidate_grooms[frontal]['region_sha256'][unchanged_region]
        if not region_passed:errors.append('Declared untouched frontal region changed: '+unchanged_region)
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
if AUDIT_CUT:
    report['paired_cut_invariants']=checks
    report['declared_cut_source']=cut_manifest['source']
    report['paired_scope']='Exact saved root/root-radius/transform hashes and unmodified mesh/UV/shape-key/groom data; does not prove silhouette quality or full collisions/animation'
    if AUDIT_FRINGE:
        report['frontal_subset_audit']=dict(unchanged_region=unchanged_region,unchanged_region_exactly_preserved=region_passed,
            source_region_sha256=source_grooms[frontal]['region_sha256'],candidate_region_sha256=candidate_grooms[frontal]['region_sha256'],
            region_counts=candidate_grooms[frontal]['region_counts'],
            source_fringe_spread90_quantiles_m=source_grooms[frontal]['fringe_group_spread90_quantiles_m'],
            candidate_fringe_spread90_quantiles_m=candidate_grooms[frontal]['fringe_group_spread90_quantiles_m'],
            spread_scope='Per fine-guide group90% Euclidean point distance to actual group median at root, middle and tip; each column reports min/median/max across groups. Includes staggered lengths; not a projected ribbon width or artistic score.')
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('STRUCTURAL_VALIDATION',not errors,len(grooms),meshes,flush=True)
if errors:raise RuntimeError(errors)
