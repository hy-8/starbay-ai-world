"""Actual offline Blender editorial studies. Preserve all earlier candidates.

Run: blender --background --python build_editorial_still.py -- concert10 --draft
Uses declared CC0 fitting sources; no image-generation substitution.
"""
from pathlib import Path

refine = Path(__file__).with_name('refine_concert_showcase.py').read_text(encoding='utf-8')
# Reuse the verified UV/body/tailoring work without constructing the rejected groom.
start = refine.index('# Replace the solid ribbon hairstyle')
end = refine.index('for ob in list(COL[\'01_Body\'].objects):', start)
refine = refine[:start] + "for ob in list(COL['05_Hair'].objects):bpy.data.objects.remove(ob,do_unlink=True)\n" + refine[end:]
refine = refine.split('# Actual source use, distinct')[0]
exec(compile(refine, str(Path(__file__).with_name('refine_concert_showcase.py')), 'exec'))

def alpha_texture_material(name, path, dark, light, roughness=.5):
    mat=material(name,dark,0,roughness)
    nt=mat.node_tree;p=nt.nodes.get('Principled BSDF')
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(path));tx.image.pack()
    bw=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(tx.outputs['Color'],bw.inputs[0])
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.02;ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].position=.60;ramp.color_ramp.elements[1].color=(*light,1)
    nt.links.new(bw.outputs[0],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
    nt.links.new(tx.outputs['Alpha'],p.inputs['Alpha'])
    p.inputs['Specular IOR Level'].default_value=.25
    return mat

hairmat=alpha_texture_material('Auburn layered hair cards CC0 derivative',assets/'hair/short02/short02_diffuse.png',(.012,.0015,.002),(.19,.029,.033),.58)
setp(hairmat,'Anisotropic',.35);setp(hairmat,'Specular IOR Level',.16)
nt=hairmat.node_tree
normal_tex=nt.nodes.new('ShaderNodeTexImage');normal_tex.image=bpy.data.images.load(str(assets/'hair/short02/short02_normal.png'));normal_tex.image.colorspace_settings.name='Non-Color';normal_tex.image.pack()
nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7;nt.links.new(normal_tex.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal'])
hair_ob=fit_proxy(assets/'hair/short02','short02',hairmat,'05_Hair')
for mod in list(hair_ob.modifiers):hair_ob.modifiers.remove(mod)
# Lift away from the scalp without the separate hard-edged cap of the prior study.
for v in hair_ob.data.vertices:
    c=v.co;c.x*=1.035;c.y=-.033+(c.y+.033)*1.025;c.z=1.76+(c.z-1.76)*1.025

# Sparse layered strands over the textured root mass. Each strand keeps its own
# width/length; there are no opaque tapered tubes masquerading as hair locks.
fiber_mats=[]
for k,col in enumerate([(.045,.006,.008),(.085,.012,.015),(.025,.0025,.004)]):
    mat=bpy.data.materials.new('Editorial auburn fiber '+str(k));mat.use_nodes=True
    nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');h=nt.nodes.new('ShaderNodeBsdfHairPrincipled');h.parametrization='COLOR'
    h.inputs['Color'].default_value=(*col,1);h.inputs['Roughness'].default_value=.55;h.inputs['Radial Roughness'].default_value=.62
    nt.links.new(h.outputs[0],out.inputs[0]);fiber_mats.append(mat)
random.seed(1002);strand_paths=[[],[],[]]
bpy.context.view_layer.update();hair_bvh=BVHTree.FromObject(hair_ob,bpy.context.evaluated_depsgraph_get())
groom_guides=[]
for side in [-1,1]:
    for k in range(15):
        f=k/14
        x=.012+side*.014;y=-.065+.13*f
        root0,_,_,_=hair_bvh.ray_cast(Vector((x,y,2.1)),Vector((0,0,-1)),.4)
        if root0 is None:continue
        root0.z-=.004
        groom_guides.append(([root0,root0+Vector((side*.055,-.028,.012)),(side*(.10+.017*f),-.170+.15*f,1.80-.018*f),(side*(.068+.042*f),-.152+.18*f,1.737-.095*f)],.0035))
    for k in range(11):
        f=k/10
        p0,_,_,_=hair_bvh.ray_cast(Vector((side*.065,.010+.06*f,2.1)),Vector((0,0,-1)),.5)
        if p0 is None:continue
        p0.z-=.006
        groom_guides.append(([p0,(side*.108,.027+.05*f,1.81),(side*.115,.052+.046*f,1.68),(side*(.11+.015*sin(k)),.067+.055*f,1.61+.033*cos(k))],.0035))
for gi,(guide,width) in enumerate(groom_guides):
    centers=bez(guide,49)
    for k in range(70):
        shift=(random.random()-.5)*2*width;depth=(random.random()-.5)*.0025;phase=random.random()*2*pi;end=random.randrange(36,49);path=[]
        for j,c in enumerate(centers[:end]):
            t=j/48;tan=(centers[min(j+1,48)]-centers[max(0,j-1)]).normalized();across=tan.cross(Vector((0,1,0))).normalized();normal=tan.cross(across)
            wave=.0018*sin(t*12+gi*.5)*sin(pi*t)+.0003*sin(t*28+phase)
            path.append(c+across*(shift+wave)+normal*(depth+.001*sin(pi*t*2+phase)*sin(pi*t)))
        strand_paths[(k+gi)%3].append(path)
for i,paths in enumerate(strand_paths):
    # Match the root cards under studio lights; the prior physical-fiber test was
    # substantially overbright relative to the card base.
    fm=material('Auburn flyaway satin '+str(i),[(.025,.002,.004),(.040,.004,.006),(.013,.001,.002)][i],0,.58)
    setp(fm,'Specular IOR Level',.20)
    batch_curves('Editorial layered hair strands '+str(i),paths,.000035,fm,'05_Hair',True,1)

browmat=alpha_texture_material('Soft dark auburn eyebrow cards',assets/'eyebrows/eyebrow002/eyebrow002.png',(.016,.006,.005),(.055,.013,.01),.65)
brows=fit_proxy(assets/'eyebrows/eyebrow002','eyebrow002',browmat,'01_Body')
for mod in list(brows.modifiers):brows.modifiers.remove(mod)
bpy.context.view_layer.update();face_bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
for v in brows.data.vertices:
    hit,normal,_,_=face_bvh.ray_cast(Vector((v.co.x,-.5,v.co.z)),Vector((0,1,0)),.5)
    if hit is not None:v.co=hit+Vector((0,-.00065,0))

# A proper complete inner garment replaces the two unsupported black strips.
for ob in list(COL['02_Innerwear'].objects):
    if 'Black inner facing' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
inner_mat=material('Washed black silk inner shirt',(.012,.011,.014),0,.48,fabric=True)
setp(inner_mat,'Sheen Weight',.16)
def open_shirt(u,v):
    a=2*pi*v;front=max(0,cos(a));top=1.524-.185*front**3
    z=1.071+(top-1.071)*u
    f=(z-1.071)/.453
    rx=.146+.061*f;ry=.12+.024*sin(f*pi*.8)
    fold=.0015*sin(a*12+f*18)*sin(pi*u)
    return Vector(((rx+fold)*sin(a),-.009-(ry+fold)*cos(a),z))
shirt_faces=[];group0=''
for line in (ROOT/'Source/base.obj').read_text().splitlines():
    q=line.split()
    if not q:continue
    if q[0]=='g':group0=q[1]
    elif q[0]=='f' and group0=='body':
        f=[int(x.split('/')[0])-1 for x in q[1:]];c=sum((arm_pose(world(src[i])) for i in f),Vector())/len(f)
        if not (1.067<c.z<1.537 and abs(c.x)<.237):continue
        if c.y<-.04 and c.z>1.32 and abs(c.x)<(c.z-1.32)*.58:continue
        shirt_faces.append(f)
shirt_ids=sorted({i for f in shirt_faces for i in f});shirt_lookup={i:k for k,i in enumerate(shirt_ids)}
shirt_verts=[]
for i in shirt_ids:
    c=arm_pose(world(src[i]));c+=Vector((c.x*1.0,(c.y+.012)*1.5,0)).normalized()*.001;shirt_verts.append(c)
inner=mesh('Anatomically fitted open black shirt',shirt_verts,[[shirt_lookup[i] for i in f] for f in shirt_faces],inner_mat,'02_Innerwear',2,.0015)
curve('Inner placket seam',[(0,-.144,1.105),(0,-.151,1.23),(0,-.159,1.36),(0,-.135,1.437)],.0013,inner_mat,'02_Innerwear')
for z,y in [(1.15,-.154),(1.235,-.160),(1.32,-.162)]:
    uv('Black shirt gunmetal button',(0,y,z),(.0026,.0013,.0026),metal,'02_Innerwear',16)

# Skin uses real albedo, plus a restrained vertex make-up mask rather than flat tint.
nt=skin.node_tree;p=nt.nodes.get('Principled BSDF')
p.inputs['Roughness'].default_value=.48;p.inputs['Subsurface Weight'].default_value=.075
for n in nt.nodes:
    if n.type=='BUMP':n.inputs['Strength'].default_value=.11;n.inputs['Distance'].default_value=.00016
makeup=body.data.color_attributes.new(name='EditorialComplexion',type='FLOAT_COLOR',domain='POINT')
for v in body.data.vertices:
    x,y,z=v.co;front=max(0,min(1,(-y-.095)/.045))
    lip=math.exp(-((x/.027)**6+((z-1.668)/.005)**4))*front
    lid=math.exp(-(((abs(x)-.035)/.026)**4+((z-1.754)/.009)**4))*front
    c=Vector((1,1,1)).lerp(Vector((.75,.41,.43)),lip*.65).lerp(Vector((.45,.36,.40)),lid*.27)
    makeup.data[v.index].color=(*c,1)
tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE')
at=nt.nodes.new('ShaderNodeVertexColor');at.layer_name='EditorialComplexion'
mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
nt.links.new(tex.outputs['Color'],mix.inputs[1]);nt.links.new(at.outputs['Color'],mix.inputs[2]);nt.links.new(mix.outputs[0],p.inputs['Base Color'])
# The separate chest patch has its own topology and therefore needs the same
# named attribute; missing vertex colours would otherwise create black holes.
chest_attr=chest.data.color_attributes.new(name='EditorialComplexion',type='FLOAT_COLOR',domain='POINT')
for item in chest_attr.data:item.color=(1,1,1,1)

# Fine tailoring details conform to the continuous jacket surface.
bpy.context.view_layer.update();jacket_bvh=BVHTree.FromObject(suit,bpy.context.evaluated_depsgraph_get())
def on_jacket(x,z,lift=.0015):
    hit,normal,_,_=jacket_bvh.ray_cast(Vector((x,-.6,z)),Vector((0,1,0)),1)
    return hit+Vector((0,-lift,0)) if hit is not None else None

for side in [-1,1]:
    # Panels of branching embroidered cord, irregular enough to read as clothing.
    paths=[]
    for row in range(7):
        z=1.17+row*.044;x=side*(.094+.017*sin(row*.52))
        pts=[]
        for j in range(33):
            t=j/32;p=on_jacket(x+side*.040*t,z+.023*sin(pi*t))
            if p is not None:pts.append(p)
        if len(pts)>4:paths.append(pts)
        for sign in [-1,1]:
            pts=[]
            for j in range(19):
                t=j/18;p=on_jacket(x+side*(.013+.020*t),z+.018+sign*.011*sin(pi*t))
                if p is not None:pts.append(p)
            if len(pts)>4:paths.append(pts)
    batch_curves('Subtle raised oxblood chest embroidery',paths,.00065,seam,'03_OuterRobe',False,1)
    # Narrow shoulder epaulette with actual surface contact, no fantasy spikes.
    for k in range(3):
        pts=[]
        for j in range(28):
            t=j/27;p=on_jacket(side*(.175+.075*t),1.478+k*.015-.020*t,.003)
            if p is not None:pts.append(p)
        if len(pts)>4:
            curve('Shoulder inset cord',pts,.0013,metal,'06_Regalia')
            for p0 in [pts[0],pts[-1]]:uv('Shoulder small fastening',p0,(.003,.0015,.003),metal,'06_Regalia',12)

# Two short chain necklaces and a modest cut metal pendant.
for side in [-1,1]:
    for row in range(2):
        pts=bez([(side*.059,-.083,1.543),(side*.064,-.152,1.492),(side*.034,-.175,1.447-row*.035),(0,-.166,1.426-row*.035)],42)
        for j,c in enumerate(pts):
            curve('Neck chain link',[(c.x+.0015*cos(a),c.y+.0009*sin(a),c.z+.0022*sin(a)) for a in [2*pi*k/9 for k in range(10)]],.00042,metal,'06_Regalia')
pendant=mesh('Brushed silver pendant',[(-.008,-.170,1.393),(0,-.173,1.401),(.008,-.170,1.393),(0,-.174,1.372)],[(0,1,2,3)],metal,'06_Regalia',0,.002)
mod=pendant.modifiers.new('Soft metal edges','BEVEL');mod.width=.001;mod.segments=3

bpy.context.view_layer.update()
chest_surfaces=[BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get()) for o in [body,chest,inner]]
def chain_surface(c):
    found=[]
    for bv in chest_surfaces:
        hit,_,_,_=bv.ray_cast(Vector((c.x,-.5,c.z)),Vector((0,1,0)),.7)
        if hit is not None:found.append(hit.y)
    if found:c.y=min(found)-.003
    return c
for ob in COL['06_Regalia'].objects:
    if ob.name.startswith('Neck chain link'):
        for sp in ob.data.splines:
            for p0 in sp.points:p0.co=(*chain_surface(Vector(p0.co[:3])),1)
    elif ob==pendant:
        for v in ob.data.vertices:v.co=chain_surface(v.co.copy())

# Deliberate restrained edge pattern on the red skirt, following its geometry.
for side in [0,1]:
    for k in range(3):
        vv=.018+k*.009 if side==0 else .982-k*.009
        pts=[skirt(.03+.92*j/130,vv)+Vector((0,-.0015,0)) for j in range(131)]
        curve('Skirt triple stitched facing',pts,.00065,seam,'03_OuterRobe')
    for k in range(12):
        u=.10+k*.065;vv=.055 if side==0 else .945
        paths=[]
        for sign in [-1,1]:
            paths.append([skirt(u+.022*sin(pi*t),vv+sign*.007*sin(2*pi*t))+Vector((0,-.002,0)) for t in [j/24 for j in range(25)]])
        batch_curves('Tone-on-tone stitched motif',paths,.00055,seam,'03_OuterRobe',False,1)

# Verifiable source use and editable scene, without introducing a game-ready claim.
(OUT/'showcase_asset_usage.json').write_text(json.dumps({
    'skin':'MakeHuman young_lightskinned_male_diffuse.png',
    'tailoring':'MakeHuman male_elegantsuit01; fitted, cut and extended',
    'eyes':'MakeHuman high-poly and brownlight_eye.png',
    'hair':'MakeHuman short02 cards and normal map; original layered curve strands, auburn shader recolour',
    'eyebrows':'MakeHuman eyebrow002; fitted to morphed face',
    'license':'CC0; explicit headers and hashes in Source/showcase_cc0_sources.json',
    'original_additions':'long coat skirt, inner shirt, tailoring details, jewellery, trousers, boots',
    'particles':False,'status':'offline study; requires visual review'
},ensure_ascii=False,indent=2),encoding='utf-8')

# Reuse the neutral three-view stage. The draft flag is exclusively a sample count.
_stage=_stage.replace('420,(1,.27,.22)','140,(1,.27,.22)').replace('450,(1,.94,.85)','180,(1,.94,.85)')
exec(compile('# Actual neutral concert studio:'+_stage,str(Path(__file__).with_name('build_concert.py')),'exec'))
