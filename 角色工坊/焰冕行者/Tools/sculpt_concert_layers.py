"""Art-directed guide groom and independent couture panels for real 3D stills.

Preserves atelier05. Every strand and applique is actual editable geometry.
No AI image replacement, animation or garment-simulation claim.
"""
import bpy, math, sys, re, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi

ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION
if OUT.exists():raise RuntimeError('Fresh candidate required')
OUT.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier05/Ember_Regent.blend'))
COL=bpy.data.collections
for ob in list(COL['05_Hair'].objects):bpy.data.objects.remove(ob,do_unlink=True)
body=max((o for o in COL['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
rng=np.random.default_rng(412);random.seed(412)

def spline(points,t):
    p=np.asarray(points,dtype=float);p=np.concatenate([p[:1],p,p[-1:]])
    v=np.minimum(t*(len(points)-1),len(points)-1-1e-7);i=v.astype(int);s=(v-i)[...,None]
    a,b,c,d=p[i],p[i+1],p[i+2],p[i+3]
    return .5*((2*b)+(-a+c)*s+(2*a-5*b+4*c-d)*s*s+(-a+3*b-3*c+d)*s*s*s)

guides=[]
# Swept crown/forehead: explicit comb trajectories with different lengths,
# instead of a radial spherical shell terminating at one shared hairline.
for side in [-1,1]:
    for k in range(27):
        f=k/26;rootx=(-.020 if side==1 else -.006)+random.uniform(-.008,.008)
        rooty=-.056+f*.125
        hit,n,_,_=bv.ray_cast(Vector((rootx,rooty,2.1)),Vector((0,0,-1)),.5)
        if hit is None:continue
        root=hit+n*.0004
        pts=[root,(side*(.040+.024*f),-.060+.10*f,1.918-.021*f),
             (side*(.083+.017*f),-.126+.115*f,1.851-.009*f),
             (side*(.081+.023*f),-.151+.11*f,1.784-.026*f),
             (side*(.038+.063*f),-.152+.12*f,1.738-.055*f+random.uniform(-.013,.013))]
        guides.append((pts,.0050,460,'crown'))
# Temple layers: independently layered curves, tapered and outward at tips.
for side in [-1,1]:
    for k in range(30):
        f=k/29;z=1.85-.125*f;y=-.08+.145*f
        hit,n,_,_=bv.ray_cast(Vector((side*.24,y,z)),Vector((-side,0,0)),.4)
        if hit is None:continue
        root=hit+n*.0005
        pts=[root,(side*.109,y-.008,z+.022),(side*(.115+.009*sin(k)),y+.007,z-.034),
             (side*(.085+.014*sin(k)),y+.017,z-.083),(side*(.101+.013*sin(k*1.7)),y+.029,z-.105-random.random()*.018)]
        guides.append((pts,.004,220,'temple'))
# Nape: varying length and wave phase avoids a flat rectangular hair curtain.
for k in range(70):
    a=pi*.52+pi*.96*k/69;th=random.uniform(.32,1.48)
    root=Vector((.086*sin(th)*sin(a),-.031-.10*sin(th)*cos(a),1.774+.104*cos(th)))
    hit,n,_,_=bv.find_nearest(root)
    if hit is not None:root=hit+n*.0005
    endz=random.uniform(1.605,1.703);side=1 if root.x>0 else -1
    pts=[root,(.10*sin(a),.075-.043*cos(a),max(root.z,1.81)),
         (.108*sin(a),.115-.023*cos(a),1.736),
         (.087*sin(a),.113-.018*cos(a),endz+.035),
         (.102*sin(a)+.010*sin(k),.123+.010*cos(k),endz)]
    guides.append((pts,.0048,250,'nape'))

positions=[];radii=[];steps=64
for points,width,num,region in guides:
    t=np.linspace(0,1,steps)[None,:]*rng.uniform(.86,1,(num,1))
    center=spline(points,t)
    tangent=np.gradient(center,axis=1);tangent/=np.maximum(np.linalg.norm(tangent,axis=2,keepdims=True),1e-9)
    basis=np.cross(tangent,np.array([0,1,0]));basis/=np.maximum(np.linalg.norm(basis,axis=2,keepdims=True),1e-9)
    normal=np.cross(tangent,basis)
    # Longitudinal offsets preserve natural strand separation within each lock.
    phase=rng.uniform(0,2*pi,(num,1));spread=(.55+.45*np.sin(pi*t))*(1-.85*t**4)
    u=rng.normal(0,width,(num,1))*spread+.0006*np.sin(t*17+phase)*np.sin(pi*t)
    v=rng.normal(0,width*.45,(num,1))*spread+.0004*np.sin(t*12+phase)*np.sin(pi*t)
    xyz=center+basis*u[...,None]+normal*v[...,None]
    positions.append(xyz.astype(np.float32));radii.append((rng.uniform(.000020,.000032,(num,1))*(1-.96*t)**.65).astype(np.float32))

xyz=np.concatenate(positions);rad=np.concatenate(radii)
cu=bpy.data.hair_curves.new('Hand directed layered guide fibers');cu.add_curves([steps]*len(xyz))
cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel())
ob=bpy.data.objects.new('Layered auburn guide groom',cu);COL['05_Hair'].objects.link(ob)
m=bpy.data.materials.new('Natural dark cherry hair fiber');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.34;bs.inputs['Radial Roughness'].default_value=.46
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.007,.0009,.0011,1);ramp.color_ramp.elements[1].color=(.052,.007,.006,1)
nt.links.new(info.outputs['Random'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs['Color']);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0]);cu.materials.append(m)
print('GUIDE_GROOM',len(guides),len(xyz),flush=True)

def mesh(name,verts,faces,material,group,sub=1,solid=.001):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL[group].objects.link(o);me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    if sub:q=o.modifiers.new('Silhouette smoothing','SUBSURF');q.levels=sub;q.render_levels=sub
    if solid:q=o.modifiers.new('Leather thickness','SOLIDIFY');q.thickness=solid;q.offset=0
    return o
def surface(name,fn,nu,nv,mat,group):
    return mesh(name,[fn(i/(nu-1),j/(nv-1)) for i in range(nu) for j in range(nv)],[(i*nv+j,(i+1)*nv+j,(i+1)*nv+j+1,i*nv+j+1) for i in range(nu-1) for j in range(nv-1)],mat,group)
def curve(name,pts,r,mat,group='06_Regalia'):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for v,p in zip(sp.points,pts):v.co=(*p,1)
    cu.materials.append(mat);o=bpy.data.objects.new(name,cu);COL[group].objects.link(o);return o
wine=bpy.data.materials['Atelier oxblood woven jacquard'];leather=bpy.data.materials['Atelier oxblood matte leather'];metal=bpy.data.materials['Atelier smoked silver'];thread=bpy.data.materials['Atelier red sewn thread']

# Pull the suit hem into a fitted frock-coat body, retaining the original mesh UV.
# All associated front ornaments follow the same edit before new details are fitted.
def tailor(p):
    x,y,z=p;w=max(0,min(1,(1.32-z)/.24));center=math.exp(-(abs(x)/.20)**8)
    return Vector((x*(1-.075*w*center),y*(1-.035*w*center),z-.16*w*center))
for group in ['03_OuterRobe','06_Regalia']:
    for o in list(COL[group].objects):
        if not any(q in o.name for q in ['Fitted CC0','Lapel','Fine fitted']):continue
        if o.type=='MESH':
            for v in o.data.vertices:v.co=tailor(v.co)
        elif o.type=='CURVE':
            for sp in o.data.splines:
                for p in sp.points:p.co=(*tailor(Vector(p.co[:3])),1)
suit=bpy.data.objects['Fitted CC0 male_elegantsuit01'];suit.data.update();bpy.context.view_layer.update();coatbv=BVHTree.FromObject(suit,bpy.context.evaluated_depsgraph_get())

# Layered asymmetrical textile panels laid over the existing coat, with controlled
# gravity folds and individually shaped hems. They are sewn to a waist/yoke.
def skirt(u,a):
    folds=(.010*sin(a*11+.8*u)+.005*sin(a*19-3*u))*u**1.25
    r=.169+.145*u**1.7+folds
    return Vector((r*sin(a),-(.136+.070*u+folds)*cos(a)+.064*u*u,1.088-.967*u+.018*u**4*sin(a*3)))
for k in range(17):
    a=.60+(2*pi-1.20)*k/16;length=random.uniform(.59,.94);width=random.uniform(.085,.13)
    def panel(u,v,a=a,length=length,width=width,k=k):
        progress=u*length+.012
        theta=a+(v-.5)*width*2*(1-.82*u**6)+.024*sin(u*6+k)*u
        p=skirt(progress,theta);out=Vector((sin(theta),-cos(theta),0))
        p+=out*(.005+.005*sin(pi*v)+.008*u*u)
        p.z+=.015*sin(pi*v)*u*u
        return p
    surface('Independent tailored over-panel %02d'%k,panel,65,13,leather if k%3==0 else wine,'03_OuterRobe')
    for edge in [.04,.96]:curve('Over-panel sewn edge',[panel(j/90,edge) for j in range(91)],.0006,thread)
    if k%2==0:
        for side in [-1,1]:
            pts=[]
            for j in range(90):
                u=.12+.75*j/89;v=.5+side*.23*sin(u*14+k)
                p=panel(u,v)+Vector((sin(a),-cos(a),0))*.002;pts.append(p)
            curve('Panel ornamental metal inlay',pts,.00065,metal)

# Fine leather scales on shoulders and front yoke. This is overlapping sewn
# material rather than spikes or particle effects.
for side in [-1,1]:
    for row in range(5):
        for col in range(6):
            x=side*(.150+row*.026);y=-.102+col*.035
            hit,n,_,_=coatbv.ray_cast(Vector((x,y,1.85)),Vector((0,0,-1)),.45)
            if hit is None:continue
            root=hit+n*.004;L=.065+random.random()*.035;w=.015
            def scale(u,v,root=root,L=L,w=w,side=side):
                p=root+Vector((side*.052*u,(v-.5)*w*2*(1-u**3),-.055*u-.015*u*u))
                h,n,_,_=coatbv.find_nearest(p)
                return (h+n*(.004+.007*sin(pi*u)+.002*sin(pi*v))) if h is not None else p
            surface('Stitched leather shoulder scale',scale,18,7,leather,'06_Regalia')
            curve('Shoulder scale spine',[scale(j/25,.5) for j in range(26)],.00055,metal)

# Face refinement: preserve the known skin UV while broadening jaw planes and
# giving the mouth a more relaxed, closed rest position.
for v in body.data.vertices:
    x,y,z=v.co
    if y<-.06 and 1.64<z<1.73:
        w=math.exp(-((x/.045)**2+((z-1.670)/.036)**2));v.co.x*=1+.040*w
    if y<-.110 and abs(x)<.031 and 1.661<z<1.699:
        w=math.exp(-(x/.025)**4)*math.exp(-((z-1.683)/.011)**2)
        v.co.z+=(1.683-z)*.10*w
body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
usage=json.loads((ROOT/'Exports/atelier05/asset_usage.json').read_text(encoding='utf-8'))
usage.update({'source':'atelier05','version':VERSION,'groom':{'method':'explicit crown, temple and nape guides; native editable fibers','guide_count':len(guides),'strand_count':len(xyz)},'wardrobe':'frock coat hem reshaping, individual sewn over-panels, fitted yoke appliques','status':'candidate requiring rendered inspection'})
(OUT/'asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
print('SCULPT_LAYERS_SAVED',str(OUT),flush=True)
