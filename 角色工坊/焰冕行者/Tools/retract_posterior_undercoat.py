"""Retract posterior support along its own paths, preserving roots and side coverage."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Original posterior coverage • surface-grown short fibers'];cu=ob.data
assert all(c.points_length==36 for c in cu.curves)
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,36,3).astype(float)
roots=raw[:,0];length=np.linalg.norm(np.diff(raw,axis=1),axis=2).sum(1)
mask=(roots[:,1]>.025)&(roots[:,2]>1.790)&(length>.040)
if '--pilot' in a: mask&=roots[:,0]<-.005
ids=np.flatnonzero(mask);assert len(ids)>500
q=raw.copy();lengths=[]
for i in ids:
    r=roots[i];b=float(np.clip((r[1]-.025)/.025,0,1));b=b*b*(3-2*b)
    target=.022+.012*(.5+.5*np.sin(r[0]*81+r[1]*103))
    end=length[i]+b*(min(length[i],target)-length[i])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw[i],axis=0),axis=1))]
    q[i]=np.column_stack([np.interp(np.linspace(0,end,36),arc,raw[i,:,k]) for k in range(3)])
    q[i,0]=r;lengths.append(np.linalg.norm(np.diff(q[i],axis=0),axis=1).sum())
assert np.array_equal(q[:,0],raw[:,0]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_retracted_posterior_undercoat';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
out.mkdir(parents=True);rd.mkdir(parents=True)
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
(out/'retracted_undercoat_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,changed_object=ob.name,selection_attribute=attr,selected_fibers=len(ids),pilot='--pilot' in a,old_length_quantiles_m=np.quantile(length[ids],[0,.5,1]).tolist(),result_length_quantiles_m=np.quantile(lengths,[0,.5,1]).tolist(),method='Existing support rootsY>25mm,Z>1.790m,old arc>40mm. Blend shortening by rootY25-50mm; target22-34mm spatial field. Resample each own source polyline; true roots, radii, topology and all other objects retained. Not exact rendered arc or continuous collision proof.'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['04_Back','03_Side','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('RETRACTED_UNDERCOAT_RENDERED',version,len(ids),flush=True)
