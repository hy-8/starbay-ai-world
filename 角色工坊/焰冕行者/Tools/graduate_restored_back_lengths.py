"""Graduate the restored posterior haircut along existing paths, without reshaping roots."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2];pilot='--pilot' in a
all_back='--all-back' in a
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float)
protected=np.zeros(len(raw),bool)
for n in ['native_resculpted_fringe_sweeps','native_inner_curtain_shift']:
 f=np.empty(len(raw),bool);cu.attributes[n].data.foreach_get('value',f);protected|=f
r=raw[:,0];lengths=np.linalg.norm(np.diff(raw,axis=1),axis=2).sum(1)
mask=(~protected)&(r[:,1]>-.005)&(raw[:,32,1]>.015)&(raw[:,-1,2]<1.790)&(lengths>.065)
if all_back:mask=(~protected)&(raw[:,-1,1]>.005)&(raw[:,-1,2]<1.790)&(lengths>.065)
if pilot:mask&=r[:,0]<-.005
ids=np.flatnonzero(mask);assert len(ids)>1000
q=raw.copy();removed=[]
for i in ids:
 old=raw[i];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
 h=float(np.clip((r[i,2]-1.765)/.105,0,1));h=h*h*(3-2*h)
 field=.5+.5*np.sin(r[i,0]*117+r[i,1]*83)*np.cos(r[i,2]*131-r[i,0]*71)
 rate=.07+.19*h+.10*field+.014*np.sin(i*2.399963)
 end=max(arc[11]+.012,arc[-1]*(1-rate));assert end<arc[-1]
 at=np.linspace(arc[11],end,54)[1:]
 q[i,12:]=np.column_stack([np.interp(at,arc,old[:,k]) for k in range(3)])
 removed.append(float(arc[-1]-np.linalg.norm(np.diff(q[i],axis=0),axis=1).sum()))
assert np.array_equal(q[:,:12],raw[:,:12]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_graduated_restored_back';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
method='Exclude accepted fringe/curtain. rootY>-5mm,midY>15mm,tipZ<1.790m,polyline length>65mm;pilot negativeX. Shorten own source polyline by7%+up-to19% root-height term+0-10% coherent root field+/-1.4% per-fiber variation. Keep first12 points, resample remaining suffix to shorter arc. No new curls or shared cutting plane; source polyline arc is not exact rendered arc or continuous collision proof.'
if all_back:method=method.replace('rootY>-5mm,midY>15mm','tipY>5mm regardless of rootY')
(out/'graduated_back_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selected_fibers=len(ids),selection_attribute=attr,pilot=pilot,all_back=all_back,preserved_prefix_points=12,removed_polyline_length_quantiles_m=np.quantile(removed,[0,.5,1]).tolist(),method=method),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in (['04_Back','05_OppositeSide'] if pilot else ['04_Back','03_Side','05_OppositeSide','02_ThreeQuarter']):
 s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('GRADUATED_BACK_RENDERED',version,len(ids),flush=True)
