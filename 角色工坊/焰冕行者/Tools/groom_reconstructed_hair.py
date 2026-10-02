"""Trace reconstructed lock surfaces into native 3D fibers for close review.

The hidden high-poly source remains editable. Hair orientation uses fitted
surface curvature and an asymmetric scalp comb field, not image billboards.
Blender: -- new-version source-version [--draft]
"""
import bpy, sys, re, json, math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]; version,source=args[:2]; draft='--draft' in args
for value in [version,source]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',value): raise ValueError(value)
out=ROOT/'Exports'/version; render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/source/'Ember_Regent.blend'))
col=bpy.data.collections['05_Hair'];ob=next(o for o in col.objects if o.type=='MESH')
dec=ob.modifiers.new('Temporary guide topology','DECIMATE');dec.ratio=.035
bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
pos=np.array([v.co[:] for v in me.vertices],dtype=np.float64)
norm=np.array([v.normal[:] for v in me.vertices],dtype=np.float64)
tri=np.array([p.vertices[:] for p in me.polygons],dtype=np.int32)
if tri.shape[1]!=3:raise RuntimeError('Triangles required')
bv=BVHTree.FromPolygons([Vector(p) for p in pos],tri.tolist(),all_triangles=True)
kd=KDTree(len(pos))
for i,p in enumerate(pos):kd.insert(Vector(p),i)
kd.balance()
print('CURVATURE_GUIDE_TOPOLOGY',len(pos),len(tri),flush=True)

# Fit each local 2x2 shape operator to neighboring normal differences. Its
# smaller-magnitude principal curvature follows the reconstructed lock axis.
base=np.cross(norm,np.array([0.,1.,0.]));base/=np.maximum(np.linalg.norm(base,axis=1,keepdims=True),1e-9)
other=np.cross(norm,base)
neighbors=np.array([[idx for _,idx,_ in kd.find_n(Vector(p),16)] for p in pos])
delta=pos[neighbors]-pos[:,None,:];dn=norm[neighbors]-norm[:,None,:]
u=np.stack([(delta*base[:,None,:]).sum(2),(delta*other[:,None,:]).sum(2)],axis=-1)
w=np.stack([(dn*base[:,None,:]).sum(2),(dn*other[:,None,:]).sum(2)],axis=-1)
ata=np.einsum('nki,nkj->nij',u,u)+np.eye(2)[None,:,:]*1e-8
atb=np.einsum('nki,nkj->nij',u,w)
operator=np.linalg.solve(ata,atb);operator=(operator+operator.transpose(0,2,1))*.5
val,vec=np.linalg.eigh(operator);choice=np.argmin(np.abs(val),axis=1)
v=vec[np.arange(len(pos)),:,choice];principal=base*v[:,0,None]+other*v[:,1,None]
strength=np.clip((np.abs(val).max(1)-np.abs(val).min(1))/(np.abs(val).max(1)+5),0,.90)
globalflow=np.zeros_like(pos)
side=np.where(pos[:,0]>.018,1.,-1.)
top=np.clip((pos[:,2]-1.80)/.08,0,1)
globalflow[:,0]=side*(.18+1.2*top)
globalflow[:,1]=np.clip((pos[:,1]+.04)*2,-.18,.24)*top
globalflow[:,2]=-1.+.95*top
globalflow-=norm*(globalflow*norm).sum(1,keepdims=True)
globalflow/=np.maximum(np.linalg.norm(globalflow,axis=1,keepdims=True),1e-9)
principal*=np.where((principal*globalflow).sum(1)>0,1.,-1.)[:,None]
flow=principal*strength[:,None]+globalflow*(1-strength[:,None])
flow/=np.maximum(np.linalg.norm(flow,axis=1,keepdims=True),1e-9)
np.savez_compressed(out/'surface_comb_field.npz',positions=pos,normals=norm,flow=flow,triangles=tri)

def field(p):
    hit,n,idx,d=bv.find_nearest(Vector(p))
    if hit is None:return None
    ids=tri[idx];pp=np.asarray(hit);dd=np.linalg.norm(pos[ids]-pp,axis=1)
    weight=1/np.maximum(dd,.00015);weight/=weight.sum()
    direction=(flow[ids]*weight[:,None]).sum(0)
    normal=(norm[ids]*weight[:,None]).sum(0);normal/=max(1e-8,np.linalg.norm(normal))
    direction-=normal*np.dot(direction,normal);direction/=max(1e-8,np.linalg.norm(direction))
    return pp,normal,direction

def trace(start,sign,steps):
    path=[];p=start.copy();last=None
    for k in range(steps):
        f=field(p)
        if f is None:break
        q,n,d=f
        if last is not None:
            d=d*.7+last*.3;d-=n*np.dot(n,d);d/=max(1e-8,np.linalg.norm(d))
        if path and np.linalg.norm(q-path[-1])<.00025:break
        path.append(q);last=d;p=q+d*(sign*.0017)
        if sign<0 and q[2]>1.901 and abs(q[0]-.018)<.002:break
        if q[2]<1.631:break
    return np.asarray(path)

rng=np.random.default_rng(10302)
center=np.array([0.,-.044,1.775]);outside=(norm*(pos-center)).sum(1)>.008
eligible=np.where(outside & (pos[:,2]>1.65))[0]
selected=rng.choice(eligible,size=min(4200,len(eligible)),replace=False)
paths=[];radii=[];guide_data=[];N=96;t=np.linspace(0,1,N)
for gi,idx in enumerate(selected):
    seed=pos[idx];back=trace(seed,-1,130);front=trace(seed,1,100)
    if len(back)<3 or len(front)<3:continue
    g=np.vstack([back[::-1],front[1:]])
    seg=np.linalg.norm(np.diff(g,axis=0),axis=1);cum=np.r_[0,np.cumsum(seg)]
    if cum[-1]<.026:continue
    # Use actual surface paths with unequal endpoints and slight normal lift.
    target=np.linspace(0,cum[-1],N)
    g=np.column_stack([np.interp(target,cum,g[:,j]) for j in range(3)])
    tangent=np.gradient(g,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-9)
    radial=g-center;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-9)
    lateral=np.cross(tangent,radial);lateral/=np.maximum(np.linalg.norm(lateral,axis=1,keepdims=True),1e-9)
    radial=np.cross(lateral,tangent)
    count=24;phase=rng.uniform(0,2*math.pi,(count,1))
    spread=rng.normal(0,.0010,(count,1))*(1-.70*t**5)
    lateraloffset=spread+.00055*np.sin(t*20+phase)*np.sin(math.pi*t)
    normaloffset=.00055+rng.uniform(0,.0013,(count,1))+.00045*np.sin(t*24+phase)*np.sin(math.pi*t)
    xyz=g[None,:,:]+lateral[None,:,:]*lateraloffset[:,:,None]+radial[None,:,:]*normaloffset[:,:,None]
    stop=rng.uniform(.86,1.,(count,1));q=t*stop*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);f=(q-lo)[:,:,None]
    xyz=xyz[np.arange(count)[:,None],lo]*(1-f)+xyz[np.arange(count)[:,None],hi]*f
    paths.append(xyz.astype(np.float32));radii.append((rng.uniform(.000026,.000041,(count,1))*(1-.97*t)**.60).astype(np.float32))
    guide_data.append(g.astype(np.float32))
    if gi%500==0:print('SURFACE_GUIDES',gi,len(selected),len(paths),flush=True)
ev.to_mesh_clear();ob.modifiers.remove(dec)
xyz=np.concatenate(paths);radius=np.concatenate(radii)
cu=bpy.data.hair_curves.new('Native fibers traced along sculpted wig locks');cu.add_curves([N]*len(xyz))
cu.attributes['position'].data.foreach_set('vector',xyz.ravel())
cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.ravel())
hair=bpy.data.objects.new('Cherry asymmetric surface groom',cu);col.objects.link(hair)
mat=bpy.data.materials.new('Cherry fiber roughness variation');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Radial Roughness'].default_value=.62
hi=nt.nodes.new('ShaderNodeHairInfo');r=nt.nodes.new('ShaderNodeValToRGB')
r.color_ramp.elements[0].color=(.016,.0015,.003,1);r.color_ramp.elements[1].color=(.085,.009,.017,1)
nt.links.new(hi.outputs['Random'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Color'])
rough=nt.nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.34;rough.inputs['To Max'].default_value=.56
nt.links.new(hi.outputs['Random'],rough.inputs['Value']);nt.links.new(rough.outputs['Result'],bs.inputs['Roughness'])
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],output.inputs[0]);cu.materials.append(mat)
if '--fill-scalp' in args:
    # The reconstructed wig determines the visible sculpted locks; a shorter
    # scalp-rooted native groom fills only its crown/temple gaps underneath.
    with bpy.data.libraries.load(str(ROOT/'Exports/hairdesign02/Ember_Regent.blend'),link=False) as (data_in,data_out):
        data_out.objects=['Asymmetric layered wolf cut groom']
    under=data_out.objects[0]
    if under is None:raise RuntimeError('Scalp groom unavailable')
    total=len(under.data.attributes['position'].data)
    srcpos=np.empty(total*3,dtype=np.float32);under.data.attributes['position'].data.foreach_get('vector',srcpos)
    srcrad=np.empty(total,dtype=np.float32);under.data.attributes['radius'].data.foreach_get('value',srcrad)
    count=870*58;num=count*72
    support=bpy.data.hair_curves.new('Scalp-rooted short undercoat');support.add_curves([72]*count)
    support.attributes['position'].data.foreach_set('vector',srcpos[:num*3])
    support.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',srcrad[:num]*.9)
    supob=bpy.data.objects.new('Scalp rooted coverage beneath sculpted locks',support);col.objects.link(supob)
    support.materials.append(mat);bpy.data.objects.remove(under,do_unlink=True)
ob.name='EDITABLE_SOURCE reconstructed fitted wig';ob.hide_render=True;ob.hide_set(True)
scene=bpy.context.scene;scene.cycles_curves.shape='THICK';scene.cycles.samples=64 if draft else 192
scene.render.resolution_percentage=70 if draft else 100
if '--detail' in args:
    scene.render.resolution_x=1800;scene.render.resolution_y=2100;scene.render.resolution_percentage=100
    scene.cycles.samples=256;scene.cycles.use_denoising=False
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'version':version,'source':source,'method':'surface curvature and asymmetric comb field traced into native hair curves','guides':len(guide_data),'strands':len(xyz),'scalp_undercoat_strands':50460 if '--fill-scalp' in args else 0,'points_per_strand':N,'source_mesh_visible':False,'renderer':'Cycles OptiX','curve_shape':'THICK','samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'status':'candidate requires visual review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
np.savez_compressed(out/'groom_guides.npz',guides=np.asarray(guide_data))
print('SURFACE_GROOM_SAVED',report,flush=True)
