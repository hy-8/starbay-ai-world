"""Read-only sampled nape/garment proximity diagnostic for actual geometry.

Signed nearest-face gaps on open garments flag potential contact, not a solid
inside/outside or motion collision proof. Representative flagged points saved.
"""
import bpy, sys, json, re, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
folder=ROOT/'Exports'/version
source=folder/'Ember_Regent.blend'
output=folder/'sampled_nape_garment_contact.json'
if output.exists():raise RuntimeError('Preserve prior diagnostic')
before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
verts=[];faces=[];face_objects=[];used=[]
for ob in bpy.data.objects:
    if ob.hide_render or ob.type!='MESH':continue
    if not any(s in ob.name.lower() for s in ['suit','collar','lapel','coat']):continue
    ev=ob.evaluated_get(dg);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    xyz=[tuple(ob.matrix_world@v.co) for v in mesh.vertices]
    if xyz and max(p[2] for p in xyz)>1.60:
        offset=len(verts);verts.extend(xyz)
        triangles=[tuple(offset+i for i in t.vertices) for t in mesh.loop_triangles]
        faces.extend(triangles);face_objects.extend([ob.name]*len(triangles));used.append(ob.name)
    ev.to_mesh_clear()
if not faces:raise RuntimeError('No actual upper garments')
bv=BVHTree.FromPolygons(verts,faces,all_triangles=True)
rear=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
p=np.empty(len(rear.data.points)*3,np.float32)
rear.data.attributes['position'].data.foreach_get('vector',p)
p=p.reshape(-1,len(rear.data.curves[0].points),3)
points=p[:,::4].reshape(-1,3)
points=points[(points[:,2]<1.735)&(points[:,1]>-.015)]
ids=np.linspace(0,max(0,len(points)-1),min(12000,len(points)),dtype=int)
rows=[]
for index in ids:
    q=Vector(points[index]);hit,normal,face,distance=bv.find_nearest(q)
    gap=float((q-hit).dot(normal))
    rows.append(dict(position_m=list(q),distance_m=float(distance),signed_face_gap_m=gap,nearest_object=face_objects[face]))
flags=[row for row in rows if row['distance_m']<.006 and row['signed_face_gap_m']<-.0005]
report=dict(source=version,source_sha256=before,source_unchanged=True,
    tested_objects=used,region='Posterior styling points z<1.735m and y>-.015m; every fourth curve point, up to 12000 deterministic uniform samples',
    sampled_points=len(rows),potential_contact_flags=len(flags),
    closest_distance_quantiles_m=np.quantile([r['distance_m'] for r in rows],[0,.5,1]).tolist() if rows else [],
    flagged_examples=sorted(flags,key=lambda r:r['signed_face_gap_m'])[:20],
    boundary='Nearest-face normals on open garments indicate potential contact only. Does not prove all-fiber clearance, surface crossing, cloth thickness, or motion safety.')
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SAMPLED_NAPE_CONTACT',len(rows),len(flags),used,flush=True)
