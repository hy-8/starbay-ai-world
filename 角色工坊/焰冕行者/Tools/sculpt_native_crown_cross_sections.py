"""Anisotropic frontal section shaping, confined to elevated crown points."""
import bpy,sys,json,re,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh cross-section study')
source=ROOT/'Exports'/base/'Ember_Regent.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);bpy.context.view_layer.update()
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
labels=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',labels)
t=np.linspace(0,1,65);mask=np.zeros(len(raw),bool);rows=[];contacts=0
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for g in np.unique(labels[labels>=0]):
 members=np.flatnonzero(labels==g);old=raw[members];center=old.mean(axis=0)
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 outward=center-np.array([0,-.035,1.776]);outward-=tangent*np.sum(outward*tangent,axis=1)[:,None];outward/=np.maximum(np.linalg.norm(outward,axis=1)[:,None],1e-8)
 across=np.cross(tangent,outward);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
 delta=old-center[None];along=np.sum(delta*tangent[None],axis=2);wide=np.sum(delta*across[None],axis=2);deep=np.sum(delta*outward[None],axis=2)
 weight=smooth((old[:,:,2]-1.812)/.030)*smooth((t-.060)/.18)[None]*(1-smooth((t-.66)/.29))[None]
 # Compress only broad lateral spread, retaining strand lengthwise scatter.
 values=center[None]+tangent[None]*along[:,:,None]+across[None]*(wide*(1-.62*weight))[:,:,None]+outward[None]*(deep*(1-.15*weight))[:,:,None]
 # Coherent shallow lift offsets put actual neighboring sections at distinct
 # depths rather than replacing their source paths with a flat comb sheet.
 phase=(g*2.399963)%6.283185
 values+=outward[None]*(.0035*np.sin(phase)*weight)[:,:,None]
 for k in range(len(members)):
  for j in range(4,62):
   if weight[k,j]<.001:continue
   hit,n,_,dist=bv.find_nearest(Vector(values[k,j]));gap=(Vector(values[k,j])-hit).dot(n)
   if dist<.015 and gap<.0004:
    d=np.array(n)*(.0006-gap);contacts+=1
    for l in range(max(4,j-2),min(62,j+3)):values[k,l]+=d*np.exp(-.5*((l-j)/1.3)**2)*float(weight[k,l]>.001)
 values[:,:4]=old[:,:4];values[:,62:]=old[:,62:]
 q[members]=values;mask[members]=True
 rows.append(dict(fibers=len(members),max_displacement_m=float(np.linalg.norm(values-old,axis=2).max())))
assert np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[:,62:],raw[:,62:]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_crown_sections','BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'crown_section_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=int(mask.sum()),sections=rows,first_four_and_last_three_points_exact=True,unselected_primary_exact=True,other_hair_unchanged=True,smooth_contact_events=contacts,method='Existing 231 frontal sections: tangent-frame lateral compression up to62%, depth compression up to15%, shallow ±3.5mm coherent section lift; smooth elevated-crown/shaft masks preserve roots and ends',status='Unreviewed actual cross-section study',scope='Discrete body guard, not complete hair segments/eye/clothing/animation or art acceptance'),indent=2),encoding='utf-8')
print('NATIVE_CROWN_SECTIONS_SAVED',version,int(mask.sum()),len(rows),flush=True)
