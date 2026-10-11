"""Bring a surviving fringe side toward the part using its existing flow."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
side=a[a.index('--side')+1] if '--side' in a else 'negative'
front_frame='--front-frame' in a
natural_length='--natural-length' in a
curtain_arc='--curtain-arc' in a
assert not curtain_arc or natural_length
prefix=6 if '--early-flow' in a else 16
amount=float(a[a.index('--amount')+1]) if '--amount' in a else .018
assert side in ['negative','positive','both'] and 0<amount<=.035
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out,rd=ROOT/'Exports'/version,ROOT/'Renders'/version
assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float)
fringe=np.empty(len(raw),bool);cu.attributes['native_resculpted_fringe_sweeps'].data.foreach_get('value',fringe)
original_fringe=fringe.copy()
if front_frame:
 upper=np.empty(len(raw),bool);cu.attributes['native_descending_fine_locks'].data.foreach_get('value',upper)
 fringe |= upper & (raw[:,0,1]<-.015)
ends=raw[:,-1]
mask=fringe & (ends[:,1]<-.08) & (ends[:,2]>1.70) & (np.abs(ends[:,0])>.015) & (np.abs(ends[:,0])<.105)
if side!='both':mask &= ends[:,0]<0 if side=='negative' else ends[:,0]>0
ids=np.flatnonzero(mask);assert len(ids)>100
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
t=np.linspace(0,1,65);u=np.clip((t-t[prefix-1])/(1-t[prefix-1]),0,1);w=u*u*(3-2*u)
q=raw.copy();repairs=0;deltas=[]
for index in ids:
 old=raw[index];end=old[-1].copy()
 sign=np.sign(end[0]);inward=amount*(.75+.25*np.cos(old[0,0]*45))
 if natural_length:end[0]-=sign*inward*abs(end[0])/(.05+abs(end[0]))*(.2 if curtain_arc else 1)
 else:end[0]-=sign*min(inward,max(0,abs(end[0])-.012))
 end[1]-=.004
 # Keep the longer outer face frame; the inner boundary finishes near brow.
 if not natural_length and abs(end[0])<.065:end[2]=max(end[2],1.750+.010*(1-abs(end[0])/.065))
 delta=end-old[-1];values=old+w[:,None]*delta
 if curtain_arc:
  bell=np.sin(np.pi*u)**1.5
  values[:,0]-=sign*amount*bell
  values[:,1]-=.009*bell
 correction=np.zeros_like(values)
 for j in range(prefix,65):
  hit,n,_,dist=bv.find_nearest(Vector(values[j]));gap=(Vector(values[j])-hit).dot(n)
  if dist<.025 and gap<.001:
   correction[j]=np.array(n)*(.0015-gap);repairs+=1
 for axis in range(3):correction[:,axis]=np.convolve(np.pad(correction[:,axis],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
 values+=correction;values[:prefix]=old[:prefix];q[index]=values;deltas.append(delta)
assert np.isfinite(q).all() and np.array_equal(q[:,:prefix],raw[:,:prefix]) and np.array_equal(q[~mask],raw[~mask])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_inner_curtain_shift'
assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'inner_curtain_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,side=side,amount_m=amount,natural_length=natural_length,curtain_arc=curtain_arc,include_front_frame=front_frame,additional_front_frame_fibers=int((mask & ~original_fringe).sum()),selection_attribute=attr,changed_fibers=len(ids),preserved_prefix_points=prefix,endpoint_delta_quantiles_m=np.quantile(deltas,[0,.5,1],axis=0).tolist(),sampled_body_repairs=repairs,method='Surviving fringe'+(' plus upper attribute/rootY<-15mm' if front_frame else '')+'; endpointY<-80mm/Z>1.70m/absX15-105mm; retain own flow, smooth endpoint displacement afterpoint'+str(prefix-1)+'. Inward75-100% of amount by rootX,forward4mm. '+('Inward also multiplied byabsX/(50mm+absX),no hardX cap or Z floor,old endpointZ before bodyguard; this is not exact arclength preservation.' if natural_length else 'Inner absX<65mm tipZ floor1.750m+10mm*(1-absX/65mm),before sampled body guard.')+(' Curtain arc reduces endpointX movement to20%, adds full-amount inward and9mm forward sin(pi*u)^1.5 middle bow.' if curtain_arc else '')+' Other geometry/radii/materials/lights retained. Not continuous collision proof.',status='Actual two-view geometry study awaiting art review'),indent=2),encoding='utf-8')
for shot in ['02_ThreeQuarter','01_Front']:
 s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('INNER_CURTAIN_RENDERED',version,len(ids),flush=True)
