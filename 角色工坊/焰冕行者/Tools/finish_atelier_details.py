"""Fit licensed sewn leather boots and refine face for the selected atelier study."""
import bpy,bmesh,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1];OUT=ROOT/'Exports'/VERSION
if OUT.exists():raise RuntimeError('Fresh candidate required')
OUT.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier04/Ember_Regent.blend'))
group=bpy.data.collections['02_Innerwear']
src=[]
for line in (ROOT/'Source/base.obj').read_text().splitlines():
    q=line.split()
    if q and q[0]=='v':src.append(Vector(tuple(map(float,q[1:4]))))
for line in (ROOT/'Source/male_young.target').read_text().splitlines():
    q=line.split()
    if len(q)==4 and q[0].isdigit():src[int(q[0])]+=Vector(tuple(map(float,q[1:4])))
folder=ROOT/'Source/FootwearCCBY/clothes/mindfront_shoes_biker_boots_male'
clo=folder/'mindfront_shoes_biker_boots_male.mhclo';text=clo.read_text()
if '# license CC BY 4.0' not in text:raise RuntimeError('Expected explicit license absent')
mapping=[];scales=[1,1,1];active=False
for line in text.splitlines():
    q=line.split()
    if not q or q[0].startswith('#'):continue
    if q[0] in ['x_scale','y_scale','z_scale']:
        ax='xyz'.index(q[0][0]);scales[ax]=abs(src[int(q[1])][ax]-src[int(q[2])][ax])/float(q[3])
    elif q[0]=='verts':active=True
    elif active:
        if not q[0].lstrip('-').isdigit():active=False;continue
        if len(q)==9:
            p=sum((src[int(q[j])]*float(q[j+3]) for j in range(3)),Vector())+Vector(tuple(float(q[j+6])*scales[j] for j in range(3)))
        elif len(q)==1:p=src[int(q[0])].copy()
        else:active=False;continue
        mapping.append(Vector((p.x*.115,-p.z*.115,(p.y+8.188)*.115)))
uvs=[];faces=[];uvfaces=[];count=0
for line in (folder/'shoes_biker_boots_male.obj').read_text().splitlines():
    q=line.split()
    if not q:continue
    if q[0]=='v':count+=1
    elif q[0]=='vt':uvs.append(tuple(map(float,q[1:3])))
    elif q[0]=='f':faces.append([int(x.split('/')[0])-1 for x in q[1:]]);uvfaces.append([int(x.split('/')[1])-1 for x in q[1:]])
assert count==len(mapping)
for side in [-1,1]:
    selected=[v for v in mapping if v.x*side>0];cx=(min(v.x for v in selected)+max(v.x for v in selected))/2
    low=min(v.z for v in selected)
    for v in selected:v.x+=side*.149-cx;v.z+=.004-low
for ob in list(group.objects):
    if any(w in ob.name.lower() for w in ['boot','heel','lace']):bpy.data.objects.remove(ob,do_unlink=True)
me=bpy.data.meshes.new('Mindfront biker boots fitted');me.from_pydata(mapping,[],faces);me.update();ob=bpy.data.objects.new('Fitted sewn leather boots - Mindfront CC BY 4.0',me);group.objects.link(ob)
layer=me.uv_layers.new(name='BootSourceUV')
for poly,uvface in zip(me.polygons,uvfaces):
    poly.use_smooth=True
    for li,ti in zip(poly.loop_indices,uvface):layer.data[li].uv=uvs[ti]
mat=bpy.data.materials.new('Sewn black leather boot PBR');mat.use_nodes=True;nt=mat.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.56;p.inputs['Specular IOR Level'].default_value=.3
for image_name,socket in [('Shoes_Biker_Boots.png','Base Color'),('Shoes_Biker_Boots_NRM.png','Normal')]:
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(folder/image_name));tx.image.pack()
    if socket=='Normal':
        tx.image.colorspace_settings.name='Non-Color';nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65;nt.links.new(tx.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs[0],p.inputs[socket])
    else:nt.links.new(tx.outputs['Color'],p.inputs[socket])
me.materials.append(mat)
for o in group.objects:
    if o.type=='MESH' and 'Tailored trouser' in o.name:
        for v in o.data.vertices:
            blend=max(0,min(1,(.43-v.co.z)/.13));side=1 if v.co.x>0 else -1
            v.co.x=side*.149+(v.co.x-side*.149)*(1-.20*blend);v.co.y*=1-.20*blend

# Slightly stronger lower jaw and a darker natural iris; no painted facial detail.
body=max((o for o in bpy.data.collections['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
for v in body.data.vertices:
    x,y,z=v.co
    if 1.625<z<1.708:
        weight=math.exp(-((z-1.663)/.027)**2)*max(0,min(1,(-y+.03)/.11));v.co.x*=1+.055*weight
eyemat=bpy.data.materials.get('UV amber-grey anatomical eyes')
for n in eyemat.node_tree.nodes:
    if n.type=='TEX_IMAGE':n.image=bpy.data.images.load(str(ROOT/'Source/ShowcaseCC0/eyes/materials/brown_eye.png'));n.image.pack()

# A narrow clipped trouser spot was visible through the upper skirt; remove only
# covered trouser faces outside its actual envelope above mid-thigh.
for o in group.objects:
    if o.type=='MESH' and 'Tailored trouser' in o.name:
        for v in o.data.vertices:
            if .78<v.co.z<1.03:v.co.x*=.96

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
(OUT/'asset_usage.json').write_text(json.dumps({'source':'atelier04','groom':'original native curves retained after authored-template comparison failed visual fitting','boots':{'author':'Mindfront (Sweden)','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','source':'https://static.makehumancommunity.org/assets/assetpacks/shoes03.html','original':'Shoes_Biker_Boots_male','changes':'barycentric fitting, stance alignment, Blender material conversion','notice':'Attribution must accompany redistribution or published artwork'},'eyes':'CC0 MakeHuman brown_eye.png','status':'offline character study; pose/render follows separately'},ensure_ascii=False,indent=2),encoding='utf-8')
print('DETAILS_SAVED',str(OUT),flush=True)
