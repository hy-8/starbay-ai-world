"""Cut saved continuous posterior hair paths to a layered nape silhouette.

No cap replacement or new noise hairstyle. Source geometry and local grouping
indices remain local. First four points, explicit front-frame61 and all other
hair components are retained. The default retains all legacy fringe; all-low
mode also cuts long side/nape ends within the older fringe classification.
"""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base,probe=a[:3]
all_low='--all-low' in a
repair_low_entries='--repair-low-entries' in a
assert not repair_low_entries or all_low, 'Entry repair requires actual low-tip selection'
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
assert not out.exists() and not render.exists()
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy()
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
frame=np.empty(len(cu.curves),bool);cu.attributes['native_front_frame_sculpture'].data.foreach_get('value',frame)
groups=np.load(ROOT/'Exports'/probe/'local_flow_groups.npz');ids=groups['ids'];labels=groups['labels']
assert np.array_equal(ids,np.flatnonzero(front<0))
family=np.full(len(raw),-1);family[ids]=labels
family[front>=0]=front[front>=0]+96
eligible=(front<0)&(~frame)&(raw[:,0,1]>-.070)&(raw[:,-1,1]>-.005)&(raw[:,-1,2]<1.710)
if all_low:eligible=(~frame)&(raw[:,-1,2]<1.710)
mask=np.zeros(len(raw),bool);removed=[];length_ratios=[];cuts=[]
for i in np.flatnonzero(eligible):
 old=raw[i];g=int(family[i]);phase=g*2.399963
 # A longer central nape and slightly shorter sides, with coherent whole-lock
 # variation. A small per-fiber variation avoids a perfectly straight edge.
 side=np.clip(abs(old[-1,0])/.105,0,1)
 target=1.677+.027*side+.006*np.sin(phase)+.003*np.sin(i*2.399963)
 if all_low:target=1.671+.023*side+.017*np.sin(phase)+.005*np.sin(i*2.399963)
 if repair_low_entries:target=min(target,old[3,2]-.012)
 start=4 if repair_low_entries else 12
 below=np.flatnonzero(old[start:,2]<target)+start
 if not len(below):continue
 j=int(below[0]);before=old[j-1];after=old[j]
 f=(before[2]-target)/max(before[2]-after[2],1e-9)
 if not 0<=f<=1:continue
 end=before*(1-f)+after*f
 tail=np.vstack([old[3:j],end])
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(tail,axis=0),axis=1))]
 total=np.linalg.norm(np.diff(old,axis=0),axis=1).sum()
 if arc[-1] < (.003 if repair_low_entries else .018):continue
 at=np.linspace(0,arc[-1],62)[1:]
 q[i,4:]=np.column_stack([np.interp(at,arc,tail[:,k]) for k in range(3)])
 new=np.linalg.norm(np.diff(q[i],axis=0),axis=1).sum()
 mask[i]=True;removed.append(total-new);length_ratios.append(new/total);cuts.append(target)
assert mask.sum()>100 and np.isfinite(q).all()
assert np.array_equal(q[:,:4],raw[:,:4]) and np.array_equal(q[~mask],raw[~mask])
assert np.array_equal(q[frame],raw[frame])
if not all_low:assert np.array_equal(q[front>=0],raw[front>=0])
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_nape_layer_cut';ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask)
out.mkdir(parents=True);render.mkdir(parents=True);s=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide'
ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for name in ['02_ThreeQuarter','04_Back','05_OppositeSide']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(out/'nape_cut_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,probe=probe,
 changed_fibers=int(mask.sum()),eligible_fibers=int(eligible.sum()),selection_attribute=attr,
 first_four_points_exact=True,all_front_frame_exact=True,all_fringe_exact=not all_low,all_low=all_low,repair_low_entries=repair_low_entries,unselected_primary_exact=True,other_hair_unchanged=True,
 tip_elevation_quantiles_m=np.quantile(cuts,[0,.5,.9,1]).tolist(),
 removed_arc_quantiles_m=np.quantile(removed,[0,.5,.9,1]).tolist(),retained_length_ratio_quantiles=np.quantile(length_ratios,[0,.5,.9,1]).tolist(),
 method=('All actual primary tips below1.710m excluding explicit front-frame61; actual old frontal guide families and96 posterior whole-path families,17mm coherent layer variation plus5mm per-fiber scatter' if all_low else 'Posterior low-tip shafts only; coherent96 whole-path-family height variation')+'; central longer nape and shorter sides. Cut at first existing-path intersection with target elevation, resample continuous remaining tail after retained first4points; no new curl or scalp cap.'+(' Low-entry fix: search begins at point4 instead of12; target capped12mm below retained point3, minimum remaining tail3mm. Source67 geometric aggregate plus66 actual ID images attribute missed low-root long tails to primary.' if repair_low_entries else ''),
 status='Actual drafts pending review',scope='Local static cut, not continuous/body/eye/clothing/animation collision or art acceptance'),indent=2),encoding='utf-8')
print('NAPE_LAYER_CUT_SAVED',version,int(mask.sum()),flush=True)
