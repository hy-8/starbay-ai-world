"""Offline close-up quality study, no UE integration or gameplay claims.
New version required. Replaces coarse locks with actual tapered fibers.
"""
from pathlib import Path
_source=Path(__file__).with_name('build_concert.py').read_text(encoding='utf-8')
_head,_stage=_source.split('# Actual neutral concert studio:')
exec(compile(_head,str(Path(__file__).with_name('build_concert.py')),'exec'))

# Replace the solid ribbon hairstyle, keeping its editable guide design.
for ob in list(COL['05_Hair'].objects):bpy.data.objects.remove(ob,do_unlink=True)
random.seed(930)
guides=[]
for k in range(40):
    a=-1.25+2.5*k/39;s=1 if a>.15 else -1;p0=scalp(.25+.20*random.random(),a/(2*pi))
    p1=p0+Vector((s*.026,-.046,.027+random.random()*.012))
    p2=Vector((p0.x+s*.041,-.166,1.82+random.uniform(-.025,.025)))
    p3=Vector((p0.x+s*.027,-.153,1.736+random.uniform(0,.07)))
    guides.append(([p0,p1,p2,p3],.006+random.random()*.004))
for k in range(85):
    a=1.18+3.92*k/84;p0=scalp(.25+.45*random.random(),a/(2*pi));s=1 if p0.x>0 else -1
    p1=p0+Vector((s*.018,.013,.023));p2=Vector((p0.x*1.35+.012*sin(k),p0.y+.032,p0.z-.075))
    p3=Vector((p0.x*1.27+.008*sin(k),p0.y+.029,p0.z-.12-.12*random.random()))
    guides.append(([p0,p1,p2,p3],.008+random.random()*.003))
fiber_mats=[]
for i,color in enumerate([(.026,.0018,.003),(.014,.0008,.0015),(.043,.0035,.004),(.010,.0005,.0009)]):
    m=bpy.data.materials.new('Auburn physical fiber '+str(i));m.use_nodes=True;n=m.node_tree.nodes;n.clear()
    out=n.new('ShaderNodeOutputMaterial');hairnode=n.new('ShaderNodeBsdfHairPrincipled');hairnode.parametrization='COLOR';hairnode.inputs['Color'].default_value=(*color,1)
    hairnode.inputs['Roughness'].default_value=.42
    if 'Radial Roughness' in hairnode.inputs:hairnode.inputs['Radial Roughness'].default_value=.50
    m.node_tree.links.new(hairnode.outputs[0],out.inputs[0]);fiber_mats.append(m)
scalp_mat=material('Auburn undercut scalp',(.20,.10,.078),0,.8)
surface('Scalp below groom',scalp,27,97,scalp_mat,'05_Hair',.001,1)
paths=[[] for _ in fiber_mats]
for gi,(guide,width) in enumerate(guides):
    count=380 if gi<40 else 260
    centers=bez(guide,60)
    for k in range(count):
        angle=random.uniform(0,2*pi);r=math.sqrt(random.random());ox=cos(angle)*r*width;oy=sin(angle)*r*width*.65
        phase=random.uniform(0,2*pi);end=37+random.randrange(23);strand=[]
        for j,c in enumerate(centers[:end]):
            t=j/59;tan=(centers[min(59,j+1)]-centers[max(0,j-1)]).normalized();cross=tan.cross(Vector((0,1,0))).normalized();norm=tan.cross(cross)
            scatter=.15+.85*(1-t)**1.2;wav=.0005*sin(t*24+phase)*sin(pi*t)
            curl=Vector((.0035*sin(t*11+gi*.7)*sin(pi*t),.002*cos(t*9+gi)*sin(pi*t),0))
            strand.append(c+cross*(ox*scatter+wav)+norm*(oy*scatter+wav*.4)+curl)
        paths[(gi+k)%4].append(strand)
for k in range(12000):
    vv=random.random();start=.015+random.random()*.05;end=.85+random.random()*.15
    paths[k%4].append([scalp(start+(end-start)*j/35,vv)+Vector((0,-.0004,.001)) for j in range(36)])
for i,items in enumerate(paths):batch_curves('Actual auburn groom fibers '+str(i),items,.000047,fiber_mats[i],'05_Hair',True,0)
stubble=[]
for k in range(18000):
    u=.48+.52*random.random();v=random.random();p0=scalp(u,v)
    direction=Vector((p0.x,p0.y+.038,(p0.z-1.773)*.6)).normalized()
    stubble.append([p0,p0+direction*(.0012+random.random()*.0015)])
batch_curves('Fine undercut stubble',stubble,.000045,fiber_mats[1],'05_Hair',True,0)
for ob in list(COL['01_Body'].objects):
    if any(s in ob.name for s in ['Natural eyebrow','Fine upper eyelid']):bpy.data.objects.remove(ob,do_unlink=True)
for m in [leather,boot,glove]:
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=390;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.72
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.00045
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])

# Genuine UV skin details from the explicitly CC0 MakeHuman system pack.
assets=ROOT/'Source/ShowcaseCC0'
image=bpy.data.images.load(str(assets/'skins/young_caucasian_male/young_lightskinned_male_diffuse.png'));image.pack()
nt=skin.node_tree;p=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image
nt.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Subsurface Weight'].default_value=.08;p.inputs['Roughness'].default_value=.45

def fit_proxy(folder,name,mat,group):
    """Apply published MakeHuman barycentric fitting, preserving original UVs."""
    folder=Path(folder);rows=(folder/(name+'.mhclo')).read_text().splitlines();scales=[1,1,1];mapping=[];active=False
    for line in rows:
        q=line.split()
        if not q or q[0].startswith('#'):continue
        if q[0] in ['x_scale','y_scale','z_scale']:
            axis='xyz'.index(q[0][0]);scales[axis]=abs(src[int(q[1])][axis]-src[int(q[2])][axis])/float(q[3])
        elif q[0]=='verts':active=True
        elif active:
            if not q[0].lstrip('-').isdigit():active=False;continue
            if len(q)==1:point=src[int(q[0])].copy()
            elif len(q)==9:
                point=sum((src[int(q[j])]*float(q[j+3]) for j in range(3)),Vector())
                point+=Vector(tuple(float(q[j+6])*scales[j] for j in range(3)))
            else:active=False;continue
            mapping.append(arm_pose(world(point)))
    raw=[];uvs=[];faces=[];uvfaces=[]
    for line in (folder/(name+'.obj')).read_text().splitlines():
        q=line.split()
        if not q:continue
        if q[0]=='v':raw.append(q[1:4])
        elif q[0]=='vt':uvs.append(tuple(map(float,q[1:3])))
        elif q[0]=='f':
            faces.append([int(x.split('/')[0])-1 for x in q[1:]]);uvfaces.append([int(x.split('/')[1])-1 for x in q[1:]])
    assert len(mapping)==len(raw),(len(mapping),len(raw))
    o=mesh('Fitted CC0 '+name,mapping,faces,mat,group,1,0)
    uv=o.data.uv_layers.new(name='SourceGarmentUV')
    for poly,indices in zip(o.data.polygons,uvfaces):
        for li,ti in zip(poly.loop_indices,indices):uv.data[li].uv=uvs[ti]
    if name=='male_elegantsuit01':
        adjacency={i:set() for i in range(len(uvs))}
        for f in uvfaces:
            for a,b in zip(f,f[1:]+f[:1]):adjacency[a].add(b);adjacency[b].add(a)
        seed=min(range(len(uvs)),key=lambda i:(uvs[i][0]-.36)**2+(uvs[i][1]-.975)**2)
        island={seed};pending=[seed]
        while pending:
            for other in adjacency[pending.pop()]:
                if other not in island:island.add(other);pending.append(other)
        assert len(island)==593,'Unexpected tailoring UV topology; inspect source before cutting'
        mask=o.data.attributes.new('SourceShirtPatch','INT','FACE')
        for p,f in zip(o.data.polygons,uvfaces):mask.data[p.index].value=int(f[0] in island)
    return o

# Replace disconnected procedural shirt/shoulder/sleeve tubes with a continuous
# professionally authored CC0 tailoring base, restyled as a longline stage coat.
for group in ['02_Innerwear','03_OuterRobe','06_Regalia']:
    for ob in list(COL[group].objects):
        if group=='02_Innerwear' and any(x in ob.name.lower() for x in ['boot','heel','trouser']):continue
        if group=='06_Regalia' and 'earring' in ob.name.lower():continue
        bpy.data.objects.remove(ob,do_unlink=True)
suit=fit_proxy(assets/'clothes/male_elegantsuit01','male_elegantsuit01',leather,'03_OuterRobe')
# Source object has two disconnected islands: trousers [0,1357), jacket thereafter.
# Identify by connectivity rather than assuming an unrecorded polygon order.
adj={v.index:set() for v in suit.data.vertices}
for edge in suit.data.edges:
    a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for vi in adj:
    if vi in seen:continue
    pending=[vi];seen.add(vi);comp=[]
    while pending:
        vi=pending.pop();comp.append(vi)
        for other in adj[vi]:
            if other not in seen:seen.add(other);pending.append(other)
    components.append(comp)
pants=min(components,key=lambda c:sum(suit.data.vertices[i].co.z for i in c)/len(c));pantset=set(pants)
suit.data.materials.append(trouser);suit.data.materials.append(shirt)
for poly in suit.data.polygons:
    c=sum((suit.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
    if poly.vertices[0] in pantset:poly.material_index=1
    # Material boundary remains UV-defined, not jagged face-center classification.
# Keep the better fitted custom narrow trousers; source pants are inspection only.
bm=bmesh.new();bm.from_mesh(suit.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in pantset],context='VERTS');bm.to_mesh(suit.data);bm.free()
# Remove the exact shirt/tie UV island rather than cutting a jagged spatial mask.
bm=bmesh.new();bm.from_mesh(suit.data);mask=bm.faces.layers.int.get('SourceShirtPatch')
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[mask]],context='FACES');bm.to_mesh(suit.data);bm.free()
# Remove the old short jacket hem instead of stretching its pockets and buttons.
bm=bmesh.new();bm.from_mesh(suit.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_center_median().z<1.082 and abs(f.calc_center_median().x)<.28],context='FACES');bm.to_mesh(suit.data);bm.free()
nappa=material('Wine nappa tailored skirt',(.086,.007,.013),0,.48,fabric=True);setp(nappa,'Sheen Weight',.03);setp(nappa,'Specular IOR Level',.28)
def skirt(u,v):
    a=(.46+.27*u)+(2*pi-2*(.46+.27*u))*v
    fold=.013*u**1.4*sin(a*12+u*3)+.0035*u*sin(a*21-u*5)
    return Vector(((.184+.132*u**1.6+fold)*sin(a),-(.152+.046*u+fold)*cos(a)+.054*u*u,1.09-.94*u+.025*u**5*sin(a*3)))
surface('Separate tailored coat skirt',skirt,93,113,nappa,'03_OuterRobe',.0025,1)
for v in [0,1]:curve('Coat skirt edge stitching',[skirt(j/100,v) for j in range(101)],.00075,seam,'03_OuterRobe')
for s in [-1,1]:
    surface('Stage waist strap',lambda u,v,s=s:Vector((.193*sin(2*pi*v),-.159*cos(2*pi*v)-.006,1.078+.018*u+s*.01)),3,101,boot,'06_Regalia',.002,1)
curve('Small stage belt buckle',[(-.023,-.174,1.067),(.023,-.174,1.067),(.023,-.174,1.111),(-.023,-.174,1.111),(-.023,-.174,1.067)],.002,metal,'06_Regalia')
for row in range(3):
    pts=bez([(.047,-.174,1.079),(.082,-.18,.963-row*.033),(.19,-.102,.98-row*.02),(.185,.008,1.087)],55)
    for j,p0 in enumerate(pts):
        curve('Hip chain individual link',[(p0.x+.0024*cos(a),p0.y+.0013*sin(a),p0.z+.0032*sin(a)) for a in [2*pi*k/10 for k in range(11)]],.0006,metal,'06_Regalia')
# Restore the exposed upper chest from the same licensed body and original UVs.
rawuv=[];bodyfaces=[];bodyuv=[];group0=''
for line in (ROOT/'Source/base.obj').read_text().splitlines():
    q=line.split()
    if not q:continue
    if q[0]=='vt':rawuv.append(tuple(map(float,q[1:3])))
    elif q[0]=='g':group0=q[1]
    elif q[0]=='f' and group0=='body':
        f=[int(x.split('/')[0])-1 for x in q[1:]];c=sum((arm_pose(world(src[i])) for i in f),Vector())/len(f)
        if 1.285<c.z<1.50 and abs(c.x)<.035+.35*(c.z-1.285) and c.y<-.02:bodyfaces.append(f);bodyuv.append([int(x.split('/')[1])-1 for x in q[1:]])
ids=sorted(set(i for f in bodyfaces for i in f));lookup={i:k for k,i in enumerate(ids)}
chest=mesh('Exposed chest at open neckline',[arm_pose(world(src[i])) for i in ids],[[lookup[i] for i in f] for f in bodyfaces],skin,'01_Body',2,0)
layer=chest.data.uv_layers.new(name='MakeHumanUV')
for p,uvf in zip(chest.data.polygons,bodyuv):
    for li,ti in zip(p.loop_indices,uvf):layer.data[li].uv=rawuv[ti]
# A black open-neck inner layer behind the lapels keeps the stage silhouette.
for s in [-1,1]:
    def inner(u,v,s=s):
        z=1.10+.39*u;x=s*(.018+.090*u+.027*v)
        return Vector((x,-.145-.023*sin(pi*u)-.005*v,z))
    surface('Black inner facing',inner,37,9,shirt,'02_Innerwear',.002,1)
# Textile variation from the authored UV texture, recoloured by shader only.
clothtex=bpy.data.images.load(str(assets/'clothes/male_elegantsuit01/male_elegantsuit01_diffuse.png'));clothtex.pack()
for mat,col in [(leather,(.145,.012,.020)),(trouser,(.022,.018,.022)),(shirt,(.016,.013,.016))]:
    nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');t=nt.nodes.new('ShaderNodeTexImage');t.image=clothtex
    grey=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(t.outputs[0],grey.inputs[0])
    mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY_ADD';mul.inputs[1].default_value=1.4;mul.inputs[2].default_value=.55;nt.links.new(grey.outputs[0],mul.inputs[0])
    color=nt.nodes.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=1;color.inputs[1].default_value=(*col,1);nt.links.new(mul.outputs[0],color.inputs[2]);nt.links.new(color.outputs[0],bs.inputs['Base Color'])

# Fit actual modelled corneas/irises, avoiding flat pupils and spherical stickers.
for ob in list(COL['01_Body'].objects):
    if any(x in ob.name.lower() for x in ['sclera','iris','pupil','limbal']):bpy.data.objects.remove(ob,do_unlink=True)
eyemat=material('UV amber-grey anatomical eyes',(.6,.6,.6),0,.22)
eyeob=fit_proxy(assets/'eyes/high-poly','high-poly',eyemat,'01_Body')
im=bpy.data.images.load(str(assets/'eyes/materials/brownlight_eye.png'));im.pack();nt=eyemat.node_tree;tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.links.new(tx.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.links.new(tx.outputs['Alpha'],nt.nodes.get('Principled BSDF').inputs['Alpha']);setp(eyemat,'Coat Weight',.45);setp(eyemat,'Coat Roughness',.08)

# Actual source use, distinct from the larger downloaded inspection subset.
(OUT/'showcase_asset_usage.json').write_text(json.dumps({'skin':'MakeHuman young_lightskinned_male_diffuse.png','tailoring':'MakeHuman male_elegantsuit01, fitted and restyled','eyes':'MakeHuman high-poly, brownlight_eye.png','license':'CC0, explicit mhclo/mhmat headers','hair':'Original guide-based fiber groom','particles':False,'status':'offline visual study, not approved final'},ensure_ascii=False,indent=2),encoding='utf-8')

_stage=_stage.replace("420,(1,.27,.22)","150,(1,.27,.22)").replace("450,(1,.94,.85)","180,(1,.94,.85)")
exec(compile('# Actual neutral concert studio:'+_stage,str(Path(__file__).with_name('build_concert.py')),'exec'))
