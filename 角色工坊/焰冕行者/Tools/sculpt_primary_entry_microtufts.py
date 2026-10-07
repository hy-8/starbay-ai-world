"""Rework actual primary entry paths, freeing the formerly fixed first4 points."""
import bpy,sys,re,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version;assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
r=raw[:,0];eligible=np.flatnonzero((r[:,0]>.003)&(r[:,0]<.105)&(r[:,2]>1.805)&(r[:,1]<.060))
body=bpy.data.objects['CC0 male body • retained topology'];assert np.array_equal(np.array(body.matrix_world),np.eye(4))
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
# Follicle-local sections; distinguish opposite departures in the same small cell.
d=raw[eligible,16]-r[eligible];angles=np.floor((np.arctan2(d[:,1],d[:,0])+np.pi)/(.5*np.pi)).astype(int)
keys=np.c_[np.floor(r[eligible]/.008).astype(int),angles]
_,labels=np.unique(keys,axis=0,return_inverse=True)
mask=np.zeros(len(raw),bool);u=np.linspace(0,1,17);rows=[];repairs=0
for k in np.unique(labels):
 ids=eligible[labels==k]
 if len(ids)<12:continue
 old=raw[ids];center=old.mean(axis=0);root=center[0];end=center[16]
 hit,n,_,dist=bv.find_nearest(Vector(root));normal=np.array(n)
 heading=end-root;heading-=normal*np.dot(heading,normal)
 if np.linalg.norm(heading)<.001:continue
 heading/=np.linalg.norm(heading)
 ending=center[17]-center[15];ending/=max(np.linalg.norm(ending),1e-9)
 L=float(np.linalg.norm(np.diff(center[:17],axis=0),axis=1).sum());phase=float(k*2.399963)
 across=np.cross(normal,heading);across/=max(np.linalg.norm(across),1e-9)
 c1=root+heading*(L*.25)+normal*.0012
 c2=end-ending*(L*.25)+normal*.003+across*(.0015*np.sin(phase))
 t=u[:,None];guide=(1-t)**3*root+3*(1-t)**2*t*c1+3*(1-t)*t*t*c2+t**3*end
 # A real3-5mm raised tuft at the middle of entry, tapered to both endpoints.
 lift=.003+.002*(.5+.5*np.cos(phase))
 guide+=normal[None]*(lift*np.sin(np.pi*u)**2)[:,None]
 guide+=across[None]*(.0015*np.sin(2*np.pi*u+phase)*np.sin(np.pi*u)**2)[:,None]
 # True roots and the individually sculpted point16 are unchanged. Intermediate
 # follicles join a shared small tuft instead of preserving the old flat fan.
 root_delta=old[:,0]-root;end_delta=old[:,16]-end
 fade=u*u*(3-2*u);spread=(1-.55*np.sin(np.pi*u)**2)
 offset=root_delta[:,None]*(1-fade)[None,:,None]+end_delta[:,None]*fade[None,:,None]
 values=guide[None]+offset*spread[None,:,None]
 for i in range(len(ids)):
  for j in range(1,16):
   h,n,_,dist=bv.find_nearest(Vector(values[i,j]));gap=(Vector(values[i,j])-h).dot(n)
   if dist<.025 and gap<.0005:values[i,j]+=np.array(n)*(.0007-gap);repairs+=1
 values[:,0]=old[:,0];values[:,16]=old[:,16];q[ids,:17]=values;mask[ids]=True
 rows.append(dict(patch=int(k),fibers=len(ids),lift_m=lift,mean_entry_arc_m=L,max_displacement_m=float(np.linalg.norm(values-old[:,:17],axis=2).max())))
assert mask.sum()>100 and np.isfinite(q).all() and np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[:,16:],raw[:,16:]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_entry_microtufts';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
reflection=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=reflection@cam.matrix_world@reflection
for name in ['02_ThreeQuarter','05_OppositeSide','01_Front']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'entry_sculpture_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,eligible_fibers=len(eligible),changed_fibers=int(mask.sum()),patch_count=len(rows),selection_attribute=attr,patches=rows,all_roots_exact=True,all_points16_through64_exact=True,unselected_primary_exact=True,other_components_exact=True,discrete_body_repairs=repairs,method='Positive-X upper primary entry indices1-15 only; actual8mm follicle cells split by departure quadrant; min12 fibers. Cubic scalp-tangent entry and existing exit tangent,3-5mm tuft lift,1.5mm phase bend,55% intermediate root/end spread contraction. All true follicles and point16 onward retained. First4 are intentionally no longer fixed; no shader/light change.',status='Three actual draft renders pending review; not target or continuous collision acceptance'),indent=2),encoding='utf-8')
print('PRIMARY_ENTRY_MICROTUFTS_SAVED',version,int(mask.sum()),len(rows),flush=True)
