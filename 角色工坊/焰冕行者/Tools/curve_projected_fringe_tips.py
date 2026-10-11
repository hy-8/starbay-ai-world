"""Curve a small inspected tip group with a smooth, body-guarded terminal field."""
import bpy,sys,json,re,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
save='--save-archive' in a;save_only='--save-only' in a;assert not save_only or save
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Renders'/version;md=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者\Exports')/version
assert not out.exists() and (not save or not md.exists())
sel=ROOT/'Renders'/selection;sm=json.loads((sel/'edit_id_manifest.json').read_text());assert sm['source_sha256']==digest
ids=np.load(sel/'local_projected_indices.npz')['selected'];assert 0<len(ids)<=500
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());original=p.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def gap(point):
 h,n,_,_=bv.find_nearest(Vector(point));return float((Vector(point)-h).dot(n))
mask=np.zeros(len(sizes),bool);mask[ids]=True;scales=[];inner=np.empty(len(sizes),bool);cu.attributes['native_inner_curtain_shift'].data.foreach_get('value',inner)
for i in ids:
 old=original[off[i]:off[i+1]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
 start=max(.65*arc[-1],arc[-1]-.045);u=np.clip((arc-start)/max(arc[-1]-start,1e-8),0,1)
 field=.80+.20*np.sin(old[0,0]*91+old[0,1]*73)**2
 delta=np.array([-np.sign(old[-1,0])*.008,.018,.006])*field;shift=u[:,None]**2*delta
 # One scale per entire curve prevents jagged pointwise reverts. Midpoints included.
 samples=np.vstack([old,(old[:-1]+old[1:])*.5]);sample_shift=np.vstack([shift,(shift[:-1]+shift[1:])*.5])
 moving=np.linalg.norm(sample_shift,axis=1)>1e-7;samples=samples[moving];sample_shift=sample_shift[moving]
 thresholds=[min(.0005,gap(point))-1e-6 for point in samples];scale=1.
 for trial in range(9):
  if all(gap(point+step*scale)>=threshold for point,step,threshold in zip(samples,sample_shift,thresholds)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=old+shift*scale;scales.append(scale)
assert np.isfinite(p).all() and np.array_equal(p[off[:-1]],original[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();modelhash=None
if save:
 cu.attributes.new('native_curved_projected_tips','BOOLEAN','CURVE').data.foreach_set('value',mask)
 md.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(md/'Ember_Regent.blend'),compress=True);modelhash=hashlib.sha256((md/'Ember_Regent.blend').read_bytes()).hexdigest()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);images={}
if not save_only:
 for shot in ['02_ThreeQuarter','03_Side','01_Front']:
  s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
manifest=dict(source=base,source_sha256=digest,source_unchanged=True,selection=selection,model_saved=save,model_sha256=modelhash,selected_fibers=len(ids),historical_inner_selected=int(inner[ids].sum()),scale_quantiles=np.quantile(scales,[0,.5,1]).tolist(),zero_scale_fibers=int(np.count_nonzero(np.array(scales)==0)),max_same_index_displacement_m=float(np.linalg.norm(p-original,axis=1).max()),images_sha256=images,method='Exact inspected projection set<=500 curves. Preserve prefix until max(65percent original arc,length-45mm). Quadratic terminal displacement8mm inwardX,18mm backY,6mm upZ times coherent root factor0.8-1. One backtracked scale per whole curve protects original signed body gap at controls and segment midpoints. Radii,counts,root and all unselected/other objects unchanged. May edit historical accepted terminal paths while preserving their roots/part;not continuous collision or artistic acceptance.')
(out/'curved_tips_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if save:(md/'curved_tips_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PROJECTED_TIPS_CURVED',version,len(ids),flush=True)
