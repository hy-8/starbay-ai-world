"""Small authored native-curve lock study on the actual CC0 target scalp.

Two smooth analytic cubic paths and thin transported cross sections. No Fab
geometry or generative image replacement. Sample only, not a complete groom.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version=a[0]
if not re.fullmatch('[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh sample only')
source=ROOT/'Exports/napeunderlay02/Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
body=bpy.data.objects['CC0 male body • retained topology'];bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
whole='--whole-groom' in a;supports=[]
for o in bpy.data.objects:
 if not o.hide_render and (o.type=='CURVES' or o.name.startswith('Original nape underlay')):
  if whole and o.name.startswith(('Abhay flow derivative','Bystedt derivative','Original posterior coverage')):
   supports.append(o);continue
  o.hide_render=True;o.hide_set(True)
mat=bpy.data.materials.new('Original lock control • physical dark cherry hair');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
info=nt.nodes.new('ShaderNodeHairInfo');ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.018,.0011,.0022,1);ramp.color_ramp.elements[1].color=(.07,.005,.008,1);nt.links.new(info.outputs['Random'],ramp.inputs[0])
bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.27;bs.inputs['Radial Roughness'].default_value=.36;nt.links.new(ramp.outputs[0],bs.inputs['Color'])
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],output.inputs[0])
for o in supports:
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)
design=[
 {'name':'Front left long curtain sample','knots':[[-.028,-.048,1.844],[-.067,-.083,1.863],[-.097,-.103,1.817],[-.044,-.134,1.756]],'across':[0,1,0],'width':.014},
 {'name':'Side left nape sample','knots':[[-.043,.006,1.844],[-.089,.012,1.861],[-.104,.091,1.778],[-.077,.073,1.700]],'across':[0,1,0],'width':.014}]
if '--head-calibrated' in a:
 design=[
  {'name':'Measured front camera-facing sample','knots':[[.032,-.051,1.870],[.068,-.113,1.889],[.113,-.168,1.807],[.065,-.178,1.742]],'across':[1,0,0],'width':.014},
  {'name':'Measured side camera-facing sample','knots':[[.043,.006,1.849],[.089,.012,1.866],[.104,.091,1.778],[.077,.073,1.700]],'across':[0,1,0],'width':.014}]
if whole:
 # Each row is an individually planned trajectory on the measured target
 # frame. Endpoints deliberately mix short forehead, ear passage and nape.
 front=[
  ([[.012,-.032,1.870],[.048,-.096,1.889],[.108,-.161,1.817],[.068,-.178,1.745]],.013),
  ([[.021,-.053,1.864],[.060,-.119,1.881],[.068,-.187,1.812],[.024,-.181,1.776]],.011),
  ([[.035,-.054,1.861],[.080,-.093,1.881],[.108,-.157,1.801],[.079,-.167,1.715]],.012),
  ([[.014,-.071,1.861],[.041,-.135,1.863],[.016,-.189,1.817],[.030,-.179,1.774]],.009),
  ([[.039,-.085,1.845],[.076,-.126,1.867],[.096,-.179,1.795],[.057,-.181,1.750]],.011),
  ([[.028,-.096,1.844],[.054,-.148,1.858],[.036,-.187,1.797],[.014,-.177,1.764]],.010),
  ([[.005,-.084,1.863],[.031,-.153,1.857],[.047,-.183,1.825],[.032,-.170,1.791]],.009),
  ([[.051,-.065,1.845],[.103,-.100,1.856],[.113,-.146,1.750],[.092,-.120,1.691]],.011)]
 sides=[
  ([[.045,-.001,1.852],[.089,.012,1.866],[.105,.085,1.781],[.077,.073,1.700]],.014),
  ([[.058,-.029,1.838],[.111,-.019,1.852],[.118,.048,1.740],[.088,.022,1.661]],.015),
  ([[.050,.020,1.837],[.084,.060,1.850],[.113,.064,1.752],[.108,.027,1.695]],.012),
  ([[.031,.018,1.857],[.075,.050,1.867],[.111,.084,1.795],[.094,.091,1.735]],.015),
  ([[.060,-.067,1.825],[.100,-.069,1.842],[.105,-.055,1.757],[.073,-.061,1.692]],.011),
  ([[.064,.005,1.812],[.103,.034,1.825],[.118,.042,1.706],[.093,.069,1.642]],.013),
  ([[.056,.037,1.795],[.096,.070,1.813],[.099,.099,1.704],[.072,.074,1.655]],.013)]
 design=[]
 for side in [1,-1]:
  for region,items,across in [('fringe',front,[1,0,0]),('side',sides,[0,1,0])]:
   for index,(knots,width) in enumerate(items):
    knots=np.array(knots,float);knots[:,0]*=side
    if side<0:
     # Deliberate mild asymmetric part and unequal tips, not exact mirroring.
     knots[0:2,1]+=.003;knots[1,2]-=.003;knots[2:,0]-=.004*np.sin(index*1.7);knots[-1,2]+=.006*np.cos(index*1.2)
    design.append(dict(name=f'Original cubic {region} {side:+d} {index:02}',knots=knots.tolist(),across=across,width=width))
 rear=[
  ([[-.025,.013,1.857],[-.047,.072,1.866],[-.016,.104,1.784],[-.039,.086,1.719]],.014),
  ([[.008,.014,1.864],[.020,.073,1.875],[.050,.101,1.792],[.028,.085,1.731]],.014),
  ([[-.008,.033,1.849],[-.020,.078,1.863],[.012,.105,1.761],[.008,.079,1.662]],.015),
  ([[.025,.031,1.847],[.049,.070,1.860],[.040,.113,1.771],[.063,.079,1.676]],.015),
  ([[-.040,.031,1.829],[-.066,.077,1.852],[-.049,.109,1.744],[-.024,.082,1.657]],.014),
  ([[-.026,.054,1.804],[-.042,.094,1.822],[-.021,.115,1.698],[-.037,.075,1.625]],.014),
  ([[.005,.060,1.798],[.018,.093,1.817],[-.010,.110,1.711],[.015,.073,1.634]],.015),
  ([[.040,.049,1.804],[.058,.088,1.817],[.032,.110,1.724],[.047,.080,1.645]],.014),
  ([[-.009,.058,1.770],[.007,.094,1.786],[.034,.098,1.682],[.017,.062,1.622]],.013),
  ([[-.047,.045,1.773],[-.065,.085,1.791],[-.081,.097,1.687],[-.065,.061,1.619]],.013),
  ([[.046,.045,1.772],[.072,.081,1.793],[.069,.098,1.683],[.080,.068,1.632]],.014),
  ([[-.030,.037,1.738],[-.051,.079,1.754],[-.043,.082,1.671],[-.021,.057,1.610]],.012),
  ([[.028,.037,1.737],[.039,.078,1.754],[.056,.083,1.675],[.033,.061,1.617]],.012),
  ([[.001,.041,1.722],[-.009,.075,1.751],[.010,.074,1.662],[-.004,.054,1.608]],.012)]
 for index,(knots,width) in enumerate(rear):design.append(dict(name=f'Original cubic rear {index:02}',knots=knots,across=[1,0,0],width=width))
N=65;t=np.linspace(0,1,N);rng=np.random.default_rng(100505);record=[];loose='--loose-fibers' in a
for row in design:
 knots=np.array(row['knots'],float);hit,nn,_,distance=bv.find_nearest(Vector(knots[0]));knots[0]=np.array(hit+nn*.0005)
 # Adjust the first handle with the attachment displacement, keeping its
 # intended local direction. C2-smooth cubic, no inter-knot tangent jumps.
 knots[1]+=knots[0]-np.array(row['knots'][0])
 def evaluate(tt):
  return (1-tt[:,None])**3*knots[0]+3*(1-tt[:,None])**2*tt[:,None]*knots[1]+3*(1-tt[:,None])*tt[:,None]**2*knots[2]+tt[:,None]**3*knots[3]
 g=evaluate(t);tg=np.gradient(g,axis=0);tg/=np.linalg.norm(tg,axis=1)[:,None]
 across=np.empty_like(g);previous=np.array(row['across'],float)
 for j in range(N):
  previous-=tg[j]*np.dot(previous,tg[j]);previous/=max(np.linalg.norm(previous),1e-9);across[j]=previous
 depth=np.cross(tg,across);depth/=np.linalg.norm(depth,axis=1)[:,None]
 fibers=[];radii=[];repairs=0;maxrepair=0.
 for i in range(500 if loose else 700):
  if loose:
   angle=rng.uniform(0,2*np.pi);radial=np.sqrt(rng.uniform(0,1))
   w=radial*np.cos(angle)*row['width']/2;d=radial*np.sin(angle)*.0025
  else:w=rng.uniform(-row['width']/2,row['width']/2);d=rng.uniform(-.0015,.0015)
  fraction=rng.uniform(.86,1);tt=t*fraction
  q=evaluate(tt)
  ac=np.stack([np.interp(tt,t,across[:,k]) for k in range(3)],axis=1)
  dep=np.stack([np.interp(tt,t,depth[:,k]) for k in range(3)],axis=1)
  # Keep roots across a broad thin scalp strip; keep most of the lock broad
  # through its middle, with loose subordinate clumps and staggered tips.
  subcenter=np.round(w/.0025)*.0025
  ww=(w*(1-.6*tt**1.8)+subcenter*.6*tt**1.8)*(1-.55*tt**1.3)
  dd=d*(1-.8*np.minimum(tt/.4,1)**2*(3-2*np.minimum(tt/.4,1)))
  if loose:
   ww=w*(1-.35*tt**1.3)+rng.normal(0,.0011)*tt**3
   dd=d*(1-.35*tt)
  q+=ac*ww[:,None]+dep*dd[:,None]
  root,normal,_,dist=bv.find_nearest(Vector(q[0]));delta=np.array(root+normal*.0004)-q[0]
  q+=delta[None]*(1-tt[:,None])**2
  phase=rng.uniform(0,2*np.pi)
  q+=ac*((.00065 if loose else .00022)*np.sin(tt*6+phase)*np.sin(np.pi*tt))[:,None]
  if loose:q+=dep*(.0004*np.sin(tt*9+phase*.7)*np.sin(np.pi*tt))[:,None]
  for j in range(1,N):
   hit,normal,_,dist=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(normal)
   if dist<.035 and gap<.0004:
    amount=.0005-gap;q[j]+=np.array(normal)*amount;repairs+=1;maxrepair=max(maxrepair,amount)
  fibers.append(q);radii.append(rng.uniform(.000030,.000045)*(1-.997*t**2.4)**.75)
 p=np.array(fibers,np.float32);rr=np.array(radii,np.float32)
 cu=bpy.data.hair_curves.new(row['name']);cu.add_curves([N]*len(p));cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rr.ravel());cu.materials.append(mat)
 o=bpy.data.objects.new(row['name'],cu);bpy.context.scene.collection.objects.link(o)
 gc=bpy.data.curves.new(row['name']+' explicit control','CURVE');gc.dimensions='3D';sp=gc.splines.new('POLY');sp.points.add(N-1)
 for v,point in zip(sp.points,g):v.co=(*point,1)
 control=bpy.data.objects.new('Hidden design '+row['name'],gc);bpy.context.scene.collection.objects.link(control);control.hide_render=True;control.hide_set(True)
 record.append(dict(name=row['name'],bezier_knots_m=knots.tolist(),fibers=len(p),points_per_fiber=N,root_strip_width_m=row['width'],
  discrete_body_point_repairs=repairs,maximum_point_repair_m=maxrepair,finite=bool(np.isfinite(p).all()),positive_radii=bool((rr>0).all()),
  loose_fibers=loose,scope=('Full groom candidate' if whole else 'Two-lock representative sample, no full-head coverage')+'. Discrete guard is not complete hair segment/clothing/animation proof.'))
out.mkdir(parents=True);render.mkdir(parents=True)
(out/'lock_control_manifest.json').write_text(json.dumps(dict(source='napeunderlay02',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),samples=record,
 purpose='Individually designed analytic cubic paths on measured target head, thin smooth transported frames, loose existing-content-free original fibers',
 whole_groom=whole,retained_licensed_short_support=[o.name for o in supports],artistic_status='Unreviewed real 3D candidate; not acceptance'),indent=2),encoding='utf-8')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
if loose:
 d=bpy.data.cameras.new('06_LockCloseup');d.lens=90;o=bpy.data.objects.new('06_LockCloseup',d);bpy.context.scene.collection.objects.link(o);o.location=(.23,-.44,1.87);o.rotation_euler=(Vector((.078,-.144,1.80))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
names=['01_Front','02_ThreeQuarter','03_Side','04_Back'] if whole else ['02_ThreeQuarter','03_Side','04_Back']
for name in names+(['06_LockCloseup'] if loose and not whole else []):
 if name=='06_LockCloseup':s.render.resolution_percentage=100;s.cycles.samples=192
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('BEZIER_LOCK_SAMPLE_RENDERED',version,flush=True)
