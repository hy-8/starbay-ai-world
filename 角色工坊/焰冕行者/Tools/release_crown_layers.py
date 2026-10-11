"""Spatially varied relief and measured own-path layering, no cubic regrouping."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];full='--full' in a;front='--front' in a
assert not(full and front)
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);r=raw[:,0];q=raw.copy()
mask=np.empty(len(raw),bool);cu.attributes['native_descending_fine_locks'].data.foreach_get('value',mask)
protected=np.zeros(len(raw),bool)
for n in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
    v=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',v);protected|=v
mask&=~protected
# Include side/back crown, protect foremost paths to maintain the accepted part.
mask&=(r[:,2]>1.800)&(np.abs(r[:,0])>.018)
if front:mask&=(r[:,0]>.018)&(r[:,1]<-.030)
else:
    mask&=r[:,1]>-.055
    if not full:mask&=r[:,0]>.045
ids=np.flatnonzero(mask);assert len(ids)>500
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
u=np.clip((np.linspace(0,1,65)-11/64)/(1-11/64),0,1)
envelope=np.sin(np.pi*u)**1.65
rng=np.random.default_rng(186);jitter=rng.random(len(raw));cuts=[];repairs=0
for i in ids:
    old=raw[i];root=r[i]
    # Continuous irregular root field: nearby fibers keep coherent texture,
    # while different small patches gain independent lift and terminal length.
    field=.5+.26*np.sin(root[0]*173+root[1]*97)+.17*np.sin(root[1]*291-root[2]*117)+.07*np.cos(root[0]*431-root[1]*193)
    field=np.clip(field,0,1)
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
    tail=s[-1]-s[28];cut=min(.004+.014*field+.002*jitter[i],tail*.35)
    v=np.clip((s-s[28])/tail,0,1);target=s-cut*v*v*(3-2*v)
    assert np.all(np.diff(target)>0)
    values=np.column_stack([np.interp(target,s,old[:,j]) for j in range(3)])
    # Approximate scalp-outward directions; sampled contact guard below.
    normal=old-np.array([0.,-.030,1.775]);normal[:,2]*=.8
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
    tangent=np.gradient(old,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    lateral=np.cross(tangent,normal);lateral/=np.maximum(np.linalg.norm(lateral,axis=1)[:,None],1e-9)
    lift=.001+.0055*field;side=.0025*np.sin(root[0]*211-root[1]*157)
    values+=envelope[:,None]*(normal*lift+lateral*side)
    correction=np.zeros_like(values)
    for j in range(12,65):
        hit,n,_,dist=bv.find_nearest(Vector(values[j]));gap=(Vector(values[j])-hit).dot(n)
        if dist<.025 and gap<.0008:correction[j]=np.array(n)*(.0012-gap);repairs+=1
    for axis in range(3):correction[:,axis]=np.convolve(np.pad(correction[:,axis],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
    values+=correction;values[:12]=old[:12];q[i]=values;cuts.append(cut)
assert np.array_equal(q[~mask],raw[~mask]) and np.array_equal(q[:,:12],raw[:,:12]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_spatial_crown_release';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
record=dict(source=base,source_sha256=digest,full=full,selected_fibers=len(ids),selection_attribute=attr,preserved_prefix_points=12,source_polyline_trim_quantiles_m=np.quantile(cuts,[0,.5,1]).tolist(),sampled_body_repairs=repairs,max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method='Source upper crown excluding current fringe and accepted curtain. RootZ>1.800,Y>-55mm,absX>18mm; pilot additionallyX>45mm. Continuous root field controls1-6.5mm mid relief/2.5mm lateral spread; own source polyline trims4-20mm afterpoint28,limited35 percent remaining path. Root12 points exact. Sampled guard,not continuous collision proof. No common group guides or shader changes.',status='True geometry pilot pending artistic review')
record['front']=front
if front:record['method']=record['method'].replace('RootZ>1.800,Y>-55mm,absX>18mm; pilot additionallyX>45mm.','Front study:RootZ>1.800,Y<-30mm,X>18mm.')
(out/'crown_release_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for shot in (['02_ThreeQuarter','01_Front'] if front else ['02_ThreeQuarter','03_Side']):
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('CROWN_RELEASE_RENDERED',version,len(ids),flush=True)
