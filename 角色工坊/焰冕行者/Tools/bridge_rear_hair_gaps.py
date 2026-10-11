"""Preview fine interpolated infill between compatible existing rear fibers."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
fine_density='--fine-density' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in [version,base])
out=ARCHIVE/'Renders'/version;assert not out.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
original_r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',original_r)
new_r=original_r.copy()
sizes=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(sizes)]
raw=np.empty(len(sizes),bool);cu.attributes['native_restored_raw_controls'].data.foreach_get('value',raw)
mask=raw&(p[off[1:]-1,1]>.015)&(p[off[1:]-1,2]<1.800)&(p[off[:-1],1]>-.030)
if pilot:mask&=p[off[:-1],0]<-.005
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 flags=np.empty(len(mask),bool);cu.attributes[key].data.foreach_get('value',flags);mask&=~flags
ids=np.flatnonzero(mask);paths=[];arcs=[];samples=[];ts=np.linspace(0,1,33)
for i in ids:
 q=p[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 paths.append(q);arcs.append(arc);samples.append(np.column_stack([np.interp(ts*arc[-1],arc,q[:,axis]) for axis in range(3)]))
samples=np.array(samples);centers=samples[:,16];tree=KDTree(len(ids))
for row,c in enumerate(centers):tree.insert(Vector(c),row)
tree.balance()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
newpaths=[];newradii=[];pairs=[];rejected=0;no_pair=0
for row,i in enumerate(ids):
 q=paths[row];arc=arcs[row]
 if arc[-1]<.050:continue
 compatible=[];direction=samples[row,24]-samples[row,8];direction/=max(np.linalg.norm(direction),1e-10)
 for _,other,dist in tree.find_range(Vector(centers[row]),.014):
  if other==row or dist<.004:continue
  oq=paths[other]
  if np.linalg.norm(oq[0]-q[0])>.018 or np.linalg.norm(oq[-1]-q[-1])>.025:continue
  if not .65<arcs[other][-1]/arc[-1]<1.5:continue
  od=samples[other,24]-samples[other,8];od/=max(np.linalg.norm(od),1e-10)
  if float(od@direction)<.92:continue
  compatible.append((abs(dist-.008),other))
 if not compatible:no_pair+=1;continue
 other=min(compatible)[1];oq=paths[other];oarc=arcs[other]
 t=arc/max(arc[-1],1e-10);neighbor=np.column_stack([np.interp(t*oarc[-1],oarc,oq[:,axis]) for axis in range(3)])
 added_for_parent=0
 for fraction in ([.18,.38,.62,.82] if fine_density else [.30+.40*((int(i)*2654435761%997)/996)]):
  blend=fraction*smooth((arc-.008)/.025)
  new=q+(neighbor-q)*blend[:,None]
  old_samples=np.vstack([q,(q[:-1]+q[1:])*.5]);new_samples=np.vstack([new,(new[:-1]+new[1:])*.5])
  if any(gap(v)<min(.0002,gap(o))-2e-6 for o,v in zip(old_samples,new_samples)):
   rejected+=1;continue
  assert np.array_equal(new[arc<=.008],q[arc<=.008])
  radius=(.000018+.000012*((int(i)*2246822519%991)/990))*(1-.98*smooth((t-.70)/.30))
  newpaths.append(new);newradii.append(radius);pairs.append([int(i),int(ids[other])]);added_for_parent+=1
 if fine_density and added_for_parent>=3:
  before_r=original_r[off[i]:off[i+1]]
  new_r[off[i]:off[i+1]]=before_r+(np.minimum(before_r,.000035)-before_r)*smooth((arc-.008)/.025)
assert len(newpaths)>100,'Insufficient compatible infill; do not render empty study'
if fine_density:cu.attributes['radius'].data.foreach_set('value',new_r);cu.update_tag()
hair=bpy.data.hair_curves.new('Fine posterior inter-bundle infill');hair.add_curves([len(q) for q in newpaths])
hair.attributes['position'].data.foreach_set('vector',np.vstack(newpaths).astype(np.float32).ravel())
hair.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.concatenate(newradii).astype(np.float32))
assert len(ob.data.materials)==1
hair.materials.append(ob.data.materials[0]);item=bpy.data.objects.new('Fine posterior inter-bundle infill',hair);bpy.context.scene.collection.objects.link(item);item.matrix_world=ob.matrix_world
out.mkdir(parents=True);np.savez_compressed(out/'local_infill_pairs.npz',pairs=np.array(pairs))
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=256;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['04_Back','05_OppositeSide']:
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
check=np.empty_like(p);cu.attributes['position'].data.foreach_get('vector',check.ravel());assert np.array_equal(check,p) and digest(source)==before
report=dict(source=base,source_sha256=before,source_unchanged=True,original_positions_unchanged=True,model_saved=False,pilot=pilot,candidate_parents=len(ids),added_fibers=len(newpaths),no_compatible_pair=no_pair,rejected_body_gap=rejected,images_sha256=images,method='Add fine18..30micron fibers from compatible original rear paths,midpoint distance4..14mm,target8mm;root separation<=18mm,tip<=25mm,direction dot>=0.92,length ratio0.65..1.5. Blend30..70percent after original root8mm with25mm onset;retain all original fibers. New endpoints interpolate within original pair. Reject any new control/midpoint worsening original sampled body gap beyond min(original,0.2mm)-2microns. Native editable added curve object;not continuous collision,exact scalp binding or art acceptance.')
report.update(fine_density=fine_density,original_radii_unchanged=bool(np.array_equal(new_r,original_r)),original_changed_radius_points=int(np.count_nonzero(new_r!=original_r)))
if fine_density:report['method']+=' Fine-density override: propose four neighbor blends18/38/62/82percent per parent. Only parents with>=3accepted children get original shaft radius capped35microns after root8mm with25mm ramp;positions/lengths unchanged.'
(out/'infill_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INFILL_PREVIEW_FINISHED',version,len(newpaths),flush=True)
