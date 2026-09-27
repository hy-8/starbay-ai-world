"""Ember Regent — editable static costume study. Run using background Blender 4.5.
Original costume meshes over a CC0 MakeHuman body. No rig/cloth simulation implied.
Always writes a new version directory; refuses to overwrite an existing blend.
"""
import bpy, math, json, random, sys, hashlib, re
from mathutils import Vector
from pathlib import Path
from math import sin, cos, pi

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
VERSION = args[0] if args else 'v01'
if not re.fullmatch(r'[A-Za-z0-9_-]+', VERSION):
    raise ValueError('Version must be a single directory name containing letters, digits, _ or -.')
for source in json.loads((ROOT/'Source/sources.json').read_text(encoding='utf-8-sig')):
    if hashlib.sha256((ROOT/'Source'/source['file']).read_bytes()).hexdigest()!=source['sha256']:
        raise RuntimeError('Source checksum mismatch: '+source['file'])
OUT = ROOT / 'Exports' / VERSION
if not bpy.app.background:
    raise RuntimeError('Use a separate background Blender process.')
if (OUT / 'Ember_Regent.blend').exists():
    raise RuntimeError('Existing model is protected. Supply a new version name.')
OUT.mkdir(parents=True, exist_ok=True)
RENDER = ROOT / 'Renders' / VERSION
RENDER.mkdir(parents=True, exist_ok=True)
random.seed(27)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
COL = {}
for name in ['01_Body','02_Innerwear','03_OuterRobe','04_Mantle','05_Hair','06_Regalia','07_Staff','90_Stage']:
    COL[name] = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(COL[name])

def assign(o, group):
    for c in list(o.users_collection): c.objects.unlink(o)
    COL[group].objects.link(o)
    return o

def material(name, color, metallic=0, rough=.4, emission=0, fabric=False):
    m = bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    nt=m.node_tree; p=nt.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    if fabric:
        p.inputs['Sheen Weight'].default_value=.3
        tex=nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=240
        tex.inputs['Detail'].default_value=2
        bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16; bump.inputs['Distance'].default_value=.00065
        nt.links.new(tex.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
skin=material('Porcelain warm skin',(.53,.32,.23),0,.48)
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.08
lip=material('Muted lips',(.29,.075,.065),0,.47)
gold=material('Brushed champagne gold',(.64,.37,.12),.78,.26)
darkgold=material('Antique gold recess',(.22,.09,.022),.75,.34)
red=material('Garnet woven silk',(.16,.004,.009),0,.55,fabric=True)
red2=material('Vermilion silk lining',(.23,.011,.004),0,.53,fabric=True)
black=material('Obsidian brocade',(.013,.008,.012),.10,.34,fabric=True)
ivory=material('Warm ivory silk',(.64,.56,.40),.06,.33,fabric=True)
hair=material('Pearl white hair',(.73,.72,.68),.18,.28)
hairshadow=material('Silver hair shadows',(.47,.48,.49),.15,.4)
brow=material('Warm charcoal eyebrow',(.11,.065,.048),0,.62)
glow=material('Molten amber inlay',(.95,.18,.013),.22,.25,2.0)
gem=material('Garnet cabochon',(.30,.009,.003),.55,.18)
eye=material('Eye sclera',(.69,.63,.52),0,.19)
iris=material('Amber iris',(.17,.065,.013),.15,.28)
pupil=material('Pupil',(.002,.001,.001),0,.17)

def mesh(name,verts,faces,mat,group,sub=0,solid=0):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); COL[group].objects.link(o)
    o.data.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    if sub:
        mod=o.modifiers.new('Tailored surface','SUBSURF');mod.levels=sub;mod.render_levels=sub
    if solid:
        mod=o.modifiers.new('Real fabric thickness','SOLIDIFY');mod.thickness=solid;mod.offset=0
    return o

def curve(name,pts,r,mat,group='06_Regalia',closed=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(name,cu);COL[group].objects.link(o);cu.materials.append(mat);return o

def uv(name,loc,scale,mat,group='06_Regalia',seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=16,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;assign(o,group);o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def linepoints(a,b,n=20):return [Vector(a).lerp(Vector(b),i/(n-1)) for i in range(n)]
def bez(points,n=40):
    a,b,c,d=map(Vector,points)
    return [(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d for t in [i/(n-1) for i in range(n)]]

def tube(name,centers,widths,depths,mat,group,n=40,fold=0):
    v=[];f=[]
    for j,c in enumerate(centers):
        c=Vector(c);t=Vector(centers[min(j+1,len(centers)-1)])-Vector(centers[max(0,j-1)])
        t.normalize();u=t.cross(Vector((0,1,0))).normalized();w=t.cross(u).normalized()
        for k in range(n):
            a=2*pi*k/n; mod=1+fold*cos(a*10+j*.3)
            v.append(c+u*(cos(a)*widths[j]*mod)+w*(sin(a)*depths[j]*mod))
    for j in range(len(centers)-1):
        for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    return mesh(name,v,f,mat,group,1,.003)

# CC0 base with licensed male macro target; retain body topology and original face UVs.
src=[];tex=[];faces=[];uvfaces=[];group=''
for line in (ROOT/'Source/base.obj').read_text().splitlines():
    p=line.split()
    if not p:continue
    if p[0]=='v':src.append(Vector(tuple(map(float,p[1:4]))))
    elif p[0]=='vt':tex.append(tuple(map(float,p[1:3])))
    elif p[0]=='g':group=p[1]
    elif p[0]=='f' and group=='body':
        faces.append([int(x.split('/')[0])-1 for x in p[1:]])
        uvfaces.append([int(x.split('/')[1])-1 for x in p[1:]])
for line in (ROOT/'Source/male_young.target').read_text().splitlines():
    p=line.split()
    if len(p)==4 and p[0].isdigit():src[int(p[0])]+=Vector(tuple(map(float,p[1:])))

def world(v):return Vector((v.x*.115,-v.z*.115,(v.y+8.188)*.115))
def arm_pose(v):
    v=Vector(v); s=1 if v.x>=0 else -1
    if .80<v.z<1.59:
        weight=max(0,min(1,(abs(v.x)-.167)/.08))
        angle=-s*math.radians(18)*weight
        x=v.x-s*.203;z=v.z-1.478
        v.x=s*.203+cos(angle)*x-sin(angle)*z
        v.z=1.478+sin(angle)*x+cos(angle)*z
    return v
verts=[arm_pose(world(v)) for v in src]
used=sorted(set(i for f in faces for i in f));remap={old:new for new,old in enumerate(used)}
body=mesh('CC0 male body • retained topology',[verts[i] for i in used],[[remap[i] for i in f] for f in faces],skin,'01_Body',1)
layer=body.data.uv_layers.new(name='MakeHumanUV')
for poly,uvf in zip(body.data.polygons,uvfaces):
    for li,ti in zip(poly.loop_indices,uvf):layer.data[li].uv=tex[ti]
# Covered body faces are not exported/rendered; keep the complete original hidden as an editable source.
full=body.copy();full.data=body.data.copy();COL['01_Body'].objects.link(full);full.name='SOURCE • full body (hidden)';full.hide_render=True;full.hide_set(True)
# Hide covered trunk and legs using material-transparent geometry removal on the visible copy.
import bmesh
bm=bmesh.new();bm.from_mesh(body.data)
remove=[]
for f in bm.faces:
    c=f.calc_center_median()
    if (c.z<1.04 and abs(c.x)<.28) or (c.z<1.475 and abs(c.x)<.225):remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(body.data);bm.free()
colors=body.data.color_attributes.new(name='SubtleSkinTint',type='FLOAT_COLOR',domain='POINT')
for v in body.data.vertices:
    x,y,z=v.co
    amount=math.exp(-((x/.026)**4+((z-1.669)/.006)**4))*max(0,min(1,(-y-.158)/.010))
    base=Vector((.53,.32,.23)).lerp(Vector((.42,.16,.13)),amount*.65)
    colors.data[v.index].color=(*base,1)
attr=skin.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='SubtleSkinTint'
skin.node_tree.links.new(attr.outputs['Color'],skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Eyes, brows, restrained lips; no painted illustration masquerading as geometry.
for s in [-1,1]:
    uv('Eye globe', (s*.03387,-.1358,1.749),(.019,.0125,.0105),eye,'01_Body')
    uv('Amber iris',(s*.03387,-.1475,1.749),(.0066,.0014,.0066),iris,'01_Body')
    uv('Round pupil',(s*.03387,-.149,1.749),(.0028,.0008,.0038),pupil,'01_Body')
    pts=bez([(s*.014,-.169,1.772),(s*.026,-.171,1.779),(s*.044,-.164,1.778),(s*.058,-.150,1.773)],25)
    curve('Arched brow',pts,.0017,brow,'01_Body')

# Inner tunic: tailored continuous torso shell.
rings=[(1.075,.164,.131,-.018),(1.15,.158,.132,-.021),(1.29,.177,.147,-.019),(1.41,.204,.157,-.015),(1.49,.204,.14,.006),(1.555,.078,.071,-.008)]
v=[];f=[];n=64
for j,(z,rx,ry,cy) in enumerate(rings):
    for k in range(n):
        a=2*pi*k/n; zz=z
        if j==len(rings)-1:zz-=.075*max(0,cos(a))**4
        v.append((rx*sin(a),cy-ry*cos(a),zz))
for j in range(len(rings)-1):
    for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
mesh('Ivory fitted under-robe',v,f,ivory,'02_Innerwear',2,.004)
for s in [-1,1]:
    pts=bez([(s*.123,-.139,1.43),(s*.085,-.170,1.38),(s*.050,-.171,1.32),(s*.004,-.165,1.30)])
    curve('Fine solar necklace',pts,.0025,gold,'02_Innerwear')
    centers=[(s*.112,-.005,1.10),(s*.128,-.005,.95),(s*.148,.012,.72),(s*.174,.013,.46),(s*.200,.001,.16)]
    tube('Pleated wide trousers',centers,[.072,.083,.087,.087,.072],[.090,.099,.093,.084,.08],black,'02_Innerwear',48,.065)
    uv('Soft leather boot',(s*.206,-.066,.074),(.077,.151,.075),black,'02_Innerwear')
    curve('Boot toe gold seam',[(s*.206+.067*cos(a),-.066+.134*sin(a),.090) for a in [pi+pi*k/32 for k in range(33)]],.004,gold,'02_Innerwear')

# Open coat: a continuous swept shell, shaped lapels and repeating custom embroidery.
spec=[(.12,.405,.235,.40),(.25,.374,.218,.35),(.55,.32,.202,.31),(.82,.270,.181,.32),(1.05,.227,.16,.34),(1.17,.202,.160,.40),(1.32,.205,.168,.54),(1.44,.231,.17,.72),(1.51,.216,.125,.91)]
def coat(j,t,extra=0):
    z,rx,ry,gap=spec[j];a=gap+(2*pi-2*gap)*t
    fold=.009*(1.2-z)*cos(a*13+z*4)
    return Vector(((rx+fold+extra)*sin(a),-(ry+fold+extra)*cos(a),z))
v=[];f=[];n=97
for j in range(len(spec)):
    for k in range(n):v.append(coat(j,k/(n-1)))
for j in range(len(spec)-1):
    for k in range(n-1):f.append((j*n+k,j*n+k+1,(j+1)*n+k+1,(j+1)*n+k))
robe=mesh('Split garnet ceremonial overcoat',v,f,red,'03_OuterRobe',2,.007)
for t in [0,1]:
    curve('Heavy embroidered lapel',[coat(j,t,.006) for j in range(len(spec))],.010,gold,'03_OuterRobe')
for j in [0,1]:curve('Double hem braid',[coat(j,k/160,.007) for k in range(161)],.0045,gold,'03_OuterRobe')
for side in [0,1]:
    for j in range(1,7):
        # Flame-leaf scrolls along the opening, separately editable geometry.
        p=coat(j,.022 if side==0 else .978,.014);s=1 if side==0 else -1
        pts=bez([p,p+Vector((s*.040,-.022,.055)),p+Vector((s*.086,-.007,.04)),p+Vector((s*.053,-.017,.100))])
        curve('Lapel flame scroll',pts,.0025,gold,'03_OuterRobe')
        uv('Embroidered garnet bead',p,(.008,.005,.01),gem,'03_OuterRobe',16)

# Broad split sleeves follow relaxed arm pose; gold cuffs and layered pauldrons.
for s in [-1,1]:
    points=[arm_pose(Vector((s*x,y,z))) for x,y,z in [(.202,0,1.478),(.255,-.005,1.405),(.335,-.015,1.288),(.414,-.104,1.207),(.451,-.172,1.164)]]
    sleeve=tube('Bell sleeve '+str(s),points,[.098,.105,.108,.126,.139],[.1,.111,.12,.129,.131],red,'03_OuterRobe',48,.055)
    c=points[-1];t=(points[-1]-points[-2]).normalized();u=t.cross(Vector((0,1,0))).normalized();w=t.cross(u)
    for offset in [0,.018]:
        curve('Cuff embroidery',[c-t*offset+u*(cos(a)*.14)+w*(sin(a)*.134) for a in [2*pi*k/64 for k in range(65)]],.006,gold,'03_OuterRobe')
    # overlapping petal armor makes a pronounced noble shoulder silhouette
    for k in range(3):
        x=s*(.195+.04*k);z=1.526-.020*k
        vv=[];ff=[]
        for j in range(17):
            t=j/16;xx=x+s*(t-.3)*.095;half=.115*sin(pi*t)**.55+.001
            for q in [-1,-.5,0,.5,1]:vv.append((xx,half*q,z+.030*(1-q*q)*sin(pi*t)-.025*t))
        for j in range(16):
            for kk in range(4):ff.append((j*5+kk,j*5+kk+1,(j+1)*5+kk+1,(j+1)*5+kk))
        mesh('Pointed overlapping shoulder plate',vv,ff,gold,'06_Regalia',1,.005)
        curve('Shoulder ruby engraving',[(vv[j*5+2][0],0,vv[j*5+2][2]+.005) for j in range(2,15)],.006,gem)

# Belt, solar clasp, hanging tassels and articulated front stole.
curve('Structured waist belt',[(.224*sin(a),-.164*cos(a),1.098) for a in [2*pi*k/100 for k in range(101)]],.020,black,'06_Regalia')
for z in [1.078,1.116]:curve('Belt gold piping',[(.227*sin(a),-.168*cos(a),z) for a in [2*pi*k/100 for k in range(101)]],.004,gold)
uv('Necklace sun pendant',(0,-.174,1.293),(.016,.006,.024),gold)
uv('Pendant ember inset',(0,-.182,1.293),(.008,.003,.014),gem)
uv('Solar belt clasp',(0,-.161,1.099),(.049,.018,.047),gold)
uv('Solar clasp garnet',(0,-.181,1.100),(.028,.011,.032),gem)
for s in [-1,1]:
    for k in range(3):
        pts=bez([(s*(.035+k*.03),-.17,1.075),(s*(.08+k*.03),-.18,.98),(s*(.09+k*.033),-.19,.87),(s*(.09+k*.033),-.20,.82-k*.032)])
        curve('Belt articulated chain',pts,.0025,gold)
        uv('Pendant obsidian drop',pts[-1],(.008,.007,.027),gem)
    v=[];f=[]
    for j in range(25):
        t=j/24;z=1.07-.91*t;x=s*(.045+.085*t+.017*sin(t*pi*2));y=-.177-.034*t
        for k in range(9):
            q=(k/8-.5);v.append((x+q*.085*(1-.2*t),y+.012*cos(q*pi*4),z+.025*cos(q*pi)))
    for j in range(24):
        for k in range(8):f.append((j*9+k,j*9+k+1,(j+1)*9+k+1,(j+1)*9+k))
    mesh('Long ivory front stole',v,f,ivory,'02_Innerwear',1,.003)
    for edge in [0,8]:curve('Stole border',[Vector(v[j*9+edge])+Vector((0,-.004,0)) for j in range(25)],.004,gold,'02_Innerwear')

# Seven individually cut flame-feather cape panels, sculpted into a display drape.
# Backs sweep rearward; no animation or real-time cloth is claimed.
for idx in range(7):
    a=(idx-3)/3
    start=Vector((a*.20,.098,1.48-abs(a)*.026))
    end=Vector((a*(.68+.08*abs(a)),.48+.21*(1-abs(a)),.11+.16*abs(a)))
    centers=bez([start,Vector((a*.34,.26,1.33)),Vector((a*.73,.65,.74)),end],45)
    v=[];f=[];nr=13
    for j,c in enumerate(centers):
        t=j/(len(centers)-1);width=(.067+.107*sin(pi*t)**.8)*(1-.87*t**9)
        for k in range(nr):
            q=k/(nr-1)*2-1
            v.append(c+Vector((q*width,.034*sin(pi*t)*cos(q*pi*2)+.018*q*q,.045*q*q*sin(pi*t)+.020*sin(t*pi*3+idx)*q)))
    for j in range(len(centers)-1):
        for k in range(nr-1):f.append((j*nr+k,j*nr+k+1,(j+1)*nr+k+1,(j+1)*nr+k))
    mesh('Flame mantle panel %02d'%idx,v,f,red if idx%2 else red2,'04_Mantle',1,.004)
    for edge in [0,nr-1]:curve('Cape metallic cut edge',[Vector(v[j*nr+edge])+Vector((0,.004,0)) for j in range(len(centers))],.004,gold,'04_Mantle')
    curve('Molten feather spine',[p+Vector((0,.018,0)) for p in centers],.0028,glow,'04_Mantle')
    def cape_surface(t,q):
        jf=t*44;j0=min(43,int(jf));c=centers[j0].lerp(centers[j0+1],jf-j0)
        width=(.067+.107*sin(pi*t)**.8)*(1-.87*t**9)
        return c+Vector((q*width,.034*sin(pi*t)*cos(q*pi*2)+.018*q*q+.006,.045*q*q*sin(pi*t)+.020*sin(t*pi*3+idx)*q))
    for j in range(9,39,5):
        t=j/44
        for s in [-1,1]:
            pts=[cape_surface(t-.090*u,s*.82*sin(u*pi/2)) for u in [k/24 for k in range(25)]]
            curve('Mantle fern embroidery',pts,.0022,gold,'04_Mantle')

# Swept, tapered ribbon-volume hair. Scalp patch covers the cranial shell.
v=[];f=[];n=72;m=18
for j in range(m):
    for k in range(n):
        a=2*pi*k/n;ph=.03+(1.80-.50*max(0,cos(a)))*j/(m-1)
        v.append((.102*sin(ph)*sin(a),-.042-.122*sin(ph)*cos(a),1.775+.115*cos(ph)))
for j in range(m-1):
    for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
mesh('Parted pearl hair cap',v,f,hair,'05_Hair',1,.003)
def lock(name,controls,width,depth=.008):
    cs=bez(controls,34);v=[];f=[];n=8
    for j,c in enumerate(cs):
        t=j/(len(cs)-1);w=width*(.055+.95*sin(pi*t)**.6)*(1-t)**.3+.00015
        tangent=(cs[min(j+1,len(cs)-1)]-cs[max(0,j-1)]).normalized()
        across=tangent.cross(Vector((0,1,0))).normalized();normal=tangent.cross(across).normalized()
        for k in range(n):
            a=2*pi*k/n;v.append(c+across*(w*cos(a))+normal*(depth*sin(a)*sin(pi*t)**.5))
    for j in range(len(cs)-1):
        for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    mesh(name,v,f,hair,'05_Hair',1)
    for strand in [-.45,.45]:
        pts=[]
        for j,p in enumerate(cs):
            t=j/(len(cs)-1);tangent=(cs[min(j+1,len(cs)-1)]-cs[max(0,j-1)]).normalized();across=tangent.cross(Vector((0,1,0))).normalized()
            pts.append(p+across*(strand*width*sin(pi*t)**.6)+Vector((0,-depth*.75*sin(pi*t)**.5,0)))
        curve('Individual silver groove',pts,.00035,hairshadow,'05_Hair')
for s in [-1,1]:
    # Forehead swept away from eyes, long face framing locks.
    for k in range(5):
        lock('Swept temple lock',[(s*(.005+k*.008),-.077,1.883-k*.002),(s*(.058+k*.014),-.155,1.89-k*.013),(s*(.060+k*.018),-.193,1.735),(s*(.108+k*.010),-.077,1.671-k*.035)],.023-k*.001)
    for k in range(7):
        lock('Long shoulder wave',[(s*(.042+k*.005),-.008+k*.009,1.871-k*.005),(s*(.123+k*.009),-.014+k*.014,1.741),(s*(.094+k*.017),-.13+k*.022,1.477),(s*(.20+k*.012),.06+k*.017,1.340-k*.025)],.023)
    for k in range(3):
        lock('Chest-length framing wave',[(s*(.073+k*.007),-.079,1.829),(s*(.17+k*.006),-.159,1.66),(s*(.067+k*.022),-.20,1.53),(s*(.127+k*.015),-.161,1.365-k*.025)],.014,.006)
for k in range(15):
    x=(k-7)*.012
    lock('Back cascading hair',[(x*.65,.023,1.877-abs(x)*.20),(x*1.7,.160,1.76),(x*1.7+.065*sin(k),.23,1.40),(x*2.2+.048*sin(k*2),.22,1.17+.06*cos(k))],.025,.009)

# Broken solar halo, segmented crown with gemstone finials (new motif).
for start,end in [(15,150),(176,280),(306,342)]:
    pts=[(.154*sin(a),.035,1.84+.154*cos(a)) for a in [math.radians(start+(end-start)*k/60) for k in range(61)]]
    curve('Broken solar crown arc',pts,.009,gold)
    curve('Crown inner ember arc',[(p[0]*.94,p[1]-.004,1.84+(p[2]-1.84)*.94) for p in pts],.0025,glow)
for k in range(9):
    a=math.radians(-72+18*k);base=Vector((.148*sin(a),.035,1.84+.148*cos(a)))
    tip=Vector(((.186+.018*(k%2))*sin(a),.025,1.84+(.186+.018*(k%2))*cos(a)))
    curve('Crown flame ray',[base,base.lerp(tip,.5)+Vector((.007,0,0)),tip],.005,gold)
    uv('Crown ember tip',tip,(.007,.007,.010),gem)
curve('Forehead circlet',[(.098*sin(a),-.043-.113*cos(a),1.817+.011*cos(3*a)) for a in [2*pi*k/100 for k in range(101)]],.004,gold)
uv('Brow sunstone',(0,-.161,1.825),(.012,.008,.019),gem)

# Freestanding ceremonial staff in the display composition, not attached to a hand.
shaft=[(.64,-.06,.08),(.71,-.013,1.79)]
curve('Obsidian staff shaft',linepoints(*shaft),.013,black,'07_Staff')
curve('Staff gold core',linepoints((.646,-.072,.08),(.716,-.025,1.79)),.0035,gold,'07_Staff')
for j in range(12):
    c=Vector(shaft[0]).lerp(Vector(shaft[1]),j/11)
    curve('Staff chased band',[(c.x+.016*cos(a),c.y+.016*sin(a),c.z) for a in [2*pi*k/24 for k in range(25)]],.003,gold,'07_Staff')
center=Vector((.718,-.013,1.91))
for radius in [.083,.111]:curve('Sun staff ring',[(center.x+radius*sin(a),center.y,center.z+radius*cos(a)) for a in [2*pi*k/80 for k in range(81)]],.005,gold,'07_Staff')
uv('Staff molten heart',center,(.041,.023,.057),glow,'07_Staff')
for k in range(10):
    a=2*pi*k/10;p=center+Vector((.108*sin(a),0,.108*cos(a)));q=center+Vector((.152*sin(a+.1),0,.152*cos(a+.1)))
    curve('Staff flame ray',bez([p,p+Vector((.022,0,.015)),q,q+Vector((.009,0,.008))],16),.0038,gold,'07_Staff')

# Gallery stage and lighting, deliberately separate from the exported character.
stage=material('Volcanic basalt',(.018,.023,.031),.32,.39)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.06,depth=.09,location=(0,.15,-.071))
o=bpy.context.object;assign(o,'90_Stage');o.name='Basalt gallery plinth';o.data.materials.append(stage)
be=o.modifiers.new('Machined edge','BEVEL');be.width=.014;be.segments=3
for r in [.92,1.012]:curve('Plinth inlaid ring',[(r*cos(a),.15+r*sin(a),-.022) for a in [2*pi*k/180 for k in range(181)]],.003,gold,'90_Stage')
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.119));o=bpy.context.object;assign(o,'90_Stage');o.data.materials.append(material('Midnight studio',(.008,.013,.023),.1,.48))
def area(name,loc,power,color,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);COL['90_Stage'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large portrait key',(-3,-4,5),480,(1,.83,.66),3,(0,0,1))
area('Cool softbox',(3,-2.5,3),340,(.62,.76,1),2.5,(0,0,1.2))
area('Amber rim',(-1.8,2.5,3.4),620,(1,.39,.12),2,(0,0,1.2))
area('Cape separation',(2,2,2),500,(.70,.82,1),2,(0,.3,1))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40
scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.world.color=(.10,.10,.10)
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.render.film_transparent=False
data=bpy.data.cameras.new('Portrait Camera');camera=bpy.data.objects.new('Portrait Camera',data);COL['90_Stage'].objects.link(camera);scene.camera=camera
def camera_at(loc,target,ortho):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=ortho;data.lens=65
camera_at((3,-7,2.85),(0,.08,1.01),2.66)
scene.render.resolution_x=1400;scene.render.resolution_y=1600
# Export evaluated geometry with physical materials. Procedural weave will not travel in GLB.
bpy.ops.object.select_all(action='DESELECT')
for group,collection in COL.items():
    if group=='90_Stage':continue
    for o in collection.objects:
        if not o.hide_render:o.select_set(True)
bpy.context.view_layer.objects.active=body
# Convert curves only on copies so the blend retains editable splines.
exports=[]
for o in list(bpy.context.selected_objects):
    copy=o.copy();copy.data=o.data.copy();bpy.context.scene.collection.objects.link(copy);exports.append(copy)
bpy.ops.object.select_all(action='DESELECT')
for o in exports:o.select_set(True)
bpy.context.view_layer.objects.active=exports[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(OUT/'Ember_Regent_Static.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.ops.export_scene.fbx(filepath=str(OUT/'Ember_Regent_Static.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y')
report={'version':VERSION,'status':'static modeled costume study; no rig, skin weights, cloth physics or UE import','units':'meters','selected_meshes':len(exports),'vertices':sum(len(o.data.vertices) for o in exports),'polygons':sum(len(o.data.polygons) for o in exports)}
for o in exports:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True);bpy.context.view_layer.objects.active=body
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
for name,loc,target,scale,res in [
    ('01_Hero',(3,-7,2.85),(0,.08,1.01),2.66,(1400,1600)),
    ('02_Front',(0,-7,2.12),(0,.05,1.03),2.45,(1400,1600)),
    ('03_Back',(-3,7,2.75),(0,.10,1.03),2.55,(1400,1600)),
    ('04_Portrait',(.85,-4,2.08),(0,-.012,1.68),.79,(1400,1400))]:
    camera_at(loc,target,scale);scene.render.resolution_x=res[0];scene.render.resolution_y=res[1]
    scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
camera_at((3,-7,2.85),(0,.08,1.01),2.66);scene.render.resolution_x=1400;scene.render.resolution_y=1600
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
report['files']={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.suffix in ['.blend','.glb','.fbx']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('EMBER_REGENT_COMPLETE',json.dumps(report,ensure_ascii=False))
