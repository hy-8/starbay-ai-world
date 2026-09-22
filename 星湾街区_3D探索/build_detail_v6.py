"""Additive fictional district art. Never overwrites the user's base .blend.
Run with Blender --background --factory-startup --python build_detail_v6.py.
Coordinates in helpers are game X, Z, height; mesh output uses Blender Z-up.
"""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).parent
random.seed(6021)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
M, B, colliders = {}, {}, []

def material(name, color, rough=.8, metal=0, glow=0, texture=None):
    m = bpy.data.materials.new('v6_' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if glow:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = glow
    if texture:
        img = bpy.data.images.new('Starbay original ' + texture, width=128, height=128)
        pixels = []
        rng = random.Random(64)
        for y in range(128):
            for x in range(128):
                value = .8 + rng.random() * .2
                if texture == 'stone':
                    if y % 32 < 2 or (x + (y // 32 % 2) * 32) % 64 < 2: value = .48
                elif texture == 'wood':
                    value *= .83 + .17 * math.sin(x * .45 + math.sin(y * .12))
                    if x % 32 < 2: value = .45
                pixels.extend([min(1, c * value) for c in color] + [1])
        img.pixels[:] = pixels
        img.pack()
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = img
        m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    M[name] = m
    B[name] = [[], []]

for name, color in [('stone',(.47,.40,.30)),('rim',(.69,.63,.48)),('wood',(.32,.17,.08)),('metal',(.07,.12,.11)),('terracotta',(.52,.22,.11)),('cloth',(.78,.68,.44)),('teal',(.065,.25,.22)),('paper',(.85,.77,.56)),('leaf',(.13,.25,.10)),('leaflight',(.25,.36,.13)),('flower',(.68,.26,.19)),('gold',(.73,.53,.21)),('fruit',(.82,.44,.07))]:
    material(name,color,texture=name if name in ['stone','wood'] else None)
material('water',(.06,.29,.29),.17,.35)
material('glow',(1,.63,.24),.4,0,3)

def mesh(name, verts, faces, mat):
    v,f = B[mat]; offset=len(v)
    v.extend([(x,-z,h) for x,z,h in verts])
    # Mapping X,Z,H -> X,-Z,H changes handedness: reverse winding.
    f.extend([tuple(offset+i for i in reversed(face)) for face in faces])

def box(x,z,h,w,d,t,mat):
    a,b,c=w/2,d/2,t/2
    mesh('',[(x+u,z+v,h+s) for u,v,s in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)

def rod(a,b,r,mat,segments=8):
    # Construct in helper coordinate system, converted by mesh().
    va,vb=Vector(a),Vector(b); delta=vb-va
    q=delta.to_track_quat('Z','Y'); verts=[]
    for h in [0,delta.length]:
        for i in range(segments):
            verts.append(tuple(va+q@Vector((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),h))))
    faces=[tuple(range(segments-1,-1,-1)),tuple(range(segments,segments*2))]+[(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
    mesh('',verts,faces,mat)

def ball(x,z,h,sx,sz,sh,mat):
    verts=[];faces=[];n=10;k=6
    for j in range(k+1):
        for i in range(n):
            a=i*math.tau/n;b=j*math.pi/k
            verts.append((x+sx*math.cos(a)*math.sin(b),z+sz*math.sin(a)*math.sin(b),h+sh*math.cos(b)))
    for j in range(k):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
    mesh('',verts,faces,mat)

def collider(x,z,w,d): colliders.append(dict(x=x,z=z,w=w,d=d))
def label(words,x,z,h,size=.3,mat='paper'):
    cu=bpy.data.curves.new('v6_sign','FONT');cu.body=words;cu.size=size;cu.align_x='CENTER';cu.extrude=.003
    if font:cu.font=font
    ob=bpy.data.objects.new('v6_'+words,cu);bpy.context.collection.objects.link(ob)
    ob.location=(x,-z,h);ob.rotation_euler=(math.pi/2,0,math.pi);cu.materials.append(M[mat])

font=None
try:font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc')
except RuntimeError:pass

def planter(x,z,w=2.2,d=1.3):
    box(x,z,.42,w,d,.62,'rim');box(x,z,.74,w-.16,d-.16,.07,'wood');collider(x,z,w,d)
    for _ in range(12):
        px=x+random.uniform(-w*.4,w*.4);pz=z+random.uniform(-d*.35,d*.35)
        ball(px,pz,.98,.32,.28,random.uniform(.2,.45),'leaflight' if random.random()<.35 else 'leaf')
        if random.random()<.55:ball(px,pz,1.23,.09,.09,.10,'flower')

def bench(x,z):
    collider(x,z,3,.8)
    for dx in [-1.1,1.1]:
        box(x+dx,z,.36,.13,.72,.52,'metal')
        box(x+dx,z+.3,.89,.12,.12,1.1,'metal')
    for dz in [-.25,-.08,.09,.26]:box(x,z+dz,.63,3,.13,.09,'wood')
    for h in [.89,1.08]:box(x,z+.3,h,3,.08,.15,'wood')

def tree(x,z,height=6):
    collider(x,z,.7,.7)
    rod((x,z,.1),(x+.1,z,height*.75),.16,'wood')
    for i in range(8):
        angle=i*2.399;radius=1.0 if i<5 else .55
        xx=x+math.sin(angle)*radius;zz=z+math.cos(angle)*radius;hh=height*.68+(i%3)*.48
        rod((x,z,height*.4),(xx,zz,hh),.055,'wood',6)
        # Individual folded leaf silhouettes keep the crown porous and cast fine shadows.
        # No opaque spheres: the foliage remains inspectable geometry in both Blender and UE.
        for j in range(130):
            angle=random.random()*math.tau
            vertical=random.uniform(-1,1);radius=random.random()**(1/3)
            ring=math.sqrt(1-vertical*vertical)
            p=Vector((xx+math.cos(angle)*radius*ring*1.15,zz+math.sin(angle)*radius*ring*.95,hh+vertical*radius*.9))
            q=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.4,1))).normalized().to_track_quat('Z','Y')
            length=random.uniform(.16,.30);width=length*.38
            leaf=[(-length,0,0),(-length*.28,width,0),(length*.48,width*.7,0),(length,0,0),(length*.48,-width*.7,0),(-length*.28,-width,0),(0,0,.035)]
            mesh('',[tuple(p+q@Vector(v)) for v in leaf],[(k,(k+1)%6,6) for k in range(6)],'leaflight' if j%3==0 else 'leaf')

def stringlights(a,b):
    points=[]
    for i in range(25):
        t=i/24
        points.append((a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t-.6*math.sin(math.pi*t)))
    for p,q in zip(points,points[1:]):rod(p,q,.018,'metal',5)
    for i,p in enumerate(points):
        if i%2==0:
            rod(p,(p[0],p[1],p[2]-.19),.016,'metal',5)
            ball(p[0],p[1],p[2]-.25,.065,.065,.09,'glow')

# The new courtyard sits between existing routes, clear of residential footprints.
box(68,45,.135,24,17,.04,'stone')
for x in [56.3,79.7]:box(x,45,.17,.16,17,.06,'rim')
for z in [36.6,53.4]:box(68,z,.17,24,.16,.06,'rim')
# Fountain rim built as an actual open ring, not a solid water-colored cylinder.
for i in range(64):
    a=i*math.tau/64;b=(i+1)*math.tau/64
    rod((68+math.cos(a)*2.4,46+math.sin(a)*2.4,.55),(68+math.cos(b)*2.4,46+math.sin(b)*2.4,.55),.19,'rim')
rod((68,46,.15),(68,46,.40),2.23,'water',64)
rod((68,46,.4),(68,46,1.38),.21,'stone',16)
rod((68,46,1.37),(68,46,1.47),.66,'rim',32)
collider(68,46,5.2,5.2)
for x in [59,76]:bench(x,51.1)
# Timber pergola with trellis, ivy and warm pendants.
for x in [57,79]:
    for z in [40,52]:
        box(x,z,2.05,.22,.22,3.9,'wood');collider(x,z,.3,.3)
for z in [40,52]:box(68,z,4.1,22.5,.22,.30,'wood')
for x in [57,79]:box(x,46,4.16,.20,12.6,.24,'wood')
for z in [40,41,42,50,51,52]:box(68,z,4.3,22.4,.10,.12,'wood')
stringlights((57,40,4.3),(79,40,4.3));stringlights((57,52,4.3),(79,52,4.3))
for x in [57.2,78.8]:
    for z in [40.1,51.8]:
        for h in [1.6,2.2,2.8,3.4,4]:ball(x,z,h,.37,.34,.4,'leaf')
for x,z in [(55,38),(81,39),(55,51),(81,52)]:tree(x,z,6.4)
for x,z in [(59,37.6),(76,37.6),(64,52.4),(72,52.4)]:planter(x,z,2.4,1.2)
box(72.5,40,2.85,5.8,.16,1.0,'teal');label('风 栖 茶 庭',72.5,39.9,2.9,.54)
label('SLOW DOWN / STAY A WHILE',72.5,39.9,2.57,.16)
# Story desk near the new POI, with cups, open notebook and tea canisters.
box(59.2,44.8,.92,1.7,.9,.1,'wood');collider(59.2,44.8,1.8,1)
for dx in [-.7,.7]:box(59.2+dx,44.8,.52,.1,.65,.8,'metal')
box(59,44.8,.99,.55,.35,.025,'paper')
for x in [59.4,59.7]:rod((x,44.7,1),(x,44.7,1.16),.07,'terracotta',12)

# Night market: suspended bulbs, bunting, actual produce, crates and a chalk menu.
for x in [-120,-90]:
    rod((x,26.9,.1),(x,26.9,4.5),.075,'metal');collider(x,26.9,.25,.25)
stringlights((-120,26.9,4.5),(-90,26.9,4.5))
for i in range(15):
    x=-119+i*2
    mesh('',[(x,27,3.8),(x+.65,27,3.8),(x+.32,27,3.17)],[(0,1,2)],'cloth' if i%2 else 'teal')
for x in [-115,-105,-95]:
    for xx in [-1.4,-.5,.5,1.4]:
        box(x+xx,29.1,1.48,.7,.55,.17,'wood')
        for _ in range(7):ball(x+xx+random.uniform(-.23,.23),29.1+random.uniform(-.16,.16),1.65,.1,.09,.1,'fruit' if xx<0 else 'flower')
    for dx in [-2.7,2.7]:
        box(x+dx,32,.38,.8,.7,.6,'wood');collider(x+dx,32,.9,.8)
        for off in [-.2,0,.2]:box(x+dx+off,31.64,.4,.06,.035,.48,'rim')
    box(x,31.95,2.45,2.8,.12,.5,'teal')
box(-110,27.3,.85,.8,.12,1.3,'metal');collider(-110,27.3,.85,.3)
label('今日花事\n鲜花 · 热茶\n日落后亮灯',-110,27.22,1.18,.13)
planter(-122,31,2,2);planter(-87,31,2,2)

# Small human traces in the park and along the promenade, outside walking lines.
for x,z in [(-2.4,40),(20.4,47),(97,-36),(99,-43)]:tree(x,z,5.8)
for x,z in [(1,37),(17,49),(100,-23),(106,-44)]:planter(x,z,1.6,1.1)
for x,z in [(3,48),(105,-38)]:
    box(x-.4,z,.72,.42,.28,.04,'paper')
    rod((x+.6,z,.70),(x+.6,z,.87),.065,'terracotta',12)
for z in [-25,-30,-35,-40]:
    rod((107.7,z,1.25),(107.7,z,2.2),.035,'metal')
    ball(107.7,z,2.25,.11,.11,.16,'glow')
# Courtyard-facing windows, shallow wall planter ledges and signs give the podium scale.
for x in [51,55,59,63,67,71]:
    box(x,56.43,2.15,3.3,.08,3.4,'teal')
    box(x,56.30,.5,3.4,.35,.16,'wood')
    for dx in [-1.6,0,1.6]:box(x+dx,56.25,2.12,.065,.08,3.5,'metal')
    box(x,56.24,3.91,3.8,.8,.12,'cloth')
label('风 栖 茶 社   /   邻 里 读 书 会',61,56.18,4.5,.48)

# Build one mesh per material with world-projected UVs: compact draw-call count.
for name,(verts,faces) in B.items():
    if not verts:continue
    me=bpy.data.meshes.new('v6_'+name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
    ob=bpy.data.objects.new('v6_'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(M[name])
    uv=me.uv_layers.new(name='UVMap')
    for face in me.polygons:
        normal=face.normal;axis=max(range(3),key=lambda i:abs(normal[i]))
        axes=[i for i in range(3) if i!=axis]
        for loop in face.loop_indices:
            v=me.vertices[me.loops[loop].vertex_index].co
            uv.data[loop].uv=(v[axes[0]]*.7,v[axes[1]]*.7)

out=ROOT/'assets';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(out/'district_detail_v6.glb'),export_format='GLB',export_animations=False)
(out/'district_detail_v6.json').write_text(json.dumps({'version':6,'colliders':colliders,'courtyard':[62,43],'source':'build_detail_v6.py','baseUnchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'星湾_第六版增量场景.blend'))
# Save a separate full scene for inspection; original base remains intact.
base=ROOT/'星湾街区.blend'
if base.exists():
    bpy.ops.wm.open_mainfile(filepath=str(base))
    bpy.ops.import_scene.gltf(filepath=str(out/'district_detail_v6.glb'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'星湾街区_第六版场景.blend'))
print('STARBAY_V6_DETAIL_OK',len(colliders))
