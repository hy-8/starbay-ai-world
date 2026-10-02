"""Second concert direction: native strand groom and tailored textile surfaces.
Load the preserved concert14 geometry, save to a fresh candidate. Offline only.
"""
import bpy,bmesh,math,sys,json,random,re
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];VERSION=args[0];DRAFT='--draft' in args
if not re.fullmatch(r'[A-Za-z0-9_-]+',VERSION):raise ValueError('Invalid version')
OUT=ROOT/'Exports'/VERSION;RENDER=ROOT/'Renders'/VERSION
if OUT.exists() or RENDER.exists():raise RuntimeError('Use fresh output directories')
OUT.mkdir(parents=True);RENDER.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/concert14/Ember_Regent.blend'))
COL={c.name:c for c in bpy.data.collections}
scene=bpy.context.scene

def mat(name,color,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
def mesh(name,verts,faces,material,group,sub=0,solid=0):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COL[group].objects.link(o);me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    if sub:
        m=o.modifiers.new('Surface refinement','SUBSURF');m.levels=sub;m.render_levels=sub
    if solid:
        m=o.modifiers.new('Real garment thickness','SOLIDIFY');m.thickness=solid;m.offset=0
    return o
def curve(name,pts,r,material,group):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    cu.materials.append(material);o=bpy.data.objects.new(name,cu);COL[group].objects.link(o);return o
def surface(name,fn,nu,nv,material,group,sub=1,solid=.001):
    pts=[fn(i/(nu-1),j/(nv-1)) for i in range(nu) for j in range(nv)]
    faces=[(i*nv+j,(i+1)*nv+j,(i+1)*nv+j+1,i*nv+j+1) for i in range(nu-1) for j in range(nv-1)]
    ob=mesh(name,pts,faces,material,group,sub,solid);layer=ob.data.uv_layers.new(name='AtelierUV')
    for p in ob.data.polygons:
        for li,vi in zip(p.loop_indices,p.vertices):layer.data[li].uv=(vi%nv/(nv-1),vi//nv/(nv-1))
    return ob
def bez(p,t):return Vector(p[0])*(1-t)**3+Vector(p[1])*3*t*(1-t)**2+Vector(p[2])*3*t*t*(1-t)+Vector(p[3])*t**3

# Remove the entire old helmet/card hair and its sparse attached ribbons.
for ob in list(COL['05_Hair'].objects):bpy.data.objects.remove(ob,do_unlink=True)

# Native Blender hair curves: Cycles shades these as fibers, not beveled tubes.
# Strand positions are actual 3D geometry, with root-to-tip radii and loose ends.
rng=np.random.default_rng(20261002);parents=640;children=100;count=parents*children;steps=56
parent_az=rng.uniform(-pi,pi,(parents,1))
az=np.repeat(parent_az,children,axis=0)+rng.normal(0,.024,(count,1));front=np.maximum(0,np.cos(az));back=np.maximum(0,-np.cos(az));side=np.where(np.sin(az)>=0,1.,-1.)
maxroot=1.53-.50*front+.30*back
root_uniform=np.repeat(rng.uniform(0,1,(parents,1)),children,axis=0)
theta0=np.arccos(1-root_uniform*(1-np.cos(maxroot)))+rng.normal(0,.018,(count,1))
theta0=np.maximum(.005,theta0)
layer=np.repeat(rng.normal(0,.20,(parents,1)),children,axis=0)
theta1=1.52+.32*(1-front)+layer+rng.normal(0,.025,(count,1))
theta1=np.maximum(theta1,theta0+.23)
t=np.linspace(0,1,steps,dtype=np.float32)[None,:]
theta=theta0+(theta1-theta0)*(t*.9+.1*t*t)
sweep=side*(.22*front+.12)*np.sin(pi*t*.65)
a=az+sweep
phase=np.repeat(rng.uniform(0,2*pi,(parents,1)),children,axis=0)
lift=(.009+.014*(1-theta0/2))*np.maximum(0,np.sin(pi*t))**.8
wave=(.007*np.sin(t*7+phase)+.0015*np.sin(t*15+phase*1.7))*np.sin(pi*t)**2
a+=.045*np.sin(t*7+phase)*np.sin(pi*t)**2
rx=.088+lift+wave;ry=.106+lift+wave
x=rx*np.sin(theta)*np.sin(a)
y=-.031-ry*np.sin(theta)*np.cos(a)
z=1.774+(.105+lift*.7)*np.cos(theta)
free=np.maximum(0,(t-.60)/.40)**1.5
length=(.035+.10*back+.035*(1-front))*(.40+np.repeat(rng.uniform(0,1,(parents,1)),children,axis=0))
z-=free*length
x+=side*free*(.008*np.sin(t*9+phase)+rng.normal(0,.002,(count,1)))
y+=free*(.018*back-.015*front)
# Prevent front curtains from closing completely over the face; keep asymmetric part.
x+=side*.004*front*np.sin(pi*t*.8)
xyz=np.stack(np.broadcast_arrays(x,y,z),axis=-1).astype(np.float32)
# Roots sit on the actual morph surface, not the old hair mesh.
body=max((o for o in COL['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'chest' not in o.name.lower() and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
print('GROOM_SCALP',body.name,flush=True)
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
for i in range(count):
    p=Vector(xyz[i,0]);hit,normal,_,_=bv.find_nearest(p)
    if hit is not None and (hit-p).length<.032:
        delta=np.array(hit+normal*.0003-p,dtype=np.float32)
        xyz[i]+=delta[None,:]*(1-t.T)**2
hair=bpy.data.hair_curves.new('Redline native groom 64000 strands');hair.add_curves([steps]*count)
hair.attributes['position'].data.foreach_set('vector',xyz.ravel())
radius=hair.attributes.new('radius','FLOAT','POINT')
rad=(rng.uniform(.000032,.000052,(count,1))*(1-.93*t)**.7).astype(np.float32)
radius.data.foreach_set('value',rad.ravel())
ob=bpy.data.objects.new('Native medium auburn strand groom',hair);COL['05_Hair'].objects.link(ob)
hm=bpy.data.materials.new('Physical auburn native fibers');hm.use_nodes=True;nt=hm.node_tree;nt.nodes.clear()
out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.40;bs.inputs['Radial Roughness'].default_value=.53
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.008,.0005,.0015,1);ramp.color_ramp.elements[1].color=(.055,.005,.011,1)
nt.links.new(info.outputs['Random'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],bs.inputs['Color']);nt.links.new(bs.outputs[0],out.inputs[0]);hair.materials.append(hm)
print('NATIVE_GROOM_READY',count,flush=True)

# Art-directed asymmetric forelocks sit over the regular scalp comb. These are
# strand bundles, with varied tips and scatter, not opaque meshed ribbon locks.
bangs=[];bangr=[];random.seed(211)
for side,number in [(1,16),(-1,10)]:
    for k in range(number):
        f=k/max(1,number-1);rx=-.023 if side==1 else .008;ry=-.032+.062*f
        root,normal,_,_=bv.ray_cast(Vector((rx,ry,2.1)),Vector((0,0,-1)),.5)
        if root is None:continue
        root+=normal*.0008
        guide=[root,Vector((side*(.057+.02*f),-.133+.075*f,1.907-.025*f)),Vector((side*(.079+.01*f),-.164+.050*f,1.82-.018*f)),Vector((side*(.029+.051*f),-.153+.048*f,1.754+.025*sin(k*.8)))]
        for strand in range(260):
            ox=random.gauss(0,.0025);oy=random.gauss(0,.0018);phase0=random.uniform(0,2*pi);end=random.uniform(.83,1);path=[]
            for j in range(steps):
                t0=j/(steps-1)*end;c=bez(guide,t0)
                c+=Vector((ox*sin(pi*t0*.75)+.001*sin(t0*12+phase0)*sin(pi*t0),oy*sin(pi*t0),0));path.append(c)
            bangs.append(path);bangr.extend([random.uniform(.000033,.000044)*(1-.93*j/(steps-1))**.7 for j in range(steps)])
bc=bpy.data.hair_curves.new('Swept fringe native strands');bc.add_curves([steps]*len(bangs));bc.attributes['position'].data.foreach_set('vector',np.asarray(bangs,dtype=np.float32).ravel());bc.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.asarray(bangr,dtype=np.float32));bc.materials.append(hm)
bo=bpy.data.objects.new('Asymmetric swept native fringe',bc);COL['05_Hair'].objects.link(bo)

def textile(name,color):
    m=mat(name,color,.65);nt=m.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.27;p.inputs['Specular IOR Level'].default_value=.25
    tc=nt.nodes.new('ShaderNodeTexCoord')
    micro=nt.nodes.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=1900;micro.inputs['Detail'].default_value=2
    nt.links.new(tc.outputs['Object'],micro.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00012;nt.links.new(micro.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
    # Tone-on-tone woven diamond pattern in real object space; no baked suit shadows.
    mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs['Scale'].default_value=1;nt.links.new(tc.outputs['Object'],mapping.inputs[0])
    waves=[]
    for sign in [-1,1]:
        mp=nt.nodes.new('ShaderNodeMapping');mp.inputs['Rotation'].default_value[1]=sign*pi/4;nt.links.new(mapping.outputs['Vector'],mp.inputs['Vector'])
        w=nt.nodes.new('ShaderNodeTexWave');w.wave_type='BANDS';w.bands_direction='X';w.inputs['Scale'].default_value=105;w.inputs['Distortion'].default_value=1.2;nt.links.new(mp.outputs[0],w.inputs['Vector']);waves.append(w)
    mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';nt.links.new(waves[0].outputs['Fac'],mul.inputs[0]);nt.links.new(waves[1].outputs['Fac'],mul.inputs[1])
    col=nt.nodes.new('ShaderNodeMixRGB');col.blend_type='MIX';col.inputs[1].default_value=(*color,1);col.inputs[2].default_value=(*(v*1.32 for v in color),1);nt.links.new(mul.outputs[0],col.inputs[0]);nt.links.new(col.outputs[0],p.inputs['Base Color'])
    return m
wine=textile('Atelier oxblood woven jacquard',(.070,.007,.014))
dark=textile('Atelier black silk vest',(.008,.009,.012))
leather=mat('Atelier oxblood matte leather',(.067,.006,.012),.48)
nt=leather.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Specular IOR Level'].default_value=.3
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=900;noise.inputs['Detail'].default_value=2
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.0002;nt.links.new(noise.outputs[0],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
silver=mat('Atelier smoked silver',(.23,.20,.17),.34,.83)
stitch=mat('Atelier red sewn thread',(.15,.023,.032),.68)

suit=bpy.data.objects['Fitted CC0 male_elegantsuit01'];suit.data.materials.clear();suit.data.materials.append(wine)
for p in suit.data.polygons:p.material_index=0;p.use_smooth=True
for m in suit.modifiers:
    if m.type=='SUBSURF':m.levels=2;m.render_levels=2
# Real elbow compression folds: displaced geometry, not painted lighting.
bpy.ops.object.select_all(action='DESELECT');suit.select_set(True);bpy.context.view_layer.objects.active=suit
for m in list(suit.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
suit.data.update()
for v in suit.data.vertices:
    x,y,z=v.co
    if abs(x)>.235 and 1.08<z<1.40:
        mask=math.exp(-((z-1.24)/.062)**2)
        angle=math.atan2(y,x-math.copysign(.30,x))
        crease=.0035*sin((z-1.14)*116+angle*1.4)*mask
        v.co+=v.normal*crease
suit.data.update()

# Clear the old uniform trim and skirt. The body, face and licensed suit are retained.
for group in ['03_OuterRobe','06_Regalia']:
    for o in list(COL[group].objects):
        n=o.name.lower()
        if any(s in n for s in ['chest embroidery','shoulder inset','shoulder small','skirt','stitched motif','hip chain','waist strap','belt buckle']):bpy.data.objects.remove(o,do_unlink=True)

# Replace the deep empty chest with a fitted, shallow V black performance vest.
chest=bpy.data.objects['Exposed chest at open neckline'];vest=chest.copy();vest.data=chest.data.copy();vest.name='Black performance vest front';COL['02_Innerwear'].objects.link(vest)
vest.data.materials.clear();vest.data.materials.append(dark)
bm=bmesh.new();bm.from_mesh(vest.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_center_median().z>1.447+abs(f.calc_center_median().x)*.58],context='FACES');bm.to_mesh(vest.data);bm.free()
for v in vest.data.vertices:v.co.y-=.003
for p in vest.data.polygons:p.material_index=0
for o in list(COL['02_Innerwear'].objects):
    if 'placket' in o.name.lower() or 'shirt gunmetal button' in o.name.lower():bpy.data.objects.remove(o,do_unlink=True)
for o in COL['02_Innerwear'].objects:
    if o.type=='MESH' and 'Tailored trouser' in o.name:
        for v in o.data.vertices:
            blend=max(0,min(1,(v.co.z-.65)/.35));v.co.x*=1-.15*blend
inner=bpy.data.objects.get('Anatomically fitted open black shirt')
if inner:
    bm=bmesh.new();bm.from_mesh(inner.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.calc_center_median().x)>.043 or f.calc_center_median().y>-.04],context='FACES');bm.to_mesh(inner.data);bm.free()

# Join the duplicated chest patch to the head/neck surface and weld its original
# shared vertices. This removes the z-fighting seam visible at the collarbone.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);chest.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015)
bm.verts.index_update();seen=set();duplicate=[]
for f in bm.faces:
    key=tuple(sorted(v.index for v in f.verts))
    if key in seen:duplicate.append(f)
    else:seen.add(key)
if duplicate:bmesh.ops.delete(bm,geom=duplicate,context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()

def skirt(u,v):
    a=.50+.20*u+(2*pi-2*(.50+.20*u))*v
    folds=(.010*sin(a*11+.8*u)+.005*sin(a*19-3*u))*u**1.25
    radius=.169+.145*u**1.7+folds
    return Vector((radius*sin(a),-(.136+.070*u+folds)*cos(a)+.064*u*u,1.088-.967*u+.018*u**4*sin(a*3)))
sk=surface('Atelier long coat tailored gores',skirt,100,129,wine,'03_OuterRobe',1,.002)
for vv in [0,.13,.29,.50,.71,.87,1]:
    curve('Long coat tailored seam',[skirt(j/110,vv) for j in range(111)],.00065,stitch,'03_OuterRobe')
for edge in [0,1]:
    surface('Wide leather facing',lambda u,v,edge=edge:skirt(u,.065*v if edge==0 else 1-.065*v)+Vector((0,-.0012,0)),100,11,leather,'03_OuterRobe',1,.001)

# Low-profile belt is fitted to the new coat waist; discrete hardware, no floating rings.
belt=surface('Atelier fitted waist belt',lambda u,v:Vector((.177*sin(2*pi*v),-.148*cos(2*pi*v)-.006,1.070+.032*u)),4,100,dark,'06_Regalia',1,.003)
curve('Atelier belt buckle',[(-.024,-.162,1.069),(.024,-.162,1.069),(.024,-.162,1.104),(-.024,-.162,1.104),(-.024,-.162,1.069)],.002,silver,'06_Regalia')
for row in range(2):
    guide=[(.037,-.162,1.089),(.075,-.17,.983-row*.040),(.160,-.11,.963-row*.025),(.175,.0,1.085)]
    for j in range(65):
        p=bez(guide,j/64);curve('New waist chain link',[(p.x+.002*cos(a),p.y+.0012*sin(a),p.z+.0028*sin(a)) for a in [2*pi*k/10 for k in range(11)]],.00048,silver,'06_Regalia')

bpy.context.view_layer.update();jbvh=BVHTree.FromObject(suit,bpy.context.evaluated_depsgraph_get())
# Layered leather shoulder appliques, draped down the sleeve instead of metal spikes.
random.seed(1002)
for side in [-1,1]:
    for row in range(4):
        for col in range(5 if side<0 else 3):
            x=side*(.163+row*.031);y=-.084+col*.040
            hit,normal,_,_=jbvh.ray_cast(Vector((x,y,1.85)),Vector((0,0,-1)),.45)
            if hit is None:continue
            root=hit+Vector((0,0,.003+row*.0008));length=.075+random.random()*.025
            guide=[root,root+Vector((side*.031,0,.012)),root+Vector((side*.061,.005,-length*.45)),root+Vector((side*.065,.008,-length))]
            width=.014+random.random()*.004
            def tab(u,v,guide=guide,width=width,row=row):
                c=bez(guide,u);w=width*(.60+.4*sin(pi*u))*max(.03,(1-u)**.35)
                p=c+Vector((0,(2*v-1)*w,0));hit,normal,_,_=jbvh.find_nearest(p)
                return hit+normal*(.002+row*.0007+.0015*sin(pi*v)*sin(pi*u)) if hit is not None else p
            surface('Layered shoulder leather applique',tab,21,9,leather,'06_Regalia',1,.0012)
            for edge in [.10,.90]:curve('Applique fine stitching',[tab(j/30,edge) for j in range(31)],.00038,stitch,'06_Regalia')

def coat_front(x,z,depth=.0015):
    p,n,_,_=jbvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),.7)
    return p+n*depth if p is not None else None

# One side carries original fine metalwork; the other remains quieter. Branches
# and fastening pins conform to the actual garment rather than hovering in front.
for side in [-1,1]:
    stem=[]
    for j in range(110):
        f=j/109;x=side*(.094+.021*sin(f*8));z=1.185+.29*f;p=coat_front(x,z)
        if p is not None:stem.append(p)
    curve('Lapel sculpted metal vine',stem,.00065,silver,'06_Regalia')
    for leaf in range(6 if side<0 else 4):
        f=.10+leaf*.135;x=side*(.094+.021*sin(f*8));z=1.185+.29*f
        sign=1 if leaf%2 else -1;pts=[]
        for j in range(45):
            t0=j/44;xx=x+side*(.024*sin(pi*t0)+sign*.008*sin(2*pi*t0));zz=z+.022*sin(pi*t0)-.009*sin(2*pi*t0)
            p=coat_front(xx,zz,.002)
            if p is not None:pts.append(p)
        if len(pts)>5:curve('Fine fitted metal leaf',pts,.00052,silver,'06_Regalia')

# Trace the real boundary of the open lapel for a sewn edge and piping.
bm=bmesh.new();bm.from_mesh(suit.data);verts={}
for edge in bm.edges:
    if not edge.is_boundary:continue
    a,b=edge.verts;ca,cb=a.co,b.co
    if not all(c.y<.01 and 1.14<c.z<1.565 and abs(c.x)<.16 for c in [ca,cb]):continue
    verts.setdefault(a.index,[]).append(b.index);verts.setdefault(b.index,[]).append(a.index)
bm.verts.ensure_lookup_table();seen=set()
for root in verts:
    if root in seen:continue
    chain=[];current=root;previous=None
    while current not in seen:
        seen.add(current);chain.append(bm.verts[current].co.copy()+Vector((0,-.0012,0)))
        options=[i for i in verts[current] if i!=previous and i not in seen]
        if not options:break
        previous,current=current,options[0]
    if len(chain)>4:curve('Lapel actual boundary piping',chain,.0010,leather,'03_OuterRobe')
bm.free()

# Skin response is preserved, with reduced broad specular glare.
skin=bpy.data.materials.get('Porcelain warm skin')
if skin:
    p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.48;p.inputs['Specular IOR Level'].default_value=.30

# Packed model and fast neutral checks. An independent scene handles display poses.
scene.cycles.samples=32 if DRAFT else 128;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=16
cam=scene.camera;cam.data.type='ORTHO'
shots=[('01_Full',(2.7,-7,2.8),(0,0,1.02),2.22,(1000,1400)),('02_Portrait',(.7,-4,1.9),(0,-.025,1.72),.56,(1000,1200)),('03_Back',(-2,5,2.5),(0,0,1.03),2.22,(1000,1400))]
for name,loc,target,scale,res in shots:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.resolution_percentage=100;scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
(OUT/'atelier_manifest.json').write_text(json.dumps({'source':'concert14','version':VERSION,'groom':'64000 native Blender hair curves, original procedural comb','wardrobe':'CC0 fitted suit plus original textile shaders, long coat panels, shoulder appliques','pose':'rest stance','status':'iterative actual model, inspect images before use'},ensure_ascii=False,indent=2),encoding='utf-8')
print('ATELIER_SAVED',str(OUT),flush=True)
