"""Redline concert wardrobe, real geometry, no magical FX. Versioned Blender source.

Uses the declared CC0 body foundation and its licensed morphs. The reference is
visual guidance only; it is neither projected onto the model nor redistributed.
Run background Blender --python this.py -- concert01 [--draft].
"""
from pathlib import Path
import sys
_couture=Path(__file__).with_name('build_couture.py').read_text(encoding='utf-8')
# Reuse the independently editable face foundation, not the old costume.
exec(compile(_couture.split('# Smooth interpolation helper')[0],str(Path(__file__).with_name('build_couture.py')),'exec'))
random.seed(929)
for o in list(bpy.data.objects):
    if o.hide_render: bpy.data.objects.remove(o,do_unlink=True)

leather=material('Concert oxblood leather',(.105,.009,.016),0,.37,fabric=True)
lining=material('Concert wine satin',(.17,.012,.023),0,.46,fabric=True)
shirt=material('Concert black silk',(.013,.012,.017),0,.46,fabric=True)
trouser=material('Concert charcoal trousers',(.017,.014,.018),0,.53,fabric=True)
boot=material('Concert polished black leather',(.009,.007,.009),0,.29)
sole=material('Concert rubber sole',(.004,.004,.005),0,.68)
metal=material('Concert antiqued silver',(.31,.27,.24),.85,.30)
seam=material('Concert red stitching',(.16,.025,.025),0,.62)
glove=material('Concert gloves',(.014,.010,.012),0,.39)
hairmats=[material('Concert auburn hair '+str(i),c,0,.37) for i,c in enumerate([(.10,.009,.014),(.16,.017,.025),(.22,.026,.032),(.065,.004,.009)])]
for m in hairmats:setp(m,'Anisotropic',.6)
for m in [leather,lining,shirt,trouser]:
    setp(m,'Sheen Weight',.06);setp(m,'Specular IOR Level',.25)
setp(leather,'Roughness',.48)
for m in hairmats:setp(m,'Roughness',.46)
setp(brow,'Base Color',(.048,.009,.012,1))
setp(iris,'Base Color',(.14,.11,.069,1));setp(iris,'Metallic',0)
setp(eye,'Base Color',(.68,.65,.61,1))
setp(skin,'Roughness',.43);setp(skin,'Subsurface Weight',.10)

# A slimmer lower face, softly defined lips and actual vertex complexion.
for v in body.data.vertices:
    x,y,z=v.co
    if z>1.61:
        jaw=math.exp(-((z-1.653)/.040)**2)
        v.co.x*=1-.055*jaw
    front=max(0,min(1,(-y-.08)/.065))
    lips=math.exp(-((x/.028)**6+((z-1.668)/.0049)**4))*front
    cheeks=math.exp(-(((abs(x)-.052)/.027)**2+((z-1.706)/.031)**2))*front
    under=math.exp(-(((abs(x)-.035)/.024)**4+((z-1.739)/.008)**2))*front
    base=Vector((.64,.465,.402)).lerp(Vector((.60,.30,.28)),cheeks*.24)
    base=base.lerp(Vector((.31,.083,.083)),lips*.82).lerp(Vector((.28,.15,.145)),under*.16)
    colors.data[v.index].color=(*base,1)
body.data.materials.append(glove)
for p in body.data.polygons:
    c=p.center
    if abs(c.x)>.32 and c.z<1.22:p.material_index=len(body.data.materials)-1
# Shoulder yoke is fitted from the actual anatomical surface, avoiding a floating
# tube opening. Its own mesh remains independently editable.
yoke=body.copy();yoke.data=body.data.copy();COL['03_OuterRobe'].objects.link(yoke);yoke.name='Anatomically fitted shoulder yoke'
bm=bmesh.new();bm.from_mesh(yoke.data)
keep=[]
for f in bm.faces:
    p=f.calc_center_median()
    if not (1.448<p.z<1.592 and abs(p.x)<.285 and not (p.y<-.043 and abs(p.x)<.105)):keep.append(f)
bmesh.ops.delete(bm,geom=keep,context='FACES');bm.to_mesh(yoke.data);bm.free()
yoke.data.materials.clear();yoke.data.materials.append(leather)
for p in yoke.data.polygons:p.material_index=0
yoke.data.update()
for v in yoke.data.vertices:v.co+=v.normal*.009
body_bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
bpy.data.objects.remove(yoke,do_unlink=True)
# Covered torso/upper arms are removed from the visible mesh; source remains v14.
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f.calc_center_median().z<1.48 and abs(f.calc_center_median().x)<.21) or (1.21<f.calc_center_median().z<1.47 and abs(f.calc_center_median().x)>.215)],context='FACES')
bm.to_mesh(body.data);bm.free()

def surface(name,fun,nu,nv,mat,group,solid=.002,sub=1):
    vs=[fun(i/(nu-1),j/(nv-1)) for i in range(nu) for j in range(nv)]
    fs=[(i*nv+j,(i+1)*nv+j,(i+1)*nv+j+1,i*nv+j+1) for i in range(nu-1) for j in range(nv-1)]
    o=mesh(name,vs,fs,mat,group,sub,solid)
    uv=o.data.uv_layers.new(name='WardrobeUV')
    for p in o.data.polygons:
        for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=(vi%nv/(nv-1),vi//nv/(nu-1))
    return o

def interp(rows,t):
    q=max(0,min(1,t))*(len(rows)-1);i=min(int(q),len(rows)-2);f=q-i
    f=f*f*(3-2*f)
    return [a+(b-a)*f for a,b in zip(rows[i],rows[i+1])]

for side in [-1,1]:
    def shoulder(u,v,side=side):
        x=side*(.076+.221*u);y=.125*(2*v-1)*(1-.24*u)
        # A continuous tailored cap: never mix ray-hit heights and fallback heights,
        # which produces spikes where the fitted patch reaches beyond anatomy.
        z=1.515+.065*sin(pi*(.20+.80*u))-.025*u-.027*(2*v-1)**2
        return Vector((x,y,z))
    surface('Tailored continuous shoulder yoke '+str(side),shoulder,31,29,leather,'03_OuterRobe',.002,1)
    curve('Shoulder stitch',[shoulder(.16+.73*j/40,.15)+Vector((0,0,.002)) for j in range(41)],.0009,seam,'03_OuterRobe')

# Fitted V-neck shirt. Closed torso and three-dimensional placket, collar, buttons.
def torso(u,v):
    z,rx,ry=interp([(1.065,.147,.115),(1.16,.147,.123),(1.32,.181,.146),(1.47,.213,.146),(1.535,.202,.115),(1.595,.074,.074)],u)
    a=2*pi*v;front=max(0,cos(a));z-=.14*u**7*front**5
    fold=.0025*sin(a*13+u*12)*sin(pi*u)
    return Vector(((rx+fold)*sin(a),-.014-(ry+fold)*cos(a),z))
surface('Fitted open neck silk shirt',torso,45,65,shirt,'02_Innerwear')
for s in [-1,1]:
    pts=bez([(s*.070,-.085,1.547),(s*.107,-.13,1.49),(s*.076,-.167,1.42),(s*.022,-.161,1.393)],40)
    # Collar folded as a narrow ribbon, not a gold pipe.
    surface('Shirt folded collar '+str(s),lambda u,v,pts=pts,s=s: pts[min(39,int(u*39))]+Vector((s*.024*sin(pi*u)*v,-.005*sin(pi*v),-.01*v)),40,7,shirt,'02_Innerwear')
curve('Shirt placket',[(0,-.147,1.08),(0,-.155,1.20),(0,-.166,1.32),(0,-.163,1.396)],.003,shirt,'02_Innerwear')
for z in [1.11,1.18,1.25,1.32]:uv('Shirt small metal button',(0,-.171,z),(.003,.002,.003),metal,'02_Innerwear',12)

# Tailored trousers follow the Epic stance; narrow ankle and directional creases.
for s in [-1,1]:
    def pant(u,v,s=s):
        z=1.095-.94*u;x=s*(.102+.047*u);a=2*pi*v
        rw=interp([(.082,.094),(.082,.09),(.057,.065),(.054,.063),(.048,.055)],u)
        crease=.0028*sin(a*9+u*19)+.0035*sin(a*5-u*48)*math.exp(-((u-.77)/.23)**2)
        return Vector((x+(rw[0]+crease)*sin(a),-.008-(rw[1]+crease)*cos(a),z+.005*sin(a*2)*sin(pi*u)))
    surface('Tailored trouser '+str(s),pant,75,49,trouser,'02_Innerwear')
    for vv in [.25,.75]:curve('Trouser stitched side seam',[pant(j/80,vv) for j in range(81)],.0008,shirt,'02_Innerwear')
    # Boots are lofts with distinct vamp, heel, toe and sole, not ellipsoids.
    cx=s*.149
    def shoe(u,v,cx=cx):
        y,rx,h,base=interp([(-.224,.0001,.0001,.03),(-.218,.032,.022,.027),(-.201,.047,.041,.028),(-.135,.051,.064,.025),(-.055,.050,.089,.027),(.008,.043,.112,.037),(.067,.034,.079,.044),(.077,.0001,.0001,.04)],u)
        a=pi*v
        return Vector((cx+rx*cos(a),y,base+h*sin(a)**.62))
    surface('Sculpted ankle boot vamp '+str(s),shoe,51,33,boot,'02_Innerwear',.003,1)
    outline=[(cx+.05*cos(a),-.071+.139*sin(a),.025) for a in [2*pi*j/80 for j in range(81)]]
    curve('Boot welt '+str(s),outline,.005,sole,'02_Innerwear')
    uv('Closed boot outsole',(cx,-.071,.026),(.051,.145,.013),sole,'02_Innerwear',48)
    bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,.025,.023));o=bpy.context.object;o.name='Stacked boot heel';o.scale=(.073,.075,.040);assign(o,'02_Innerwear');o.data.materials.append(sole)
    mod=o.modifiers.new('Rounded heel edges','BEVEL');mod.width=.007;mod.segments=3
    for j in range(7):
        y=-.105+.019*j;z=.106+.013*j
        curve('Boot lace cross',[(cx-.024,y,z),(cx+.024,y+.012,z+.005)],.0012,shirt,'02_Innerwear')
        curve('Boot lace cross',[(cx+.024,y,z+.001),(cx-.024,y+.012,z+.006)],.0012,shirt,'02_Innerwear')
    tube('Boot ankle shaft',[(cx,0,.135),(cx,0,.18),(cx,0,.235)],[.047,.048,.050],[.054,.054,.055],boot,'02_Innerwear',40,.015)

# Red leather longline stage coat. No impossible hovering train; split above boots.
table=[(.20,.30,.183,.56),(.39,.276,.170,.50),(.70,.234,.156,.43),(1.04,.196,.160,.42),(1.19,.183,.158,.49),(1.37,.214,.164,.66),(1.48,.220,.145,.86),(1.505,.215,.132,.91)]
def coat(u,v):
    z,rx,ry,gap=interp(table,u);a=gap+(2*pi-2*gap)*v
    fold=(.010*sin(a*10+u*4)+.004*sin(a*19-u*13))*(1-u)**1.5
    return Vector(((rx+fold)*sin(a),-.005-(ry+fold)*cos(a)+.034*(1-u)**2,z+.024*(1-u)**5*sin(a*3)))
surface('Oxblood tailored longline coat',coat,81,109,leather,'03_OuterRobe',.003,1)
for side in [0,1]:
    ss=1 if side==0 else -1
    surface('Wine satin coat facing',lambda u,v,side=side:coat(u,.038*v if side==0 else 1-.038*v)+Vector((0,-.003,0)),65,9,lining,'03_OuterRobe')
    curve('Coat narrow stitched edge',[coat(j/100,side)+Vector((0,-.003,0)) for j in range(101)],.0011,seam,'03_OuterRobe')
    # Genuine folded lapels use a shaped strip off the torso.
    def lapel(u,v,ss=ss):
        p=Vector((ss*(.075+.070*sin(pi*u)-.025*u),-.08-.095*sin(pi*u*.8),1.555-.36*u))
        return p+Vector((ss*.038*sin(pi*u)*v,-.014*sin(pi*v),-.013*v))
    surface('Folded leather notch lapel',lapel,37,11,leather,'03_OuterRobe',.003,1)
    # Paired restrained chains and stitch tracery, deliberately not armour.
    for j in range(0):
        vv=.057+j*.018 if side==0 else .943-j*.018
        path=[coat(.12+.78*t,vv+.005*sin(t*36+j))+Vector((0,-.004,0)) for t in [k/130 for k in range(131)]]
        curve('Raised coat embroidery',path,.00065,metal,'03_OuterRobe')
    for k in range(8):
        u=.35+k*.065;p=coat(u,.035 if side==0 else .965)+Vector((0,-.006,0))
        uv('Coat understated rivet',p,(.0025,.002,.0025),metal,'03_OuterRobe',10)
    pocket=[coat(.58,.12 if side==0 else .88),coat(.49,.16 if side==0 else .84)]
    curve('Slanted welt pocket',pocket,.005,boot,'03_OuterRobe')

mh=json.loads((ROOT/'Source/default.mhskel').read_text(encoding='utf-8'))
def joint(bone,endpoint):
    ids=mh['joints'][mh['bones'][bone][endpoint]]
    return sum((arm_pose(world(src[i])) for i in ids),Vector())/len(ids)
for s in [-1,1]:
    side='L' if s>0 else 'R'
    a=joint('upperarm01.'+side,'head');b=joint('lowerarm01.'+side,'head');c=joint('wrist.'+side,'head')
    print('SLEEVE_ANATOMY',side,list(a),list(b),list(c),flush=True)
    cs=[]
    for j in range(49):
        t=j/48
        cs.append(a.lerp(b,t/.52) if t<.52 else b.lerp(c,(t-.52)/.48))
    def sleeve(u,v):
        j=min(47,int(u*48));c=cs[j].lerp(cs[j+1],u*48-j);tan=(cs[min(48,j+1)]-cs[max(0,j-1)]).normalized()
        cross=tan.cross(Vector((0,1,0))).normalized();norm=tan.cross(cross);a=2*pi*v
        r=.080-.035*u;wr=.002*sin(a*7+u*19)*sin(pi*u)+.0025*sin(u*53+a*2)*math.exp(-((u-.62)/.21)**2)
        return c+cross*cos(a)*(r+wr)+norm*sin(a)*(r*.98+wr)
    surface('Tailored leather sleeve '+str(s),sleeve,55,49,leather,'03_OuterRobe')
    for v in [.0,.5]:curve('Sleeve stitched seam',[sleeve(j/70,v) for j in range(71)],.0008,seam,'03_OuterRobe')
    for u in [.94,.99]:curve('Leather cuff edge',[sleeve(u,j/70) for j in range(71)],.0012,metal,'03_OuterRobe')
    # Three short shoulder tabs replace large spikes.
    for j in range(3):
        pts=bez([(s*(.14+j*.024),-.084,1.509),(s*(.18+j*.022),-.03,1.536),(s*(.20+j*.025),.035,1.506),(s*(.24+j*.021),.079,1.478)],25)
        surface('Layered shoulder leather tab',lambda u,v,pts=pts,s=s:pts[min(24,int(u*24))]+Vector((s*.012*(v-.5),0,0)),25,5,leather,'06_Regalia')
        curve('Shoulder tab silver edge',pts,.0017,metal,'06_Regalia')

# Belt, small buckle, jewellery: believable manufactured pieces.
surface('Black leather belt',lambda u,v:Vector((.174*sin(2*pi*v),-.147*cos(2*pi*v)-.008,1.077+.032*u)),3,97,boot,'06_Regalia')
curve('Belt rectangular buckle',[(-.023,-.166,1.078),(.023,-.166,1.078),(.023,-.166,1.11),(-.023,-.166,1.11),(-.023,-.166,1.078)],.0025,metal,'06_Regalia')
for s in [-1,1]:
    for row in range(2):
        pts=bez([(s*.058,-.054,1.567),(s*.071,-.16,1.51-row*.035),(s*.038,-.178,1.44-row*.037),(0,-.171,1.427-row*.042)],55)
        # Discrete links, alternate orientation.
        for j in range(0,54,2):
            c=pts[j];curve('Necklace chain link',[(c.x+.0022*cos(a),c.y+(.0012 if j%4 else .0022)*sin(a),c.z+.003*sin(a)) for a in [2*pi*k/12 for k in range(13)]],.00055,metal,'06_Regalia')
    curve('Drop earring',[(s*.086,-.042,1.736),(s*.093,-.053,1.708)],.001,metal,'06_Regalia')
    uv('Small earring charm',(s*.093,-.053,1.704),(.0025,.002,.005),metal,'06_Regalia',12)
curve('Hip chain',bez([(.048,-.163,1.09),(.09,-.183,.96),(.188,-.116,.97),(.182,-.025,1.082)],70),.0018,metal,'06_Regalia')

# Layered auburn cut: opaque tapered locks with fine longitudinal grooves/fibres.
# Each lock follows a curved guide and has a volumetric elliptical cross-section.
def scalp(u,v):
    a=2*pi*v;ph=.018+(1.89-.63*max(0,cos(a)))*u
    return Vector((.092*sin(ph)*sin(a),-.038-.115*sin(ph)*cos(a),1.773+.112*cos(ph)))
surface('Auburn fitted scalp',scalp,23,73,hairmats[3],'05_Hair',.001,1)
guides=[]
for s in [-1,1]:
    for k in range(15):
        f=k/14
        guides.append(([(-.027+s*.008*f,-.044+.075*f,1.891-.023*f),(s*(.075+.035*f),-.125,1.916-.028*f),(s*(.099+.016*f),-.166,1.80-.037*f),(s*(.071+.023*f),-.156+.06*f,1.739-.057*f)],.005+.002*f))
    for k in range(16):
        f=k/15
        guides.append(([(s*(.065+.022*f),-.027+.091*f,1.861-.033*f),(s*(.105+.014*f),-.035+.07*f,1.78),(s*(.106+.012*sin(k)),.028+.07*f,1.69),(s*(.102+.019*f),.036+.085*f,1.61+.06*f)],.006))
for k in range(30):
    a=1.27+3.74*k/29;p=scalp(.57,a/(2*pi));s=sin(a)
    guides.append(([p,(p.x*1.22,.098,1.79),(s*.113,.145,1.64),(s*.125+.015*sin(k),.153+.01*cos(k),1.555+.045*cos(k*2))],.007))
# Forelocks cross the large bare forehead asymmetrically.
for k in range(18):
    f=k/17
    guides.append(([(-.05+.026*f,-.065,1.87),(-.020+.075*f,-.173,1.89),(.048+.038*f,-.194,1.813),(.035+.043*f,-.173,1.742+.025*sin(k))],.0055))
fine=[]
for gi,(guide,width) in enumerate(guides):
    cs=bez(guide,37)
    def lock(u,v,cs=cs,width=width,gi=gi):
        j=min(35,int(u*36));c=cs[j].lerp(cs[j+1],u*36-j);tan=(cs[min(36,j+1)]-cs[max(0,j-1)]).normalized()
        across=tan.cross(Vector((0,1,0))).normalized();normal=tan.cross(across);a=2*pi*v
        taper=max(.02,(1-u)**.53)*(.45+.55*sin(pi*u)**.45)
        return c+across*cos(a)*width*taper+normal*sin(a)*width*.63*taper+Vector((.004*sin(u*11+gi)*sin(pi*u),.002*cos(u*9+gi)*sin(pi*u),0))
    surface('Sculpted auburn layered lock %02d'%gi,lock,37,11,hairmats[gi%4],'05_Hair',0,1)
    for k in range(12):
        vv=(k+.5)/12
        fine.append([lock(t,vv)+Vector((0,-.0004,0)) for t in [.035+.96*j/35 for j in range(36)]])
batch_curves('Auburn fine directional fibers',fine,.00016,hairmats[2],'05_Hair',True,0)
rootpaths=[]
for k in range(550):
    a=k/550
    rootpaths.append([scalp(.02+.98*j/26,a)+Vector((0,-.0005,.001)) for j in range(27)])
batch_curves('Combed scalp fibers',rootpaths,.00023,hairmats[1],'05_Hair',True,0)

# Portrait proportions, head straight for animation; no built-in showcase head tilt.
for c in ['01_Body','05_Hair']:
    for ob in COL[c].objects:
        if ob==body:continue
        if c=='01_Body' and 'Iris radial' in ob.name:
            ob.data.materials.clear();ob.data.materials.append(iris)

# Actual neutral concert studio: dark cyclorama, reflective deck, soft key/rim.
stage=material('Stage graphite',(.012,.014,.019),.25,.30)
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='Studio floor';assign(floor,'90_Stage');floor.data.materials.append(stage)
def light(name,loc,power,color,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);COL['90_Stage'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('Large neutral key',(2,-3,3),250,(1,.89,.82),1.6,(0,0,1.2))
light('Cool fill',(-2,-1,1.9),65,(.72,.81,1),2.1,(0,0,1.3))
light('Concert edge',(-1,1.7,2.6),420,(1,.27,.22),1.5,(0,0,1.2))
light('White rim',(1,1.5,3),450,(1,.94,.85),1.2,(0,0,1.3))
scene=bpy.context.scene;scene.world.color=(.025,.025,.025);scene.render.engine='CYCLES';scene.cycles.samples=24 if DRAFT else 64;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.view_settings.exposure=-.65
data=bpy.data.cameras.new('Concert camera');cam=bpy.data.objects.new('Concert camera',data);COL['90_Stage'].objects.link(cam);scene.camera=cam;data.type='ORTHO'
shots=[('01_Full',(2.7,-7,2.8),(0,0,1.02),2.22,(1100,1500)),('02_Portrait',(.7,-4,1.9),(0,-.025,1.72),.51,(1200,1400)),('03_Back',(-2,5,2.5),(0,0,1.03),2.22,(1000,1400))]
for name,loc,target,scale,res in shots:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=scale
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
cam.location=(2.7,-7,2.8);cam.rotation_euler=(Vector((0,0,1.02))-cam.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=2.22
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
(OUT/'design_manifest.json').write_text(json.dumps({'style':'Redline / 绯序: realistic concert wardrobe','version':VERSION,'magic_particles':False,'source':'CC0 body foundation; original wardrobe geometry','status':'actual Blender model; rig and UE validation follow separately','reference':'User image 2026-09-29, visual only, not redistributed'},ensure_ascii=False,indent=2),encoding='utf-8')
print('CONCERT_MODEL_SAVED',str(OUT),flush=True)
