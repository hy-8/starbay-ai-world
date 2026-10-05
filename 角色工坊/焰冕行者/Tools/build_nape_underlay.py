"""Original narrow lofted underlay locks beneath existing native nape fibers.

No imported hair-card artwork or new licensed donor. Added meshes are editable,
and retained native fibers/body/clothing are not altered.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or renders.exists():raise RuntimeError('Fresh version required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],dg)
vv=[];ff=[]
for name in ['Fitted CC0 male_elegantsuit01','Tailored standing rear collar']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();offset=len(vv)
    vv.extend(tuple(ob.matrix_world@v.co) for v in m.vertices)
    ff.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles);ev.to_mesh_clear()
coat=BVHTree.FromPolygons(vv,ff,all_triangles=True)
rear=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(rear.matrix_world),np.eye(4)):raise RuntimeError('Neutral groom required')
p=np.empty(len(rear.data.points)*3,np.float32);rear.data.attributes['position'].data.foreach_get('vector',p)
p=p.reshape(-1,len(rear.data.curves[0].points),3)
ids=np.flatnonzero((p[:,0,2]<1.805)&(p[:,0,1]>.025))
roots=p[ids,0].astype(float);pool=roots[::8]
selected=[int(np.argmin(np.linalg.norm(pool-np.median(pool,axis=0),axis=1)))];dmin=np.full(len(pool),np.inf)
for _ in range(27):
    dmin=np.minimum(dmin,np.sum((pool-pool[selected[-1]])**2,axis=1));selected.append(int(np.argmax(dmin)))
centers=pool[selected];labels=np.argmin(np.sum((roots[:,None]-centers[None])**2,axis=2),axis=1)
col=bpy.data.collections.new('Original nape underlay locks • editable mesh prototype')
bpy.context.scene.collection.children.link(col)
mat=bpy.data.materials.new('Original nape underlay • strand-direction shading');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links
bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.75
bs.inputs['Anisotropic'].default_value=.15
bs.inputs['Specular IOR Level'].default_value=.18
bs.inputs['Coat Weight'].default_value=0
uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY'
mapping.inputs[1].default_value=(35,.035,1);links.new(uv.outputs['UV'],mapping.inputs[0])
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=2
links.new(mapping.outputs[0],noise.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.012,.001,.003,1)
ramp.color_ramp.elements[1].color=(.05,.004,.009,1)
links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.00015
links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
alpha=nodes.new('ShaderNodeValToRGB');alpha.color_ramp.elements[0].position=.38
alpha.color_ramp.elements[0].color=(0,0,0,1)
alpha.color_ramp.elements[1].position=.68;alpha.color_ramp.elements[1].color=(.48,.48,.48,1)
links.new(noise.outputs['Fac'],alpha.inputs[0])
transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
links.new(alpha.outputs['Color'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
added=[];scalp_repairs=0;coat_repairs=0
for label in range(len(centers)):
    group=p[ids[labels==label]].astype(float)
    if len(group)<50:continue
    # Median is only the added underlay silhouette; the dense personal fibers
    # above it stay byte-for-byte intact, including all root and radius data.
    base=np.median(group,axis=0)
    N=len(base);tt=np.linspace(0,1,N)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(base,axis=0),axis=1))]
    guide=np.stack([np.interp(tt*.90*arc[-1],arc,base[:,k]) for k in range(3)],axis=1)
    tangent=np.gradient(guide,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    across=np.cross(tangent,np.tile((0,1,0),(N,1)));across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-9)
    normal=np.cross(across,tangent)
    halfwidth=.0045+(.0015*np.sin(label*2.4))
    # A narrow, flattened 3D ribbon with staggered taper; no blunt strip edge.
    widths=halfwidth*np.sin(np.pi*tt)**.7
    verts=[];faces=[];uvcoords=[]
    for j in range(N):
        for k in range(8):
            angle=2*np.pi*k/8
            q=guide[j]+across[j]*(widths[j]*np.cos(angle))+normal[j]*(widths[j]*.07*np.sin(angle))
            q[1]-=.001
            hit,nn,_,distance=bv.find_nearest(Vector(q));gap=(Vector(q)-hit).dot(nn)
            if gap<.001 and distance<.025:q+=np.array(nn)*(.0012-gap);scalp_repairs+=1
            if q[2]<1.735:
                hit,_,_,_=coat.ray_cast(Vector((q[0],.4,q[2])),Vector((0,-1,0)),.7)
                if hit and q[1]<hit.y+.0025:q[1]=hit.y+.0025;coat_repairs+=1
            verts.append(tuple(q));uvcoords.append((.5+.5*np.cos(angle),float(tt[j])))
    for j in range(N-1):
        for k in range(8):faces.append((j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k))
    mesh=bpy.data.meshes.new(f'Original nape lock {label:02d} mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    layer=mesh.uv_layers.new(name='Original strand direction UV')
    for poly in mesh.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:layer.data[li].uv=uvcoords[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new(f'Original nape underlay {label:02d}',mesh);col.objects.link(ob);mesh.materials.append(mat)
    added.append(dict(object=ob.name,vertices=len(verts),faces=len(faces),native_source_fibers=len(group),maximum_halfwidth_m=halfwidth))
out.mkdir(parents=True);renders.mkdir(parents=True)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='Add28 narrow original flattened loft underlay locks following actual nape groups, tapered ends and original UV directional procedural shading; all native fibers unchanged',
    components=[],added_visible_meshes=[r['object'] for r in added],added_mesh_details=added,radii_unchanged=True,
    scalp_vertex_repairs=scalp_repairs,coat_vertex_repairs=coat_repairs,
    shader='Dark matte underlay with long directional procedural transparency, maximum per-surface opaque blend .48; no coated specular ribbon',
    license='New mesh/UV/procedural shader original. Retained support/donors retain existing licenses; no new source asset or imported textures.',
    collision_scope='Discrete added vertices nearest-body guard and posterior clothing-ray guard, not full surface/strand/animation collision proof',
    status='Unreviewed nape underlay prototype; not artistic approval')
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400;scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(renders/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('NAPE_UNDERLAY_RENDERED',version,len(added),flush=True)
