import bpy, math, random, json
from mathutils import Vector
from pathlib import Path
random.seed(38)
ROOT=Path(__file__).parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
M={}; B={}
def mat(name,color,rough=.6,metal=0,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal
    if emission: bs.inputs['Emission Color'].default_value=(*color,1); bs.inputs['Emission Strength'].default_value=emission
    M[name]=m; B[name]=[[],[]]
    return m
for a in [('stone',(.53,.51,.46)),('ivory',(.76,.73,.64)),('dark',(.12,.13,.125)),('road',(.095,.105,.115)),('paving',(.49,.48,.44)),('curb',(.66,.65,.59)),('white',(.85,.85,.76)),('yellow',(.78,.57,.11)),('gold',(.65,.47,.22)),('ochre',(.49,.29,.105)),('cream',(.8,.7,.46)),('red',(.49,.025,.025)),('trunk',(.17,.12,.07)),('soil',(.14,.13,.075)),('silver',(.55,.59,.58)),('rubber',(.022,.026,.029)),('greenSign',(.015,.12,.09)),('blueSign',(.016,.13,.28))]:mat(*a)
for i,c in enumerate([(.18,.27,.3),(.25,.38,.43),(.37,.5,.55),(.13,.22,.25),(.44,.48,.45)]):mat('glass'+str(i),c,.22,.42)
for i,c in enumerate([(.025,.075,.012),(.045,.12,.021),(.085,.17,.035),(.12,.21,.05)]):mat('leaf'+str(i),c,.85)
for i,c in enumerate([(.67,.7,.69),(.05,.065,.075),(.23,.27,.29),(.23,.1,.065),(.55,.57,.5)]):mat('car'+str(i),c,.24,.5)
mat('lamp',(1,.82,.47),.35,0,2);mat('redLight',(1,.012,.004),.4,0,3)

def mesh(name,verts,faces,material):
    v,f=B[material]; n=len(v); v.extend(verts); f.extend([tuple(n+i for i in x) for x in faces])
def box(name,loc,dim,material,rz=0):
    x,y,z=loc; a,b,c=[d/2 for d in dim]; co=math.cos(rz); si=math.sin(rz)
    verts=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
    mesh(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material)
def ball(name,loc,scale,material,seg=10,rings=6):
    verts=[];faces=[]
    for j in range(rings+1):
        p=math.pi*j/rings
        for i in range(seg):
            t=2*math.pi*i/seg; verts.append((loc[0]+scale[0]*math.sin(p)*math.cos(t),loc[1]+scale[1]*math.sin(p)*math.sin(t),loc[2]+scale[2]*math.cos(p)))
    for j in range(rings):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;faces.append((a,b,b+seg,a+seg))
    mesh(name,verts,faces,material)
def rod(name,a,b,r,material,seg=8):
    v=Vector(b)-Vector(a); q=v.to_track_quat('Z','Y'); verts=[]
    for z in [0,v.length]:
        for i in range(seg):
            p=q@Vector((r*math.cos(i*math.tau/seg),r*math.sin(i*math.tau/seg),z))+Vector(a);verts.append(tuple(p))
    faces=[tuple(range(seg-1,-1,-1)),tuple(range(seg,seg*2))]+[(i,(i+1)%seg,(i+1)%seg+seg,i+seg) for i in range(seg)]
    mesh(name,verts,faces,material)
font=None
try:font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc')
except:pass
def text(name,body,loc,size,material='white',rot=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.012
    if font:cu.font=font
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rot;cu.materials.append(M[material])

# Meter-scale interpretive reconstruction. X east, Y north, Z up; no photographic people/textures.
box('base',(0,0,-.45),(300,270,.7),'soil')
box('main boulevard',(0,0,-.045),(280,27,.12),'road')
box('cross street',(-20,0,-.04),(25,250,.12),'road')
for x,y,w,h in [(59,58,156,87),(-84,61,100,93),(56,-60,151,93),(-82,-63,103,99)]:
    box('sidewalk',(x,y,0),(w,h,.22),'paving')
    # regular paving seams
    for xx in range(int(x-w/2),int(x+w/2),3):box('paver seam',(xx,y,.112),(.025,h,.012),'stone')
    for yy in range(int(y-h/2),int(y+h/2),3):box('paver seam',(x,yy,.113),(w,.025,.012),'stone')
for x,w in [(-84,105),(61,155)]:
    for y in [-13.7,13.7]:box('curb',(x,y,.15),(w,.35,.3),'curb')
for x in [-33, -7]:
    for y,h in [(-65,99),(65,99)]:box('curb',(x,y,.15),(.35,h,.3),'curb')
for x in range(-138,140,9):
    if -36<x<-4:continue
    for y in [-9,-5,5,9]:box('lane dash',(x,y,.025),(4,.12,.015),'white')
    for y in [-.18,.18]:box('double yellow',(x,y,.028),(9,.13,.015),'yellow')
for y in range(-120,122,9):
    if abs(y)<18:continue
    for x in [-28,-12]:box('lane dash',(x,y,.029),(.12,4,.015),'white')
    for x in [-20.18,-19.82]:box('double yellow',(x,y,.03),(.13,9,.015),'yellow')
for xx in [-39,0]:
    for yy in range(-11,12,2):box('zebra',(xx,yy,.04),(5,1,.02),'white')
for yy in [-19,19]:
    for xx in range(-30,-8,2):box('zebra',(xx,yy,.04),(1,5,.02),'white')

colliders=[]
def collider(x,y,w,d):colliders.append({'x':x,'z':-y,'w':w,'d':d})
def tower(x,y,w,d,h):
    collider(x,y,w,d);box('residential mass',(x,y,h/2),(w,d,h),'stone')
    box('retail podium',(x,y,3.7),(w+1,d+1,7.4),'ivory')
    floors=int((h-8)/3.1);bays=int(w/3.8)
    for side in [-1,1]:
        yf=y+side*(d/2+.06)
        for i in range(bays):
            xx=x-w/2+(i+.5)*w/bays
            box('vertical inset',(xx,yf,8+(h-8)/2),(w/bays-.28,.18,h-8),'dark')
            for j in range(floors):
                zz=9.1+j*3.1;glass='glass'+str(random.randrange(5))
                box('apartment glass',(xx,yf+side*.13,zz),(w/bays-.65,.09,2.05),glass)
                box('window mullion',(xx,yf+side*.21,zz),(.065,.08,2.08),'dark')
                box('window transom',(xx,yf+side*.21,zz-.35),(w/bays-.6,.08,.06),'dark')
                if i%3==0:
                    box('balcony slab',(xx,yf+side*.38,zz-1.18),(w/bays-.15,.85,.17),'stone')
                    box('balcony rail',(xx,yf+side*.7,zz-.78),(w/bays-.3,.06,.65),'glass3')
                if i%3==1 and j%2==0:
                    box('AC condenser',(xx+1,yf+side*.4,zz-1),(.58,.4,.36),'ivory')
        for i in range(bays+1):box('facade upright',(x-w/2+i*w/bays,yf+side*.28,h/2+3),(.26,.4,h-6),'ivory')
        for i in range(bays):
            xx=x-w/2+(i+.5)*w/bays
            box('shopfront',(xx,yf+side*.18,3.1),(w/bays-.5,.1,5),'glass1')
            box('shop door',(xx,yf+side*.26,1.5),(.06,.06,2.9),'silver')
            box('shop header',(xx,yf+side*.2,6.6),(w/bays-.3,.13,.8),'dark')
    for side in [-1,1]:
        for j in range(floors):
            for yy in [-d*.28,0,d*.28]:
                box('side window',(x+side*(w/2+.03),y+yy,9.1+j*3.1),(.09,d*.19,2.05),'glass'+str(random.randrange(4)))
        box('side pilaster',(x+side*(w/2+.15),y,h/2),(.3,.4,h),'ivory')
    for z in [7.5,h-.4,h+.3]:box('cornice',(x,y,z),(w+1,d+1,.35),'ivory')
    box('rooftop plant',(x,y,h+1.1),(w*.52,d*.5,2),'stone')
    for xx in [-w/2,w/2]:
        rod('roof balustrade',(x+xx,y-d/2,h+1.2),(x+xx,y+d/2,h+1.2),.07,'silver')

for values in [(-58,40,30,23,61),(-94,46,26,24,67),(-125,65,23,26,56),(-56,83,27,23,59),(-97,91,28,25,73),(-60,-47,29,23,62),(-95,-55,26,24,55),(-126,-66,24,23,51),(25,-62,28,22,57),(61,-68,29,23,65),(99,-75,27,22,56),(120,65,22,27,64)]:tower(*values)
text('beauty salon','光 影 理 发',(-58,28.1,6.4),1.2)
text('shop sign','青芽生活 · 生活馆',(-94,33.7,6.4),.85)

# Fictional Starbay shopping centre with patterned facade and glazed ground floor.
x,y,w,d,h=49,51,82,60,26
# Hollow ground floor, real opening at X=22..30 on the photographed south entrance.
box('STARBAY upper floors',(x,y,16),(w,d,20),'cream')
for cx,cy,cw,cd in [(8,51,1,60),(90,51,1,60),(49,81,82,1),(15,21,14,.6),(60,21,60,.6)]:collider(cx,cy,cw,cd)
box('rear ground wall',(49,81,3),(82,.6,6),'ivory');box('east ground wall',(90,51,3),(.6,60,6),'ivory')
box('interior stone floor',(49,51,.04),(81,59,.13),'ivory')
box('interior ceiling',(49,51,5.8),(81,59,.25),'ivory')
for side,face in [('front',21),('left',8)]:
    along=w if side=='front' else d
    for i in range(int(along/3)):
        for j in range(6):
            a=(x-w/2 if side=='front' else y-d/2)+(i+.5)*3
            z=7.5+j*3
            loc=(a,face-.07,z) if side=='front' else (face-.07,a,z)
            dim=(2.97,.16,2.97) if side=='front' else (.16,2.97,2.97)
            panel=('gold' if i<7 else 'ivory') if j>=2 else 'gold'
            if random.random()<.14:panel='cream'
            box('gold facade panel',loc,dim,panel)
    for i in range(int(along/2)):
        a=(x-w/2 if side=='front' else y-d/2)+(i+.5)*2
        if side=='front' and 22<a<30:continue
        loc=(a,face-.12,3.1) if side=='front' else (face-.12,a,3.1)
        dim=(1.88,.15,5.7) if side=='front' else (.15,1.88,5.7)
        box('retail glazing',loc,dim,'glass3')
    for z in [6.1,12.3]:
        box('burgundy belt',(x,20.75,z),(w,.3,.24),'red') if side=='front' else box('burgundy belt',(7.75,y,z),(.3,d,.24),'red')
# Diamond tiles across lower fascia
for i in range(39):
    for j in range(3):
        xx=9+i*2.08;zz=7.25+j*1.65
        mesh('diamond',[(xx,20.77,zz-1),(xx+1.02,20.77,zz),(xx,20.77,zz+1),(xx-1.02,20.77,zz)],[(0,1,2,3)],random.choice(['gold','ochre','cream']))
box('restaurant billboard',(62,20.48,18.8),(21,.4,10.3),'dark')
box('green billboard',(62,20.22,18.8),(20.6,.08,9.9),'greenSign')
text('restaurant','云 朵 食 堂',(62,20.12,19.4),2.25)
text('restaurant english','CLOUD KITCHEN',(62,20.11,17.9),.6)
text('restaurant sub','热食  咖啡  慢生活',(62,20.11,16.05),.9)
text('roof Starbay','星湾广场',(30,20.2,26.8),3,'red')
text('roof Starbay english','STARBAY PLAZA',(31,20.1,25.7),.72,'red')
box('entry canopy',(26,18.5,4.8),(18,5,.35),'silver')
for xx in [18,34]:rod('entry column',(xx,17,0),(xx,17,4.8),.14,'silver')
text('entrance','星湾广场  STARBAY PLAZA',(26,15.9,4.15),.55)
# An interpretive interior; all shop names and layout are fictional.
mat('interiorWood',(.30,.19,.105));mat('interiorGreen',(.055,.15,.10));mat('interiorCoral',(.55,.16,.095));mat('interiorGlow',(1,.83,.57),.45,0,2)
for xx in range(11,89,3):box('interior floor joint',(xx,51,.115),(.017,59,.008),'stone')
for yy in range(24,80,3):box('interior floor joint',(49,yy,.116),(80,.017,.008),'stone')
for xx in [22,40,58,76]:
    for yy in [31,47,65,77]:
        rod('interior pillar',(xx,yy,.1),(xx,yy,5.68),.30,'ivory',20);collider(xx,yy,.7,.7)
for xx in [17,33,49,65,81]:
    for yy in [28,40,53,67,77]:box('ceiling light',(xx,yy,5.62),(5,.3,.06),'interiorGlow')
# Entry wayfinding and service desk, visible from the automatic doors.
box('welcome sign',(26,27,4.55),(10,.22,1),'interiorGreen');text('welcome','欢迎来到星湾 · 首层大厅',(26,26.82,4.35),.42)
box('service desk',(42,28,.64),(7,1.7,1.15),'interiorWood');collider(42,28,7,1.7)
box('desk top',(42,28,1.27),(7.2,1.85,.1),'ivory');text('service label','服 务 台',(42,27.09,.70),.32)
text('interior identity','STARBAY  /  CITY LIVING',(49,79.8,3.7),1.1,'gold')
text('interior caveat','虚构世界 · 地点与商家均为游戏设定',(49,79.7,2.55),.42,'stone')
# Left coffee shop and seating: open fronts, counter and chairs are solid obstacles.
box('cafe backdrop',(10,46,2.2),(1,20,4.4),'interiorWood');box('cafe counter',(14,44,.68),(2.1,9,1.2),'interiorGreen');collider(14,44,2.1,9)
text('coffee shop','街角咖啡  /  COFFEE',(16.5,38.5,3.85),.55,'interiorGreen')
for yy in [53,59]:
    for xx in [15,23]:
        rod('table pedestal',(xx,yy,.15),(xx,yy,.86),.07,'dark');box('cafe table',(xx,yy,.9),(1.1,1.1,.1),'interiorWood');collider(xx,yy,1.6,1.6)
        for side in [-1,1]:box('cafe chair',(xx+side*.9,yy,.47),(.46,.48,.12),'interiorCoral')
# A book shop and colorful family shop on the opposite side of the atrium.
box('bookshop backdrop',(87,45,2.2),(1,20,4.4),'interiorWood')
for yy in [38,43,48,53]:
    box('bookshelf',(85,yy,1.3),(1,3.7,2.5),'interiorWood');collider(85,yy,1,3.7)
    for z in [.5,1.1,1.7,2.3]:
        box('shelf',(84.8,yy,z),(1.3,3.7,.08),'ivory')
        for b in range(12):box('book',(84.7,yy-1.6+b*.27,z+.20),(.7,.16,.34),random.choice(['red','blueSign','cream','greenSign']))
text('bookshop sign','城市书屋 · BOOKS',(76,36.5,3.8),.58,'interiorWood')
box('family kiosk',(72,66,.6),(8,4,1.1),'cream');collider(72,66,8,4)
text('family sign','童趣乐园',(72,63.8,2.85),.7,'interiorCoral')
for xx in [70,72,74]:ball('toy',(xx,65,1.65),(.4,.4,.5),random.choice(['red','blueSign','yellow']))
# Atrium art, planters, and rest seating leave a clear circulation loop.
box('atrium planting',(57,52,.45),(7,5,.8),'ivory');collider(57,52,7,5)
for xx in [55,57,59]:
    rod('indoor trunk',(xx,52,.8),(xx,52,2.5),.1,'trunk');ball('indoor crown',(xx,52,2.7),(1.1,1.1,.7),'leaf1')
for xx,yy in [(44,65),(53,68),(35,55)]:
    box('interior sofa',(xx,yy,.45),(4,1,.65),'interiorGreen');box('sofa back',(xx,yy+.5,.95),(4,.25,.8),'interiorGreen');collider(xx,yy,4,1.4)
for xx in [27,65]:
    box('interior guide',(xx,35,1.6),(.8,.25,3),'interiorGreen');text('guide','1F\n大厅',(xx,34.83,2.2),.25)
# Landmark pylon
box('pylon',(4,27,8),(1.5,1.5,16),'ivory');text('pylon text','星\n湾\n广\n场',(4,26.15,13.5),1,'red')
for z in [3,5,7]:box('pylon accent',(4,26.13,z),(.55,.1,.55),'gold',math.pi/4)

def tree(x,y,s=1):
    box('tree pit',(x,y,.16),(2.8*s,2.8*s,.2),'soil');rod('tree trunk',(x,y,.1),(x,y,4.5*s),.16*s,'trunk')
    for i in range(7):
        a=i*2.4;xx=x+math.cos(a)*1.25*s;yy=y+math.sin(a)*1.25*s;zz=(4.5+random.random()*1.8)*s
        rod('branch',(x,y,2.8*s),(xx,yy,zz),.065*s,'trunk')
        for j in range(16):ball('foliage',(xx+random.uniform(-1.05,1.05)*s,yy+random.uniform(-1.05,1.05)*s,zz+random.uniform(-.8,.8)*s),(.59*s,.52*s,.48*s),'leaf'+str(random.randrange(4)),8,5)
for xx in range(-131,132,11):
    if -38<xx<5:continue
    for yy in [-19,17]:
        if yy==17 and 12<xx<38:continue
        tree(xx,yy,random.uniform(.8,1.15))
for yy in range(-108,115,12):
    if abs(yy)<27:continue
    for xx in [-37,-3]:tree(xx,yy,random.uniform(.8,1.1))
# Plaza garden south-east
box('garden',(37,-31,.22),(24,9,.44),'curb');box('garden soil',(37,-31,.48),(23.4,8.4,.15),'soil');collider(37,-31,24,9)
for xx in range(27,49,3):
    for yy in [-33,-30]:ball('hedges',(xx,yy,1),(1.7,1.5,.85),'leaf1')
for xx in [28,39,47]:tree(xx,-31,1.15)
for xx,yy in [(17,-25),(55,-24),(78,16),(-45,19),(-71,-18)]:
    box('bench seat',(xx,yy,.6),(2.3,.62,.14),'trunk');box('bench back',(xx,yy+.3,1),(2.3,.13,.65),'trunk')
    for dx in [-.8,.8]:box('bench leg',(xx+dx,yy,.33),(.12,.5,.55),'dark')
for xx in range(5,85,5):rod('bollard',(xx,-15,.1),(xx,-15,.9),.075,'silver')

def lamp(x,y):
    rod('lamp post',(x,y,.1),(x,y,10.5),.12,'ivory')
    for sign in [-1,1]:
        points=[(x,y,8.5),(x+sign*.8,y,10.2),(x+sign*2.2,y,11.1),(x+sign*3,y,11.3)]
        for a,b in zip(points,points[1:]):rod('lamp arm',a,b,.065,'ivory')
        ball('luminaire',(x+sign*3,y,11.25),(.56,.21,.13),'silver');box('light panel',(x+sign*3,y,11.13),(.8,.25,.03),'lamp')
for xx in [-123,-83,-43,9,52,99]:
    for yy in [-14.3,14.3]:lamp(xx,yy)
for xx,yy in [(-34,-15),(-5,15),(-34,15),(-5,-15)]:
    rod('traffic signal pole',(xx,yy,0),(xx,yy,6.8),.13,'ivory')
    endx=xx+(9 if xx<-20 else -9);rod('signal cantilever',(xx,yy,6.8),(endx,yy,6.8),.15,'ivory')
    box('signal housing',(endx,yy,6.35),(.65,.45,1.7),'dark')
    for z in [5.85,6.35,6.85]:ball('signal light',(endx,yy-.25,z),(.19,.05,.19),'redLight' if z==6.85 else 'dark')

def car(x,y,angle,style):
    def cv(a,b,c):return (x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),c)
    box('car body',cv(0,0,.65),(4.65,1.86,.64),'car'+str(style),angle)
    ball('car bonnet',cv(1.1,0,.96),(1.05,.88,.2),'car'+str(style))
    box('car cabin',cv(-.2,0,1.16),(2.4,1.61,.65),'glass3',angle)
    box('car roof',cv(-.28,0,1.52),(1.9,1.5,.1),'car'+str(style),angle)
    for xx in [-1.45,1.4]:
        for yy in [-.94,.94]:
            rod('wheel',cv(xx,yy-.13,.43),cv(xx,yy+.13,.43),.36,'rubber',14)
            rod('alloy hub',cv(xx,yy-.145,.43),cv(xx,yy+.145,.43),.22,'silver',12)
    for yy in [-.63,.63]:
        box('headlight',cv(2.34,yy,.75),(.03,.45,.2),'lamp',angle)
        box('taillight',cv(-2.34,yy,.77),(.03,.48,.14),'redLight',angle)
    for xx in [-.6,.65]:box('pillar',cv(xx,0,1.2),(.09,1.65,.63),'car'+str(style),angle)
for val in [(-61,-7,0,1),(35,-7,0,0),(69,-11,0,2),(107,-7,0,4),(-88,7,math.pi,0),(47,7,math.pi,1),(-14,37,math.pi/2,2),(-26,-48,-math.pi/2,0)]:car(*val)
# Shared bikes parked on plaza, no source-photo humans.
for xx in range(60,73,2):
    for yy in [-23,-24.2]:
        # bike wheel rings approximated with slender spokes and dark tire torus-like segments
        center=(xx,yy,.48)
        for i in range(16):
            a=i*math.tau/16;b=(i+1)*math.tau/16
            rod('bike tire',(xx+math.cos(a)*.34,yy,.48+math.sin(a)*.34),(xx+math.cos(b)*.34,yy,.48+math.sin(b)*.34),.045,'rubber',5)
    rod('bike frame',(xx,-23,.48),(xx,-23.7,1),.065,'blueSign');rod('bike frame',(xx,-24.2,.48),(xx,-23.7,1),.06,'blueSign')
    box('bike saddle',(xx,-23.7,1.08),(.28,.35,.1),'dark');rod('handle',(xx,-24.1,1.2),(xx,-24.1,.5),.045,'silver');rod('handlebar',(xx-.32,-24.1,1.2),(xx+.32,-24.1,1.2),.045,'dark')

import sys
sys.path.insert(0,str(ROOT))
from build_world_v3 import build_world
build_world(box,rod,ball,text,collider,mat,tree)
from build_interior_v4 import build_interior
interior_upgrade=build_interior(box,rod,ball,text,collider,mat)

# Consolidate by material for efficient real-time rendering.
for name,(verts,faces) in B.items():
    if not verts:continue
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(M[name])
    if name.startswith('leaf'):
        for p in me.polygons:p.use_smooth=True

# Separate sliding door nodes can move in the real-time viewer.
doorMat=mat('doorGlass',(.24,.43,.49),.14,.1)
doorMat.diffuse_color=(.24,.43,.49,.22);doorMat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.22
for name,xx in [('EntryDoor_L',24),('EntryDoor_R',28)]:
    bpy.ops.mesh.primitive_cube_add(size=1,location=(xx,21.0,1.6));ob=bpy.context.object;ob.name=name;ob.dimensions=(3.9,.06,3.05);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(doorMat)

scene=bpy.context.scene
scene.world.use_nodes=True;nodes=scene.world.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');sky=nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=math.radians(12);sky.sun_rotation=math.radians(225);sky.altitude=.1;bg.inputs['Strength'].default_value=.23;scene.world.node_tree.links.new(sky.outputs[0],bg.inputs[0]);scene.world.node_tree.links.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(-90,-70,60));sun=bpy.context.object;sun.name='Late afternoon sunlight';sun.rotation_euler=(math.radians(66),math.radians(-20),math.radians(-45));sun.data.energy=3;sun.data.angle=.06;sun.data.color=(1,.79,.55)
bpy.ops.object.camera_add(location=(-43,-48,15));cam=bpy.context.object;cam.name='Starbay street view';cam.rotation_euler=(Vector((36,31,12))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=27;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
    for dev in pref.devices:dev.use=dev.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# Export environment before Blender-only animated NPC instances.
bpy.ops.object.select_all(action='DESELECT')
for ob in scene.objects:
    if ob.type in {'MESH','FONT'}:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/starbay_environment.glb'),use_selection=True,export_format='GLB',export_apply=True)
manifest={'colliders':colliders,'bounds':[-135,135,-112,112],'setting':'fictional','units':'meters','design':'fictional urban neighbourhood','blender':'4.5.9 LTS','version':4,'interiorUpgrade':interior_upgrade,'interior':{'minX':8.6,'maxX':89.4,'minZ':-80.4,'maxZ':-21,'entrance':[26,-21],'fictional':True}}
(ROOT/'assets/scene.json').write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
# Independently evaluated armatures keep the saved Blender crowd fully editable.
for i,(xx,yy) in enumerate([(13,16),(41,16),(72,16),(-44,20),(-72,18),(10,-19),(54,-20),(-39,-32)]):
    kind=['man','woman','elder','child'][i%4]
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/f'assets/npc_{kind}.glb'));added=set(bpy.data.objects)-before
    bpy.context.view_layer.update();points=[o.matrix_world@Vector(p) for o in added if o.type=='MESH' for p in o.bound_box]
    low=min(p.z for p in points);height=max(p.z for p in points)-low
    wrapper=bpy.data.objects.new('Pedestrian %02d'%i,None);scene.collection.objects.link(wrapper)
    for ob in added:
        if ob.parent not in added:ob.parent=wrapper
        if ob.type=='ARMATURE' and ob.animation_data and ob.animation_data.action:
            action=ob.animation_data.action
            for layer in action.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(ob.animation_data.action_slot)
                    if bag:
                        for fc in bag.fcurves:fc.modifiers.new('CYCLES')
    wrapper.location=(xx,yy,.14);wrapper.rotation_euler.z=math.pi/2
    spec=next(s for s in json.loads((ROOT/'assets/npc_catalog.json').read_text(encoding='utf-8')) if s['id']==kind)
    joints={o.name.split('.')[0]:o for o in added if o.type=='EMPTY'}
    period=round(spec['stepLength']/.6/spec['speed']*24)
    for frame in range(1,period+2):
        phase=(frame-1)/period;hips=spec['hipHeight']+math.cos(phase*math.tau*2)*spec['height']*.003-spec['height']*.012
        joints['Hips'].location.z=hips;joints['Hips'].keyframe_insert(data_path='location',frame=frame)
        for side,offset in [('L',0),('R',.5)]:
            p=(phase+offset)%1;lift=0
            if p<.6:forward=spec['stepLength']*(.5-p/.6)
            else:
                t=(p-.6)/.4;forward=spec['stepLength']*(-.5+t);lift=math.sin(math.pi*t)*spec['height']*(.035 if kind=='elder' else .058)
            down=hips-spec['footHeight']-lift;L1=spec['legUpper'];L2=spec['legLower'];dist=min(math.hypot(down,forward),L1+L2-.0001)
            ha=-math.atan2(forward,down)-math.acos(max(-1,min(1,(L1*L1+dist*dist-L2*L2)/(2*L1*dist))))
            ka=math.pi-math.acos(max(-1,min(1,(L1*L1+L2*L2-dist*dist)/(2*L1*L2))))
            for part,angle in [('UpperLeg',ha),('LowerLeg',ka),('Foot',-ha-ka),('UpperArm',math.cos((phase+offset)*math.tau)*.29),('LowerArm',-.20)]:
                ob=joints[part+'_'+side];ob.rotation_euler.x=angle;ob.keyframe_insert(data_path='rotation_euler',frame=frame)
    for ob in added:
        if ob.animation_data and ob.animation_data.action:
            for layer in ob.animation_data.action.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(ob.animation_data.action_slot)
                    if bag:
                        for fc in bag.fcurves:
                            fc.modifiers.new('CYCLES')
                            for key in fc.keyframe_points:key.interpolation='LINEAR'
    wrapper.keyframe_insert(data_path='location',frame=1);wrapper.location.x+=spec['speed']*599/24;wrapper.keyframe_insert(data_path='location',frame=600)
    if wrapper.animation_data:
        for layer in wrapper.animation_data.action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(wrapper.animation_data.action_slot)
                if bag:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.frame_end=600;scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=115;area.spaces.active.region_3d.view_location=(10,10,12)
scene['gameplay']='第三版：浏览器中有连续昼夜、街区任务和本地存档。小集、公园、光环广场、落日长廊为虚构扩展设计。'
scene['README']='星湾是虚构都市游戏世界。地点、商家与居民均为游戏设定；浏览器提供NPC寻路、等灯与本地Ollama AI。'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'星湾街区.blend'))
if '--skip-preview' not in sys.argv:
    scene.render.filepath=str(ROOT/'场景预览.png');bpy.ops.render.render(write_still=True)
print('SCENE_BUILD_COMPLETE',flush=True)
