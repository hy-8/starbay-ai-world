"""Four original articulated civilian characters; meters, +Z up, -Y forward.
Runtime uses distance-driven two-bone leg IK, not the old imported combat walk.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).parent
CATALOG=[]
SPECS=[dict(id='man',label='成年男性',height=1.78,age=32,skin=(.62,.405,.285),shirt=(.61,.55,.43),pants=(.055,.085,.12),hair=(.022,.018,.016),width=1.0,speed=1.25),
 dict(id='woman',label='成年女性',height=1.65,age=28,skin=(.72,.49,.36),shirt=(.035,.23,.24),pants=(.62,.57,.46),hair=(.035,.021,.018),width=.88,speed=1.18),
 dict(id='elder',label='老人',height=1.63,age=72,skin=(.56,.375,.27),shirt=(.27,.075,.065),pants=(.20,.23,.23),hair=(.48,.49,.46),width=.94,speed=.78),
 dict(id='child',label='孩子',height=1.18,age=9,skin=(.64,.42,.27),shirt=(.76,.43,.10),pants=(.06,.19,.25),hair=(.025,.018,.012),width=.95,speed=1.02)]
def material(name,color,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough
 return m
def empty(name,parent=None,loc=(0,0,0)):
 ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.location=loc;return ob
def finish(ob,name,parent,loc,scale,mat):
 ob.name=name;ob.parent=parent;ob.location=loc;ob.scale=scale;ob.data.materials.append(mat)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
def ell(name,parent,loc,scale,mat,seg=24,rings=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings);return finish(bpy.context.object,name,parent,loc,scale,mat)
def shape(name,parent,profiles,mat,seg=24):
 # ring tuple (z, x radius, y radius, y center)
 vertices=[];faces=[]
 for z,rx,ry,cy in profiles:
  for i in range(seg):
   a=math.tau*i/seg;vertices.append((rx*math.cos(a),cy+ry*math.sin(a),z))
 for j in range(len(profiles)-1):
  for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;faces.append((a,b,b+seg,a+seg))
 faces.extend([tuple(range(seg-1,-1,-1)),tuple((len(profiles)-1)*seg+i for i in range(seg))]);mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.parent=parent;mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True
 return ob
def line(name,parent,points,r,mat):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.parent=parent;cu.materials.append(mat);return ob
def rings(name,parent,x,y,z,rx,rz,mat,r=.002):return line(name,parent,[(x+rx*math.cos(i*math.tau/40),y,z+rz*math.sin(i*math.tau/40)) for i in range(41)],r,mat)
for spec in SPECS:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 s=spec['height'];w=spec['width'];kid=spec['id']=='child';elder=spec['id']=='elder';female=spec['id']=='woman'
 skin=material('skin',spec['skin']);shirt=material('civilian_clothes',spec['shirt']);pants=material('pants',spec['pants']);hair=material('hair',spec['hair']);shoe=material('shoe',(.035,.045,.055));sole=material('sole',(.72,.73,.68));white=material('eyes',(.83,.84,.79));iris=material('iris',(.045,.032,.022),.3);lip=material('lips',(.40,.205,.16));details=material('details',(.14,.10,.07));accent=material('accent',(.72,.67,.54));bag=material('bag',(.075,.21,.23))
 root=empty('Character');L1=s*(.227 if kid else .235);L2=s*(.222 if kid else .235);footH=s*.045;hipH=L1+L2+footH-s*.018;hip=empty('Hips',root,(0,0,hipH));waist=s*.092*w
 shape('trouser waist',hip,[(-.008*s,waist*.97,.060*s,0),(.025*s,waist,.063*s,0),(.075*s,waist*.96,.058*s,0)],pants,32)
 torso=empty('Torso',hip,(0,0,s*.055));torsoH=s*.245
 shape('tailored shirt',torso,[(0,waist,s*.062,0),(.09*s,waist*.92,s*.065,0),(.19*s,s*.124*w,s*.072,0),(.235*s,s*.105*w,s*.065,0),(.25*s,s*.06,s*.048,0)],shirt)
 # Layered urban clothing: fitted jacket / relaxed blazer / cardigan / hoodie.
 inner=material('cotton tee',(.83,.81,.72));trim=material('stitched trim',(.38,.32,.24));metal=material('small hardware',(.66,.53,.31),.3)
 shape('visible inner tee',torso,[(.045*s,.027*s,.001*s,-.069*s),(.19*s,.027*s,.001*s,-.078*s),(.235*s,.022*s,.001*s,-.070*s),(.247*s,.018*s,.001*s,-.055*s)],inner)
 for side in [-1,1]:
  line('jacket front edge',torso,[(side*.027*s,-.060*s,.239*s),(side*.032*s,-.078*s,.19*s),(side*.030*s,-.071*s,.045*s)],.0011*s,trim)
  line('tailored shoulder seam',torso,[(side*.045*s,0,.25*s),(side*.093*s,-.035*s,.229*s),(side*.124*s,0,.202*s)],.0012*s,trim)
  line('pocket seam',torso,[(side*.050*s,-.067*s,.09*s),(side*.082*s,-.059*s,.09*s)],.002*s,trim)
  if not kid:
   points=[(side*.029*s,-.057*s,.250*s),(side*.064*s,-.058*s,.219*s),(side*.034*s,-.080*s,.156*s),(side*.024*s,-.079*s,.191*s)]
   me=bpy.data.meshes.new('tailored lapel');me.from_pydata(points,[],[(0,1,2,3)]);me.update();ob=bpy.data.objects.new('flat tailored lapel',me);bpy.context.collection.objects.link(ob);ob.parent=torso;me.materials.append(shirt)

 if kid:
  ell('hood back',torso,(0,.025*s,.242*s),(.062*s,.042*s,.035*s),shirt)
  for side in [-1,1]:line('hood drawstring',torso,[(side*.021*s,-.056*s,.243*s),(side*.022*s,-.081*s,.174*s)],.0018*s,inner)
  line('hoodie front pocket',torso,[(-.055*s,-.063*s,.08*s),(-.043*s,-.070*s,.035*s),(.043*s,-.070*s,.035*s),(.055*s,-.063*s,.08*s)],.002*s,trim)
 if elder:
  for z in [.08,.13,.18]:ell('cardigan button',torso,(0,-.076*s,z*s),(.0035*s,.002*s,.0035*s),metal,12,8)
 neck=ell('neck',torso,(0,0,s*.263),(s*.029,s*.027,s*.045),skin)
 head=empty('Head',torso,(0,0,s*.335));headScale=1.12 if kid else 1;rx=s*.058*headScale;ry=s*.053*headScale;hz=s*.076*headScale
 # A unified, softly sculpted face; shallow eyes and restrained nose avoid bulging features.
 jaw=.76 if female else (.85 if not kid else .82)
 shape('sculpted face',head,[(-hz,.36*rx,.42*ry,-.05*ry),(-hz*.88,.62*rx,.64*ry,-.05*ry),(-hz*.65,jaw*rx,.81*ry,-.035*ry),(-hz*.38,rx*.94,ry*.93,0),(-hz*.05,rx,ry,0),(hz*.22,rx,ry,0),(hz*.50,rx*.98,ry*.97,.015*ry),(hz*.76,rx*.88,ry*.87,.025*ry),(hz*.94,rx*.61,ry*.60,.035*ry),(hz*1.025,rx*.15,ry*.16,.04*ry)],skin,48)
 brow=material('soft brows',(.065,.043,.033));eyelid=material('eyelid',tuple(v*.88 for v in spec['skin']));iris=material('warm brown eyes',(.052,.033,.018),.3)
 for side in [-1,1]:
  ell('ear',head,(side*rx*.98,.05*ry,-hz*.04),(rx*.15,ry*.15,hz*.245),skin)
  ell('ear inner',head,(side*rx*1.045,-ry*.115,-hz*.045),(rx*.058,ry*.017,hz*.115),eyelid)
  ex=side*rx*.425;ez=hz*.16
  ell('eye socket',head,(ex,-ry*.891,ez),(rx*.235,ry*.036,hz*.104),eyelid)
  ell('almond eye',head,(ex,-ry*.925,ez),(rx*.207,ry*.026,hz*.072),white)
  ell('brown iris',head,(ex,-ry*.954,ez),(rx*.072,ry*.012,hz*.060),iris,20,12)
  ell('eye glint',head,(ex-rx*.022,-ry*.969,ez+hz*.023),(rx*.017,ry*.006,hz*.015),white,12,8)
  line('upper eyelid',head,[(ex-rx*.20,-ry*.937,ez),(ex,-ry*.96,ez+hz*.071),(ex+rx*.20,-ry*.937,ez)],.0009*s,brow)
  line('eyebrow',head,[(ex-rx*.21,-ry*.907,ez+hz*.17),(ex,-ry*.956,ez+hz*.215),(ex+rx*.21,-ry*.907,ez+hz*.17)],s*(.0020 if female else .0026),brow)
 ell('nose bridge',head,(0,-ry*.965,-hz*.015),(rx*.095,ry*.115,hz*.22),skin)
 ell('nose tip',head,(0,-ry*1.065,-hz*.18),(rx*.145,ry*.13,hz*.085),skin)
 for side in [-1,1]:ell('nostril wing',head,(side*rx*.105,-ry*1.036,-hz*.208),(rx*.064,ry*.047,hz*.034),eyelid,16,10)
 line('relaxed mouth',head,[(-rx*.23,-ry*.817,-hz*.485),(-rx*.085,-ry*.876,-hz*.501),(0,-ry*.887,-hz*.491),(rx*.085,-ry*.876,-hz*.501),(rx*.23,-ry*.817,-hz*.485)],s*.0014,lip)
 ell('lower lip',head,(0,-ry*.874,-hz*.527),(rx*.17,ry*.025,hz*.028),lip)
 # Hair is sculpted as a cap and directional locks, with a visible forehead.
 shape('fitted hair cap',head,[(hz*.42,rx*.99,ry*.99,.12*ry),(hz*.72,rx*1.035,ry*1.035,.09*ry),(hz*.98,rx*.78,ry*.83,.09*ry),(hz*1.15,rx*.28,ry*.33,.09*ry),(hz*1.17,rx*.08,ry*.09,.09*ry)],hair,40)
 if female:
  ell('bob hair back',head,(0,ry*.68,-hz*.05),(rx*1.035,ry*.57,hz*.87),hair)
  for side in [-1,1]:
   ob=ell('tapered bob side',head,(side*rx*.95,ry*.13,-hz*.08),(rx*.18,ry*.60,hz*.71),hair);ob.rotation_euler.y=side*.08
   ell('earring stud',head,(side*rx*1.04,-ry*.17,-hz*.25),(s*.0024,s*.002,s*.0024),metal,12,8)
  ob=ell('swept side fringe',head,(-rx*.38,-ry*.70,hz*.72),(rx*.52,ry*.21,hz*.24),hair);ob.rotation_euler.y=-.28

 elif kid:
  ell('baseball cap',head,(0,ry*.04,hz*.79),(rx*1.09,ry*1.05,hz*.42),bag)
  ell('curved cap brim',head,(0,-ry*.95,hz*.62),(rx*.91,ry*.55,hz*.045),bag)
  ell('cap badge',head,(0,-ry*.974,hz*.86),(rx*.15,ry*.021,hz*.14),inner)
 elif elder:
  for side in [-1,1]:
   ell('silver temple',head,(side*rx*.92,ry*.14,hz*.21),(rx*.12,ry*.55,hz*.43),hair)
   rings('thin spectacle rim',head,side*rx*.425,-ry*1.01,hz*.16,rx*.29,hz*.18,metal,r=.0012)
   line('glasses temple',head,[(side*rx*.72,-ry*.99,hz*.16),(side*rx*1.04,0,hz*.14)],s*.0011,metal)
   line('smile line',head,[(side*rx*.27,-ry*.95,-hz*.22),(side*rx*.36,-ry*.87,-hz*.41)],s*.0006,eyelid)
  line('glasses bridge',head,[(-rx*.14,-ry*1.03,hz*.18),(rx*.14,-ry*1.03,hz*.18)],s*.0011,metal)
 else:
  for side in [-1,1]:ell('trimmed sideburn',head,(side*rx*.96,ry*.14,hz*.17),(rx*.095,ry*.50,hz*.38),hair)
  ob=ell('sculpted swept quiff',head,(-rx*.12,-ry*.31,hz*.93),(rx*.92,ry*.67,hz*.27),hair);ob.rotation_euler.y=-.09
 for side,label in [(-1,'L'),(1,'R')]:
  thigh=empty('UpperLeg_'+label,hip,(side*s*.052*w,0,0));knee=empty('LowerLeg_'+label,thigh,(0,0,-L1));foot=empty('Foot_'+label,knee,(0,0,-L2))
  shape('trouser thigh',thigh,[(s*.02,s*.052*w,s*.054,0),(-L1*.25,s*.048*w,s*.051,0),(-L1*.72,s*.036*w,s*.038,0),(-L1,s*.031*w,s*.033,0)],pants)
  ell('knee joint',knee,(0,0,0),(s*.032*w,s*.034,s*.034),skin if kid else pants)
  calfmat=skin if kid else pants
  shape('calf',knee,[(0,s*.031*w,s*.033,0),(-L2*.28,s*.034*w,s*.036,.004*s),(-L2*.73,s*.025*w,s*.027,0),(-L2,s*.022*w,s*.024,0)],calfmat)
  ell('sneaker upper',foot,(0,-s*.035,-footH*.48),(s*.031,s*.074,footH*.53),shoe)
  ell('shoe sole',foot,(0,-s*.036,-footH*.86),(s*.033,s*.076,footH*.17),sole)
  ell('sneaker tongue',foot,(0,-s*.021,-footH*.02),(s*.021,s*.031,footH*.12),inner)
  for j in range(3):line('laces',foot,[(-s*.018,-s*(.03+j*.012),-footH*.06),(s*.018,-s*(.035+j*.012),-footH*.06)],s*.0018,sole)
  shoulder=empty('UpperArm_'+label,torso,(side*s*.118*w,0,s*.212));armL=s*.16;lower=empty('LowerArm_'+label,shoulder,(0,0,-armL))
  shape('sleeve',shoulder,[(s*.034,s*.007,s*.009,0),(s*.025,s*.025,s*.028,0),(s*.009,s*.037,s*.041,0),(-armL*.35,s*.034,s*.038,0),(-armL*(.65 if kid else .94),s*.027,s*.030,0)],shirt)
  ell('elbow',lower,(0,0,0),(s*.027,s*.028,s*.031),skin)
  shape('forearm',lower,[(0,s*.026,s*.027,0),(-s*.065,s*.025,s*.027,0),(-s*.13,s*.016,s*.018,0)],skin)
  palm=ell('hand',lower,(0,0,-s*.15),(s*.024,s*.015,s*.032),skin)
  for f in range(4):ell('finger',lower,((f-1.5)*s*.010,-s*.003,-s*(.182-(abs(f-1.5)*.003))),(s*.005,s*.006,s*.020),skin,12,8)
  ell('thumb',lower,(side*s*.026,-s*.005,-s*.153),(s*.009,s*.009,s*.023),skin,12,8)
 if kid:
  ell('school backpack',torso,(0,s*.085,s*.10),(s*.085,s*.045,s*.113),bag)
  for side in [-1,1]:line('backpack strap',torso,[(side*s*.052,s*.08,s*.22),(side*s*.063,-s*.04,s*.22),(side*s*.052,-s*.077,s*.05)],s*.009,bag)
 if female:
  ell('crossbody bag',hip,(s*.11,-s*.035,s*.01),(s*.038,s*.055,s*.07),bag)
  line('crossbody strap',torso,[(-s*.07,-s*.065,s*.23),(0,-s*.08,s*.10),(s*.105,-s*.035,-s*.015)],s*.005,bag)
 # Convert visible curves to mesh so exported GLB retains all facial/clothing details.
 for ob in list(bpy.context.scene.objects):
  if ob.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
 # Consolidate rigid surfaces per joint and material to reduce browser draw calls.
 groups={}
 for ob in list(bpy.context.scene.objects):
  if ob.type=='MESH':groups.setdefault((ob.parent,ob.data.materials[0]),[]).append(ob)
 for (parent,mat),objects in groups.items():
  if len(objects)<2:continue
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objects:ob.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name=parent.name+'_'+mat.name
 root['type']=spec['id'];root['label']=spec['label']
 bpy.ops.export_scene.gltf(filepath=str(ROOT/f"assets/npc_{spec['id']}.glb"),export_format='GLB',export_animations=False)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f"assets/npc_{spec['id']}.blend"))
 CATALOG.append({**spec,'legUpper':L1,'legLower':L2,'hipHeight':hipH,'footHeight':footH,'stepLength':s*(.235 if elder else .30),'file':f"npc_{spec['id']}.glb"})
(ROOT/'assets/npc_catalog.json').write_text(json.dumps(CATALOG,ensure_ascii=False,indent=2),encoding='utf-8')
print('V4_URBAN_CIVILIAN_MODELS_READY',flush=True)
