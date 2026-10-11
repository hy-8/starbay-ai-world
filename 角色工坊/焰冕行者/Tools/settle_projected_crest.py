"""Lower a localized high-crest arc while preserving roots, tips and strand gauge."""
import bpy,sys,json,hashlib,re
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,idsversion=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:3])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
idm=json.loads((ROOT/'Renders'/idsversion/'edit_id_manifest.json').read_text());assert idm['source_sha256']==digest
selected=np.load(ROOT/'Renders'/idsversion/'local_projected_indices.npz')['selected']
mixed='--mixed-projected' in a
out=ROOT/'Renders'/version;assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());old=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
accepted=np.empty(len(sizes),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',accepted)
if mixed:
 cam=bpy.data.objects['02_ThreeQuarter'];view=np.array(cam.matrix_world.inverted());proj=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1))
 world=np.c_[p,np.ones(len(p))]@np.array(ob.matrix_world).T;local=world@view.T;clip=local@proj.T;ndc=clip[:,:3]/clip[:,3,None]
 cx,cy,rx,ry=idm['selection_rule']['ThreeQuarter_normalized_ellipse']
 projected_field=np.exp(-((ndc[:,0]*.5+.5-cx)/(rx*1.1))**2-((.5-ndc[:,1]*.5-cy)/(ry*1.1))**2)
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
mask=np.zeros(len(sizes),bool);reverted=0
for i in selected:
 if (not mixed and sizes[i]!=65) or accepted[i]:continue
 path=old[off[i]:off[i+1]];t=np.linspace(0,1,len(path))
 field=np.exp(-((path[:,0]-.009)/.032)**2-((path[:,1]+.033)/.033)**2)
 height=smooth((path[:,2]-1.870)/.008);envelope=smooth((t-.12)/.15)*(1-smooth((t-.7)/.15));envelope[:8]=0;envelope[56:]=0
 delta=.003*field*height*envelope
 if mixed:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  delta=.004*projected_field[off[i]:off[i+1]]*smooth(arc/.018)*(1-smooth((arc/max(arc[-1],1e-8)-.75)/.25))
 if delta.max()<.00001:continue
 vals=path.copy();vals[:,2]-=delta
 for j in (range(1,len(path)-1) if mixed else range(8,56)):
  if delta[j]<.00001:continue
  h,n,_,d=bv.find_nearest(Vector(vals[j]));oh,on,_,od=bv.find_nearest(Vector(path[j]))
  if (Vector(vals[j])-h).dot(n)<min(.0005,(Vector(path[j])-oh).dot(on)):
   vals[j]=path[j];reverted+=1
 p[off[i]:off[i+1]]=vals;mask[i]=np.any(vals!=path)
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
for shot in ['02_ThreeQuarter','01_Front']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
method='Selected65control crest strands only,exclude accepted inner curtain.3mm maximum downward spatial Gaussian with highZ gate and smooth middle envelope. First8,last9,all radii/counts/materials retained. Revert points that would worsen original signed body gap or cross0.5mm positive gap. Discrete guard,not continuous collision proof.'
if mixed:method='Mixed-count selected crest strands,exclude accepted inner curtain.4mm maximum downward projected Gaussian,18mm root arc-length fade and last25percent fade to exact tip. All roots,tips,radii/counts/materials retained;near-root intermediate controls intentionally change. Revert points worsening original signed body gap or crossing0.5mm positive gap. Discrete guard,not continuous collision proof.'
(out/'crest_settle_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,model_saved=False,selection=idsversion,mixed_projected=mixed,selected_fibers=int(mask.sum()),max_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),discrete_reverted_points=reverted,images_sha256=images,method=method),indent=2),encoding='utf-8')
print('CREST_SETTLE_PREVIEW',version,int(mask.sum()),flush=True)
