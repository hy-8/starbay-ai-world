"""Couture refinement: actual fibers, tailored panels, raised filigree, sculpted mantle.
Run in a new background Blender with -- VERSION [--draft]. Keeps the v0.1 script intact.
"""
from pathlib import Path
import sys
_base=Path(__file__).with_name('build_character.py').read_text(encoding='utf-8')
# Reuse initialization and mesh/material helpers, not the first edition costume.
exec(compile(_base.split('# CC0 base')[0],str(Path(__file__).with_name('build_character.py')),'exec'))
DRAFT='--draft' in args
from mathutils import noise

def setp(mat,key,value):mat.node_tree.nodes.get('Principled BSDF').inputs[key].default_value=value
setp(red,'Base Color',(.105,.0025,.002,1));setp(red,'Metallic',0);setp(red,'Roughness',.49);setp(red,'Sheen Weight',.13);setp(red,'Specular IOR Level',.25)
setp(red2,'Base Color',(.19,.005,.001,1));setp(red2,'Roughness',.47);setp(red2,'Specular IOR Level',.25)
setp(gold,'Base Color',(.57,.28,.064,1));setp(gold,'Roughness',.29)
setp(ivory,'Base Color',(.60,.51,.37,1));setp(ivory,'Roughness',.56)
setp(black,'Roughness',.48)
setp(hair,'Metallic',0);setp(hair,'Roughness',.34)
setp(glow,'Emission Strength',5)
bronze=material('Blackened raised gold relief',(.23,.08,.012),.8,.33)
ember=material('Amber hot filament',(1,.17,.005),.15,.26,5)
hot=material('White-hot filament',(1,.53,.13),0,.25,8)
smoke=material('Basalt bronze inset',(.014,.006,.003),.45,.44)
platinum=material('Platinum woven braid',(.55,.47,.36),.75,.32)
hairmats=[material('Ivory fiber '+str(i),c,0,.38) for i,c in enumerate([(.62,.64,.65),(.78,.77,.71),(.40,.44,.48),(.88,.83,.70)])]
for m in hairmats:setp(m,'Anisotropic',.55)

# Generated original textile bitmap is actually mapped onto the 3D costume.
brocade=bpy.data.images.load(str(ROOT/'Materials/Ember_Brocade_Albedo.png'));brocade.pack()
orm=bpy.data.images.load(str(ROOT/'Materials/Ember_Brocade_ORM.png'));orm.colorspace_settings.name='Non-Color';orm.pack()
normalmap=bpy.data.images.load(str(ROOT/'Materials/Ember_Brocade_Normal.png'));normalmap.colorspace_settings.name='Non-Color';normalmap.pack()
for material0 in [red,red2]:
    nt=material0.node_tree;p=nt.nodes.get('Principled BSDF');img=nt.nodes.new('ShaderNodeTexImage');img.image=brocade;img.extension='REPEAT'
    nt.links.new(img.outputs['Color'],p.inputs['Base Color'])
    pack=nt.nodes.new('ShaderNodeTexImage');pack.image=orm;sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(pack.outputs[0],sep.inputs[0])
    nt.links.new(sep.outputs['Blue'],p.inputs['Metallic']);nt.links.new(sep.outputs['Green'],p.inputs['Roughness'])
    nm=nt.nodes.new('ShaderNodeTexImage');nm.image=normalmap;n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs[0],n.inputs['Color']);nt.links.new(n.outputs[0],p.inputs['Normal'])

# Mesh foundation from the same declared CC0 sources, with independently licensed morphs.
exec(compile('# CC0 base'+_base.split('# CC0 base')[1].split('# Covered body faces')[0],'<body-foundation>','exec'))
morphs=json.loads((ROOT/'Source/couture_sources.json').read_text(encoding='utf-8'))
for record in morphs:
    path=ROOT/'Source'/record['file'];data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=record['sha256']:raise RuntimeError('Morph source mismatch')
    for line in data.decode().splitlines():
        p=line.split()
        if len(p)==4 and p[0].isdigit():
            i=int(p[0])
            if i in remap:
                dx,dy,dz=map(float,p[1:]);body.data.vertices[remap[i]].co+=Vector((dx,-dz,dy))*(.115*record['weight'])
# Subtle V jaw and bridge refinement, not a change to source files.
for v in body.data.vertices:
    x,y,z=v.co
    if z>1.60:
        jaw=math.exp(-((z-1.659)/.051)**2)*max(0,min(1,(-y+.04)/.10))
        v.co.x*=1-.09*jaw
body.modifiers[0].levels=2;body.modifiers[0].render_levels=2
full=body.copy();full.data=body.data.copy();COL['01_Body'].objects.link(full);full.name='SOURCE full CC0 body';full.hide_render=True;full.hide_set(True)
import bmesh
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_center_median().z<1.075 and abs(f.calc_center_median().x)<.30],context='FACES')
bm.to_mesh(body.data);bm.free()
body.data.update()
colors=body.data.color_attributes.new(name='SkinAlbedo',type='FLOAT_COLOR',domain='POINT')
for v in body.data.vertices:
    x,y,z=v.co
    lipmask=math.exp(-((x/.027)**4+((z-1.669)/.007)**4))*max(0,min(1,(-y-.151)/.017))
    blush=math.exp(-(((abs(x)-.052)/.025)**2+((z-1.71)/.033)**2))*max(0,min(1,(-y-.075)/.06))
    base=Vector((.64,.41,.30)).lerp(Vector((.54,.28,.22)),blush*.28).lerp(Vector((.40,.12,.098)),lipmask*.82)
    eyelid=math.exp(-(((abs(x)-.035)/.018)**4+((z-1.759)/.006)**2))*max(0,min(1,(-y-.105)/.025))
    base=base.lerp(Vector((.29,.13,.095)),eyelid*.29)
    colors.data[v.index].color=(*base,1)
nodes=skin.node_tree.nodes;links=skin.node_tree.links;p=nodes.get('Principled BSDF')
attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='SkinAlbedo';links.new(attr.outputs['Color'],p.inputs['Base Color'])
p.inputs['Roughness'].default_value=.43;p.inputs['Subsurface Weight'].default_value=.10
p.inputs['Subsurface Radius'].default_value=(1,.45,.23)
p.inputs['Subsurface Scale'].default_value=.006
texskin=nodes.new('ShaderNodeTexNoise');texskin.inputs['Scale'].default_value=460;texskin.inputs['Detail'].default_value=2
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00025
links.new(texskin.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])

def batch_curves(name,paths,r,mat,group,taper=False,res=1):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=res;cu.resolution_u=8
    for path in paths:
        sp=cu.splines.new('POLY');sp.points.add(len(path)-1)
        for j,(p,c) in enumerate(zip(sp.points,path)):
            p.co=(*c,1)
            if taper:p.radius=max(.035,(1-j/(len(path)-1))**.65)
    o=bpy.data.objects.new(name,cu);COL[group].objects.link(o);cu.materials.append(mat);return o

# Detailed inset eyes, limbal rings, tear lines and individually drawn brow fibers.
for s in [-1,1]:
    uv('Sclera',(s*.034,-.139,1.749),(.020,.014,.0124),eye,'01_Body',48)
    uv('Amber iris',(s*.034,-.1525,1.749),(.0072,.0018,.0072),iris,'01_Body',40)
    uv('Pupil',(s*.034,-.1543,1.749),(.0031,.0008,.0038),pupil,'01_Body',32)
    limbal=material('Dark limbal ring '+str(s),(.028,.010,.005),0,.25)
    curve('Limbal edge',[(s*.034+.0071*cos(a),-.1533,1.749+.0071*sin(a)) for a in [2*pi*k/60 for k in range(61)]],.00055,limbal,'01_Body')
    irislines=[]
    for k in range(80):
        a=k/80*2*pi;r0=.0035+random.random()*.001
        irislines.append([(s*.034+r*cos(a),-.1542,1.749+r*sin(a)) for r in [r0,.0067]])
    batch_curves('Iris radial detail',irislines,.00016,gold,'01_Body',res=0)
    browpath=bez([(s*.012,-.171,1.775),(s*.030,-.174,1.781),(s*.049,-.167,1.782),(s*.064,-.144,1.776)],35)
    browlines=[]
    for j in range(380):
        t=random.random();p=browpath[min(33,int(t*34))]+Vector((0,-random.random()*.001,(random.random()-.5)*.0033))
        browlines.append(bez([p,p+Vector((s*.0015,-.0006,.0015)),p+Vector((s*.002,-.0003,.0022)),p+Vector((s*.004,0,.0015))],7))
    batch_curves('Natural eyebrow fibers',browlines,.00029,brow,'01_Body',True,0)

# Eyelashes follow a raycast onto the actual eyelid surface, rather than floating in space.
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
for s in [-1,1]:
    lashes=[];lid=[]
    for j in range(35):
        t=j/34;x=s*(.014+.041*t);z=1.749+.0060*sin(pi*t)+.0008*t
        hit,normal,_,_=bvh.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)),.4)
        if hit is not None:
            p=hit+Vector((0,-.0005,0));lid.append(p)
            length=.0017+.0022*sin(pi*t)
            lashes.append(bez([p,p+Vector((s*.0003,-length*.5,.0005)),p+Vector((s*.0006,-length,.001)),p+Vector((s*.0012,-length,.0018))],7))
    if lid:curve('Fine upper eyelid definition',lid,.00033,brow,'01_Body')
    batch_curves('Upper eyelashes',lashes,.00017,brow,'01_Body',True,0)

# Smooth interpolation helper for tailored cloth surfaces.
def interp(table,t):
    t=max(0,min(1,t));p=t*(len(table)-1);i=min(int(p),len(table)-2);f=p-i;f=f*f*(3-2*f)
    return [a+(b-a)*f for a,b in zip(table[i],table[i+1])]
def surface(name,fun,nu,nv,mat,group,solid=.003,sub=1):
    vs=[fun(i/(nu-1),j/(nv-1)) for i in range(nu) for j in range(nv)]
    fs=[(i*nv+j,(i+1)*nv+j,(i+1)*nv+j+1,i*nv+j+1) for i in range(nu-1) for j in range(nv-1)]
    ob=mesh(name,vs,fs,mat,group,sub,solid)
    uv=ob.data.uv_layers.new(name='TailorUV')
    ulen=sum((Vector(fun((i+1)/40,.5))-Vector(fun(i/40,.5))).length for i in range(40))/.45
    vlen=sum((Vector(fun(.5,(i+1)/40))-Vector(fun(.5,i/40))).length for i in range(40))/.45
    for poly in ob.data.polygons:
        for li,vi in zip(poly.loop_indices,poly.vertices):uv.data[li].uv=(vi%nv/(nv-1)*vlen,vi//nv/(nu-1)*ulen)
    return ob
def trim(fun,name,mat=gold,r=.0028,group='03_OuterRobe',u0=0,u1=1,v=0):
    return curve(name,[Vector(fun(u0+(u1-u0)*k/100,v))+Vector((0,-.002,0)) for k in range(101)],r,mat,group)

# Ivory wrap shirt with deep V, kept narrow enough to show the underlying chest.
table=[(1.09,.156,.139,.035),(1.24,.157,.152,.12),(1.41,.196,.16,.55),(1.49,.204,.135,.91),(1.551,.078,.075,1.00)]
def shirt(u,v):
    z,rx,ry,gap=interp(table,u);a=gap+(2*pi-2*gap)*v
    return Vector((rx*sin(a),-ry*cos(a)-.009,z+.002*cos(a*15+u*7)))
surface('Ivory silk open wrap',shirt,45,80,ivory,'02_Innerwear',.003,1)
for v in [0,1]:trim(shirt,'Ivory collar rolled edge',platinum,.004,'02_Innerwear',v=v)

# Pants are fitted at the hip and break into small folds above the boot.
for s in [-1,1]:
    pts=[(s*(.115+.082*t),-.010+.008*sin(t*pi),1.10-.95*t) for t in [j/16 for j in range(17)]]
    widths=[.080+.02*sin(j/16*pi)-.015*(j/16)**5 for j in range(17)]
    depths=[.097+.012*sin(j/16*pi*2) for j in range(17)]
    tube('Ivory wide silk trouser',pts,widths,depths,ivory,'02_Innerwear',64,.035)
    uv('Black heeled ceremonial boot',(s*.197,-.067,.073),(.067,.142,.074),black,'02_Innerwear')
    curve('Boot gold welt',[(s*.197+.061*cos(a),-.067+.132*sin(a),.060) for a in [2*pi*k/60 for k in range(61)]],.0023,gold,'02_Innerwear')

# Coat split into separate left/right cut panels: dynamic hem, narrow waist, broad shoulders.
coat_table=[(.11,.385,.22,.27),(.29,.327,.207,.26),(.54,.265,.184,.29),(.81,.215,.162,.30),(1.05,.182,.148,.30),(1.20,.171,.150,.40),(1.38,.211,.164,.72),(1.49,.222,.13,1.00)]
def coat(u,v):
    z,rx,ry,gap=interp(coat_table,u);a=gap+(2*pi-2*gap)*v
    fold=.011*(1-u)*sin(a*14+u*7)+.005*sin(a*23-u*4)*(1-u)**2
    gust=.10*(1-u)**3*sin(a)*sin(a*2+.7)
    return Vector(((rx+fold)*sin(a)+gust,-(ry+fold)*cos(a)+.12*(1-u)**3*sin(a*.5),z+.035*(1-u)**5*(1+sin(a*4))))
surface('Cut garnet silk overcoat',coat,90,135,red,'03_OuterRobe',.005,1)
for v in [0,1]:
    trim(coat,'Gold bound lapel',gold,.005,v=v)
    trim(coat,'Gold lapel parallel braid',platinum,.0015,v=.017 if v==0 else .983)
for u in [.018,.05]:
    curve('Sinuous gold hem braid',[coat(u,k/180)+Vector((0,-.001,0)) for k in range(181)],.0033,gold,'03_OuterRobe')

def floral(fun,us,vs,uwidth,vwidth,group='03_OuterRobe',radius=.0012):
    """Paired curling tendrils and almond leaves fitted on the true cloth surface."""
    paths=[];leaves=[];lv=[];lf=[]
    for u in us:
        for v in vs:
            paths.append([fun(u+(t-.5)*uwidth,v)+Vector((0,-.004,0)) for t in [i/24 for i in range(25)]])
            for s in [-1,1]:
                for row in [-.22,.16]:
                    pts=[]
                    for j in range(45):
                        t=j/44;angle=t*pi*2.15;r=sin(t*pi*.80)
                        uu=u+row*uwidth+.26*uwidth*t+.15*uwidth*r*sin(angle)
                        vv=v+s*vwidth*(.18+.7*t+.28*r*cos(angle))
                        pts.append(fun(uu,vv)+Vector((0,-.004,0)))
                    paths.append(pts)
                    # almond-shaped leaf path
                    leaf=[fun(u+(row+.08+.15*sin(a))*uwidth,v+s*(.72+.08*cos(a)**3)*vwidth)+Vector((0,-.005,0)) for a in [2*pi*k/32 for k in range(32)]]
                    leaves.append(leaf+[leaf[0]])
                    center=fun(u+(row+.08)*uwidth,v+s*.72*vwidth)+Vector((0,-.006,0))
                    offset=len(lv);lv.extend([center]+leaf)
                    for k in range(32):lf.append((offset,offset+1+k,offset+1+(k+1)%32))
    batch_curves('Raised baroque flame scrolls',paths,radius,gold,group,False,1)
    batch_curves('Paired almond leaf engraving',leaves,radius*.8,platinum,group,False,1)
    mesh('Raised gilded acanthus leaves',lv,lf,gold,group,0,0)

floral(coat,[.13,.29,.46,.64,.81],[.04,.96],.18,.029,radius=.0016)
floral(coat,[.17,.39,.62],[.14,.30,.45,.55,.70,.86],.18,.036,radius=.0011)
# An extra fine diamond brocade sits physically on the lower robe.
paths=[]
for j in range(12):
    u=.09+j*.045
    for k in range(18):
        v=.06+k*.05
        paths.append([coat(u+du,v+dv)+Vector((0,-.0018,0)) for du,dv in [(0,-.009),(.013,0),(0,.009),(-.013,0),(0,-.009)]])
batch_curves('Fine gilded cloth repeat',paths,.00055,darkgold,'03_OuterRobe',False,0)

# Sleeves follow relaxed arms with gathered shoulder fabric and gravity folds.
for s in [-1,1]:
    controls=[arm_pose(Vector((s*x,y,z))) for x,y,z in [(.204,0,1.475),(.25,-.005,1.41),(.40,-.08,1.22),(.447,-.177,1.15)]]
    cs=bez(controls,49)
    def sleeve(u,v):
        j=min(47,int(u*48));c=cs[j].lerp(cs[j+1],u*48-j);t=(cs[min(48,j+1)]-cs[max(0,j-1)]).normalized()
        a=2*pi*v;across=t.cross(Vector((0,1,0))).normalized();normal=t.cross(across)
        r=.076+.035*u**1.6;fold=.009*sin(a*9+u*2)*sin(pi*u)+.0035*sin(a*17-u*7)
        return c+across*(cos(a)*(r+fold))+normal*(sin(a)*(r+fold)*1.03)+Vector((0,0,-.020*sin(a)**2*sin(pi*u)))
    surface('Gathered bell sleeve '+str(s),sleeve,49,65,red,'03_OuterRobe',.004,1)
    for u in [.965,.995]:curve('Layered sleeve hem',[sleeve(u,j/100) for j in range(101)],.004,gold,'03_OuterRobe')
    floral(sleeve,[.40,.68,.87],[.12,.37,.62,.87],.25,.08,radius=.0013)

# Broad shaped shoulder ornaments, with blackened recesses, gold filigree and gemstones.
for s in [-1,1]:
    def pauldron(u,v):
        a=(v-.5)*pi*1.10
        return Vector((s*(.147+.155*u),-.003+.115*sin(a)*(1-.36*u),1.505+.056*sin(pi*u)**.7*cos(a)-.028*u))
    surface('Sculpted gold shoulder shell',pauldron,25,29,bronze,'06_Regalia',.003,1)
    for v in [0,1]:trim(pauldron,'Shoulder gold rolled edge',gold,.003,'06_Regalia',v=v)
    for j in range(5):
        u=.15+.16*j;path=[]
        for k in range(45):
            t=k/44;path.append(pauldron(u+.075*sin(t*pi*2),t)+Vector((0,0,.006)))
        curve('Shoulder acanthus ribs',path,.003,gold)
    uv('Shoulder garnet',(s*.224,-.018,1.557),(.018,.031,.009),gem)

# Belt with sculptural filigree, cabochon and draped chains.
curve('Velvet fitted belt',[(.192*sin(a),-.161*cos(a),1.098) for a in [2*pi*k/120 for k in range(121)]],.019,black)
for z in [1.081,1.115]:curve('Fine belt metal border',[(.194*sin(a),-.165*cos(a),z) for a in [2*pi*k/120 for k in range(121)]],.0027,gold)
uv('Belt sun relief',(0,-.174,1.098),(.048,.012,.039),bronze)
uv('Belt central stone',(0,-.192,1.103),(.014,.009,.021),gem)
for k in range(12):
    a=k/12*2*pi
    curve('Belt petal engraving',[(.031*cos(a)+.013*cos(t),-.189,1.10+.023*sin(a)+.008*sin(t)) for t in [2*pi*j/32 for j in range(33)]],.0016,gold)
for s in [-1,1]:
    for k in range(3):
        pts=bez([(s*.023,-.19,1.089),(s*.05,-.207,1.00-k*.035),(s*.12,-.189,1.00-k*.035),(s*.17,-.12,1.087)])
        curve('Waist droplet chain',pts,.0017,gold)
        for j in range(0,len(pts),6):uv('Chain ruby bead',pts[j],(.003,.003,.004),gem,seg=12)
    # Long hanging silk strip with intricate fitted edge decoration.
    def stole(u,v):
        return Vector((s*(.049+.10*u+.025*sin(u*7))+(v-.5)*.050,-.168-.071*u+.012*sin(u*9+v*3),1.09-.95*u+.013*sin(v*pi)))
    surface('Layered ivory front sash',stole,65,13,ivory,'02_Innerwear',.002,1)
    for v in [0,1]:trim(stole,'Sash woven edge',gold,.002,'02_Innerwear',v=v)
    floral(stole,[.15,.35,.55,.75,.92],[.5],.13,.22,'02_Innerwear',.00075)

# Layered chains drape over the exposed chest, shrink-fitted to the skin surface.
for tier in range(3):
    pts=[]
    for j in range(151):
        t=j/150;x=.070*cos(pi*t);z=1.558-(.214+tier*.075)*sin(pi*t)**.84
        hit,_,_,_=bvh.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)),.5)
        y=(hit.y-.006) if hit is not None else -.145
        pts.append(Vector((x,y,z)))
    curve('Draped fine neck chain',pts,.0013,platinum)
    back=[Vector((-.07*cos(a),.030+.048*sin(a),1.558+.004*sin(a))) for a in [pi*j/60 for j in range(61)]]
    curve('Neck chain back connection',[pts[-1]]+back+[pts[0]],.0013,platinum)
    loops=[]
    for j in range(2,148,3):
        c=pts[j];tangent=(pts[j+1]-pts[j-1]).normalized();across=tangent.cross(Vector((0,1,0))).normalized()
        loops.append([c+tangent*(.0023*cos(a))+across*(.0015*sin(a)) for a in [2*pi*k/12 for k in range(13)]])
    batch_curves('Articulated neck chain links',loops,.00055,gold,'06_Regalia',False,0)
    p=pts[75]
    uv('Suspended engraved chest pendant',p+Vector((0,-.003,-.009)),(.008,.004,.017),gold)
    uv('Chest ruby pendant inset',p+Vector((0,-.008,-.009)),(.0045,.002,.011),gem)

# Long ribbon-like mantle panels. The rightward flow is modeled, not simulated.
mantle_funs=[]
for idx in range(8):
    a=(idx-3.5)/3.5
    root=Vector((a*.207,.098,1.475-abs(a)*.019))
    end=Vector((.60+a*.82,.48+.12*sin(idx),.08+.18*(idx%3)+.07*cos(idx)))
    controls=[root,Vector((a*.34+.25,.28,1.43)),Vector((a*.55+1.0,.38+.19*cos(idx),.66+.22*sin(idx))),end]
    cs=bez(controls,101)
    def mantle(u,v,cs=cs,idx=idx):
        j=min(99,int(u*100));c=cs[j].lerp(cs[j+1],u*100-j)
        width=(.044+.13*sin(pi*u)**.65)*(1-.8*u**8)
        q=(v-.5)*2
        flutter=.043*sin(u*14+q*3+idx)*sin(pi*u)**.6
        return c+Vector((q*width,.047*cos(q*pi*1.3)*sin(pi*u)+flutter,.05*q*q*sin(pi*u)+.044*sin(u*11+idx)*q))
    mantle_funs.append(mantle)
    surface('Wind-sculpted mantle %02d'%idx,mantle,101,29,red2 if idx%3==0 else red,'04_Mantle',.002,1)
    for v in [0,1]:trim(mantle,'Mantle cut gold edge',gold,.0027,'04_Mantle',v=v)
    floral(mantle,[.16,.32,.49,.66,.82],[.5],.18,.32,'04_Mantle',.0014)
    # Branching glowing seams hug the fabric; vary path so it reads as embers rather than uniform piping.
    paths=[]
    for k in range(4):
        paths.append([mantle(t,.5+.33*sin(t*13+k*1.7))+Vector((0,-.006,0)) for t in [.08+.9*j/110 for j in range(111)]])
    batch_curves('Molten branching mantle seams',paths,.0016,ember,'04_Mantle',True,1)

# Broad billowing cloth lobes break the regular feather silhouette, with curved flame tips.
for idx in range(3):
    controls=[Vector((-.13+idx*.11,.19,1.48)),Vector((.35,.29,1.70-idx*.14)),Vector((1.13,.44,1.32-idx*.22)),Vector((1.62-idx*.1,.42,1.36-idx*.30))]
    cs=bez(controls,101)
    def billow(u,v,cs=cs,idx=idx):
        j=min(99,int(u*100));c=cs[j].lerp(cs[j+1],u*100-j);q=(v-.5)*2
        width=.018+.19*sin(pi*.83*u)**.60
        return c+Vector((.03*q*sin(u*12)+u**7*.065*sin(q*9+idx),q*width*.55+.055*sin(u*17+q*3)*sin(pi*u),q*width+.060*cos(q*5+u*10)*sin(pi*u)+u**7*.030*cos(q*13+idx)))
    surface('Broad wind-billowed silk %02d'%idx,billow,101,45,red2,'04_Mantle',.002,1)
    for v in [0,1]:trim(billow,'Billowing edge ember',ember,.0028,'04_Mantle',v=v)
    floral(billow,[.19,.35,.51,.68,.85],[.32,.68],.16,.20,'04_Mantle',.0013)

# A flowing translucent outer veil with gold fire filigree provides a broad cloth silhouette.
veil=material('Thin dark garnet organza',(.08,.002,.002),.03,.50)
setp(veil,'Transmission Weight',.18)
def veilfun(u,v):
    q=(v-.5)*2
    return Vector((q*(.21+.53*u)+.61*u**1.5,.14+.50*u+.065*sin(u*10+q*4),1.48-1.36*u+.11*sin(pi*u)*cos(q*4)+.07*(1-q*q)*sin(u*9)))
surface('Long trailing organza veil',veilfun,90,80,veil,'04_Mantle',.001,1)
for v in [0,1]:trim(veilfun,'Veil metallic edge',gold,.0018,'04_Mantle',v=v)
floral(veilfun,[.20,.39,.58,.78,.93],[.17,.36,.64,.83],.13,.075,'04_Mantle',.0009)

# Hair: thousands of tapered individual fibers following waved guides, no plastic ribbon locks.
def scalp(u,v):
    a=2*pi*v;ph=.015+(1.94-.68*max(0,cos(a)))*u
    return Vector((.098*sin(ph)*sin(a),-.039-.120*sin(ph)*cos(a),1.774+.111*cos(ph)))
scalpmat=material('Natural scalp beneath white hair',(.59,.385,.285),0,.60)
surface('Scalp under fibers',scalp,24,97,scalpmat,'05_Hair',.001,1)
guides=[]
for s in [-1,1]:
    for k in range(9):
        off=k/8
        guides.append(([(s*(.003+.027*off),-.030+.015*off,1.884-.008*off),(s*(.108+.021*off),-.162,1.902-.027*off),(s*(.123-.025*off),-.190,1.727-.018*k),(s*(.060+.013*k),-.154,1.772-.025*k)],.008,.006,75))
    for k in range(12):
        off=k/11
        guides.append(([(s*(.047+.032*off),-.055+.08*off,1.855-.025*off),(s*(.17+.035*off),-.10+.04*off,1.79),(s*(.07+.07*off),-.21+.12*off,1.40),(s*(.19+.07*off)+.07,-.14+.18*off,1.15+.12*sin(k))],.012,.009,70))
for k in range(28):
    a=1.35+3.60*k/27;p=scalp(.46,a/(2*pi))
    guides.append(([p,Vector((p.x*1.7,.17,1.68)),Vector((.12+p.x*2.5,.28,1.45)),Vector((.20+p.x*3.4,.30+.07*sin(k),1.04+.10*cos(k)))],.016,.010,70))
# Root fibers flow over the cap; follows cranial surface instead of converging on a flat sheet.
paths_by_mat=[[] for _ in hairmats]
for k in range(1000):
    a=random.random();end=.75+random.random()*.25
    path=[scalp(.02+(end-.02)*j/28,a)+Vector((0,-.0005,.0015)) for j in range(29)]
    paths_by_mat[k%4].append(path)
for guide,w,d,count in guides:
    cs=bez(guide,38)
    for k in range(count):
        phase=random.random()*2*pi;ox=random.uniform(-1,1)*w;oy=random.uniform(-1,1)*d
        path=[]
        length=33+random.randrange(5)
        for j,c in enumerate(cs[:length]):
            t=j/37;tan=(cs[min(37,j+1)]-cs[max(0,j-1)]).normalized();across=tan.cross(Vector((0,1,0))).normalized();normal=tan.cross(across)
            wave=.002*sin(t*18+phase)*sin(pi*t)
            curl=Vector((.023*sin(t*12+guide[0][0]*24)*sin(pi*t)**2,-.018*cos(t*11+guide[0][0]*13)*sin(pi*t)**2,0))
            path.append(c+across*(ox*(.30+.70*sin(pi*t))+wave)+normal*(oy*sin(pi*t)+wave*.35)+curl)
        paths_by_mat[k%4].append(path)
for i,paths in enumerate(paths_by_mat):batch_curves('Waved silver individual fibers '+str(i),paths,.00030,hairmats[i],'05_Hair',True,0)

# Filigree crown with seven sculpted upward flames and small suspended sun arcs.
def flame_leaf(name,base,tip,width,mat,group='06_Regalia'):
    base=Vector(base);tip=Vector(tip);axis=tip-base;across=axis.cross(Vector((0,1,0))).normalized()
    vs=[];fs=[]
    for j in range(21):
        t=j/20;c=base+axis*t+across*(width*.35*sin(pi*t*2));w=width*sin(pi*t)**.75
        for q in [-1,-.5,0,.5,1]:vs.append(c+across*(q*w)+Vector((0,-width*.25*(1-q*q)*sin(pi*t),0)))
    for j in range(20):
        for k in range(4):fs.append((j*5+k,(j+1)*5+k,(j+1)*5+k+1,j*5+k+1))
    return mesh(name,vs,fs,mat,group,1,.0015)
for a0,a1 in [(-100,-17),(17,100)]:
    pts=[(.132*sin(a),.022,1.827+.139*cos(a)) for a in [math.radians(a0+(a1-a0)*k/70) for k in range(71)]]
    curve('Split solar circlet',pts,.0035,gold)
curve('Crown structural band',[(.104*sin(a),-.045-.083*cos(a),1.837+.018*cos(a)) for a in [2*pi*k/140 for k in range(141)]],.005,gold)
for k in range(13):
    a=math.radians(-80+k*13.33);base=Vector((.103*sin(a),-.049-.080*cos(a),1.837+.018*cos(a)))
    tip=base+Vector((.033*sin(a),.022,.053+.045*(k%2)+.015*cos(k*2)))
    flame_leaf('Forged flame crown finial',base,tip,.0085,gold)
    curve('Crown ember ridge',bez([base,base+Vector((.009,-.006,.030)),tip-Vector((.006,.004,.014)),tip],28),.0015,ember)
    uv('Crown garnet cabochon',base+Vector((0,-.006,.006)),(.0055,.004,.009),gem,seg=24)
curve('Engraved forehead band',[(.10*sin(a),-.043-.118*cos(a),1.819+.014*cos(a*2)) for a in [2*pi*k/160 for k in range(161)]],.0035,gold)
uv('Forehead tear garnet',(0,-.166,1.820),(.009,.005,.016),gem)

# Ceremonial staff: offset angular sun sculpture, chased helical shaft.
a=Vector((.61,-.03,.05));b=Vector((.86,.015,1.90))
curve('Obsidian ceremonial staff',linepoints(a,b,100),.011,smoke,'07_Staff')
for phase in [0,pi]:
    curve('Chased spiral staff',[a.lerp(b,t)+Vector((.012*cos(t*2*pi*13+phase),.012*sin(t*2*pi*13+phase),0)) for t in [j/650 for j in range(651)]],.0016,gold,'07_Staff')
center=b+Vector((.018,0,.088))
for r in [.055,.091]:curve('Chased staff sun ring',[(center.x+r*cos(t),center.y,center.z+r*sin(t)) for t in [2*pi*j/100 for j in range(101)]],.003,gold,'07_Staff')
uv('Luminous staff crystal',center,(.022,.017,.046),gem,'07_Staff',48)
for k in range(11):
    an=2*pi*k/11;base=center+Vector((.075*cos(an),0,.075*sin(an)));tip=center+Vector((.144*cos(an+.16),0,.144*sin(an+.16)))
    flame_leaf('Staff forged sun flame',base,tip,.016,gold,'07_Staff')
    curve('Staff molten flame vein',bez([base,base+Vector((.01,-.005,.01)),tip-Vector((.008,0,.004)),tip],24),.0018,ember,'07_Staff')

# A restrained downward, three-quarter head pose. Body neck falloff keeps the shoulder seam smooth.
from mathutils import Matrix
pivot=Vector((0,-.015,1.59))
headxf=Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-9),4,'Z') @ Matrix.Rotation(math.radians(7),4,'X') @ Matrix.Translation(-pivot)
for ob in list(COL['01_Body'].objects):
    if ob in [body,full]:
        for v in ob.data.vertices:
            weight=max(0,min(1,(v.co.z-1.56)/.067));weight=weight*weight*(3-2*weight)
            v.co=v.co.lerp(headxf@v.co,weight)
    else:ob.matrix_world=headxf@ob.matrix_world
for ob in list(COL['05_Hair'].objects):ob.matrix_world=headxf@ob.matrix_world
for ob in list(COL['06_Regalia'].objects):
    if any(word in ob.name.lower() for word in ['crown','circlet','forehead']):ob.matrix_world=headxf@ob.matrix_world

# Real 3D translucent flame ribbons and embers, separated for effects-free review/export.
COL['08_EmberFX']=bpy.data.collections.new('08_EmberFX');scene0=bpy.context.scene;scene0.collection.children.link(COL['08_EmberFX'])
flamemat=bpy.data.materials.new('Emissive translucent flame silk');flamemat.use_nodes=True
nt=flamemat.node_tree;nt.nodes.clear();output=nt.nodes.new('ShaderNodeOutputMaterial');mix=nt.nodes.new('ShaderNodeMixShader');trans=nt.nodes.new('ShaderNodeBsdfTransparent');em=nt.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1,.11,.003,1);em.inputs['Strength'].default_value=5
coord=nt.nodes.new('ShaderNodeTexCoord');no=nt.nodes.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=9;no.inputs['Detail'].default_value=3
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.42;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.68;ramp.color_ramp.elements[1].color=(.75,.75,.75,1)
nt.links.new(coord.outputs['UV'],no.inputs['Vector']);nt.links.new(no.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],mix.inputs[0]);nt.links.new(trans.outputs[0],mix.inputs[1]);nt.links.new(em.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],output.inputs[0])
for k in range(34):
    fun=mantle_funs[k%len(mantle_funs)];base=fun(.24+.70*random.random(),random.choice([0,1]));length=.10+random.random()*.22
    phase=random.random()*2*pi
    def flame(u,v,base=base,length=length,phase=phase):
        q=(v-.5)*2;w=.012*sin(pi*u)**.8*(1-u)
        return base+Vector((u*length*.55+.025*sin(u*9+phase)*sin(pi*u)+q*w,-.011-q*w*.45,u*length+.018*sin(u*13+phase)*sin(pi*u)))
    surface('Translucent sculpted flame tongue',flame,33,9,flamemat,'08_EmberFX',0,0)
sparkpaths=[]
for k in range(150):
    base=Vector((random.uniform(-.15,1.65),random.uniform(-.03,.65),random.uniform(.3,1.9)))
    if random.random()<.55 and base.x<.5:continue
    length=random.uniform(.002,.016)
    sparkpaths.append([base,base+Vector((length*.4,0,length))])
batch_curves('Floating hot embers',sparkpaths,.00085,hot,'08_EmberFX',True,0)

# Sculpted basalt ground, separate from all model exports.
rock=material('Rough volcanic basalt',(.016,.019,.024),.12,.75)
nt=rock.node_tree;tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=9;tex.inputs['Detail'].default_value=5
bp=nt.nodes.new('ShaderNodeBump');bp.inputs['Strength'].default_value=.5;bp.inputs['Distance'].default_value=.04
nt.links.new(tex.outputs['Fac'],bp.inputs['Height']);nt.links.new(bp.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
vor=nt.nodes.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=6
coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Generated'],vor.inputs['Vector'])
cracks=nt.nodes.new('ShaderNodeValToRGB');cracks.color_ramp.elements[0].position=.002;cracks.color_ramp.elements[0].color=(1,1,1,1);cracks.color_ramp.elements[1].position=.005;cracks.color_ramp.elements[1].color=(0,0,0,1)
nt.links.new(vor.outputs['Distance'],cracks.inputs[0]);strength=nt.nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.65;nt.links.new(cracks.outputs[0],strength.inputs[0]);nt.links.new(strength.outputs[0],nt.nodes.get('Principled BSDF').inputs['Emission Strength']);nt.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.11,.004,1)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.7,depth=.14,location=(.35,.18,-.10));o=bpy.context.object;assign(o,'90_Stage');o.name='Basalt presentation ground';o.data.materials.append(rock)
be=o.modifiers.new('Worn rock edges','BEVEL');be.width=.04;be.segments=3
for k in range(50):
    a=random.random()*2*pi;r=random.uniform(.95,1.5);loc=(.3+r*cos(a),.18+r*sin(a),-.015)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.05,.14),location=loc);o=bpy.context.object;assign(o,'90_Stage');o.name='Basalt fragment';o.scale=(1,.7,.4);o.data.materials.append(rock)
    o.rotation_euler=(random.random(),random.random(),random.random()*pi)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.19));o=bpy.context.object;assign(o,'90_Stage');o.data.materials.append(material('Dark neutral backdrop',(.005,.008,.012),0,.8))
def area(name,loc,power,color,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);COL['90_Stage'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Portrait warm softbox',(-2,-3.5,3.8),260,(1,.85,.70),2.1,(0,0,1.4))
area('Cool fill',(2.5,-2.6,2.6),100,(.65,.78,1),2,(0,0,1.1))
area('Ember rim',(1,1.5,2.8),380,(1,.21,.045),1.5,(0,0,1))
area('Silver rim',(-1.6,1.2,3),230,(.63,.78,1),1.5,(0,0,1.5))

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32 if DRAFT else 96;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.world.color=(.04,.04,.04);scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
data=bpy.data.cameras.new('Couture Camera');camera=bpy.data.objects.new('Couture Camera',data);COL['90_Stage'].objects.link(camera);scene.camera=camera
def camera_at(loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale
def hero():camera_at((3,-7,2.9),(.35,.13,1.03),4.00)
hero();scene.render.resolution_x=2560;scene.render.resolution_y=1600
scene.use_nodes=True;tree=scene.node_tree;tree.nodes.clear()
rl=tree.nodes.new('CompositorNodeRLayers');gl=tree.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=2.3
out=tree.nodes.new('CompositorNodeComposite');tree.links.new(rl.outputs['Image'],gl.inputs['Image']);tree.links.new(gl.outputs['Image'],out.inputs['Image'])
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for ar in bpy.context.screen.areas:
    if ar.type=='VIEW_3D':ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
views=[('01_Hero',(3,-7,2.9),(.35,.13,1.03),4.00,(2560,1600)),('02_Front',(0,-7,2.20),(.30,.05,1.04),2.68,(1800,1800)),('03_Back',(-3,7,2.70),(.33,.16,1.03),2.90,(1800,1800)),('04_Portrait',(.7,-4,1.95),(.015,-.01,1.67),.68,(1800,1800)),('06_Embroidery',(2,-4,1.9),(.20,-.03,1.30),.85,(1800,1800))]
if DRAFT:views=[views[0],views[3]]
for name,loc,target,scale,res in views:
    camera_at(loc,target,scale);scene.render.resolution_x=res[0]//(2 if DRAFT else 1);scene.render.resolution_y=res[1]//(2 if DRAFT else 1)
    scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
if not DRAFT:
    COL['08_EmberFX'].hide_render=True
    gl.mute=True
    strength.inputs[1].default_value=0
    lightsave=[(o.data,o.data.energy,o.data.color[:]) for o in COL['90_Stage'].objects if o.type=='LIGHT']
    for data0,_,_ in lightsave:
        data0.color=(1,1,1);data0.energy=200
    emissions=[]
    for mat in bpy.data.materials:
        if mat.use_nodes:
            pp=mat.node_tree.nodes.get('Principled BSDF')
            if pp and not pp.inputs['Emission Strength'].is_linked:
                emissions.append((pp,pp.inputs['Emission Strength'].default_value));pp.inputs['Emission Strength'].default_value=0
    camera_at((2.6,-7,2.6),(.37,.12,1.03),3.12);scene.render.resolution_x=1800;scene.render.resolution_y=1800
    scene.render.filepath=str(RENDER/'05_Neutral.png');bpy.ops.render.render(write_still=True)
    for pp,val in emissions:pp.inputs['Emission Strength'].default_value=val
    for data0,energy,color in lightsave:data0.energy=energy;data0.color=color
    gl.mute=False;COL['08_EmberFX'].hide_render=False
    strength.inputs[1].default_value=.65
hero();scene.render.resolution_x=2560;scene.render.resolution_y=1600
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
print('COUTURE_MODEL_RENDERED',VERSION,flush=True)
