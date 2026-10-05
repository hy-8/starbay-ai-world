"""Scalp-root bands give existing crown shafts genuinely different cut lengths."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
whole='--all-side-back' in a
if not all(re.fullmatch('[A-Za-z0-9_-]+',x) for x in a[:2]):raise ValueError(a)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh layered cut required')
source=ROOT/'Exports'/base/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
assert all(c.points_length==65 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel())
raw=p.reshape(-1,65,3).astype(float);q=raw.copy();root=raw[:,0]
front=np.empty(len(cu.curves),np.int32);cu.attributes['native_front_guide_index'].data.foreach_get('value',front)
# Select upper crown non-fringe roots; lower lengths keep the medium silhouette.
ids=np.flatnonzero((front<0)&(root[:,2]>1.834))
if whole:
 ids=np.flatnonzero(front<0)
 grouping=np.c_[np.round(root[ids]/.010).astype(int),np.round(raw[ids,-1]/.018).astype(int)]
else:grouping=np.round(root[ids]/.0075).astype(int)
labels,inv=np.unique(grouping,axis=0,return_inverse=True)
t=np.linspace(0,1,65);rows=[];cut_mask=np.zeros(len(raw),bool)
for g in range(len(labels)):
 members=ids[inv==g];old=raw[members];r=old[:,0].mean(axis=0)
 # Real root elevation bands: short crown, middle layer, lower perimeter.
 if r[2]>1.861:ratio=.66
 elif r[2]>1.850:ratio=.78
 else:ratio=.90
 if whole:ratio=float(np.clip(1-(r[2]-1.802)*3.0,.75,.98))
 # Alternate back part leaves enough full-length outer fibers between layers.
 if not whole and r[1]>.044 and r[2]<1.855:continue
 values=[]
 for path in old:
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
  assert arc[-1]>0
  values.append(np.column_stack([np.interp(t*arc[-1]*ratio,arc,path[:,j]) for j in range(3)]))
 values=np.array(values);center=values.mean(axis=0)
 # Narrow cut ends rather than leave the broad truncated native sheet.
 fade=np.clip((t-.62)/.38,0,1);fade=fade*fade*(3-2*fade)
 values=center[None]+(values-center[None])*(1-.55*fade)[None,:,None]
 tangent=np.gradient(center,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
 outward=center-np.array([0,-.035,1.776]);outward-=tangent*np.sum(outward*tangent,axis=1)[:,None];outward/=np.maximum(np.linalg.norm(outward,axis=1)[:,None],1e-8)
 if whole:
  across=np.cross(tangent,outward);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-8)
  phase=np.arctan2(r[0],r[1]+.035)*2+(r[2]-1.802)*75
  wave=.006*np.sin(2.2*np.pi*t+phase)*np.sin(np.pi*t)**1.5
  values+=across[None]*wave[None,:,None]
 # Soft feather flick in the final quarter, retaining inherited larger waves.
 values+=outward[None]*(.004*np.sin(np.pi*np.clip((t-.72)/.28,0,1)))[None,:,None]
 values[:,0]=old[:,0];q[members]=values;cut_mask[members]=True
 rows.append(dict(fibers=len(members),length_ratio=ratio,source_median_length_m=float(np.median(np.linalg.norm(np.diff(old,axis=1),axis=2).sum(axis=1))),cut_median_length_m=float(np.median(np.linalg.norm(np.diff(values,axis=1),axis=2).sum(axis=1)))))
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~cut_mask],raw[~cut_mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
ob.data.attributes.new('native_crown_cut','BOOLEAN','CURVE').data.foreach_set('value',cut_mask)
out.mkdir(parents=True);render.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter','03_Side','04_Back']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'crown_cut_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changed_fibers=int(cut_mask.sum()),root_band_cuts=rows,all_side_back=whole,all_roots_exactly_retained=True,unselected_primary_exactly_retained=True,other_native_objects_unchanged=True,method='Root/end-flow partitions, continuous .75-.98 arc-length layers, small 6mm coherent cross-flow wave by actual scalp angle/elevation, narrowed ends; designed fringe retained' if whole else 'Real follicle elevation bands .66/.78/.90 arc-length cuts, preserved full-length lower back, narrowed cut tips and soft 4mm final feather flick',status='Unreviewed actual layered-cut study',scope='Cut-length design only; no exhaustive collision or artistic approval'),indent=2),encoding='utf-8')
print('NATIVE_CROWN_CUT_SAVED',version,int(cut_mask.sum()),len(rows),flush=True)
