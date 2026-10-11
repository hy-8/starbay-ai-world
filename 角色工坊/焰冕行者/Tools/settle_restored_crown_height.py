"""Softly settle only excess height in newly restored non-fringe strands."""
import bpy,sys,re,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];version,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:2])
source=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
out=ROOT/'Exports'/version;rd=ROOT/'Renders'/version;assert not out.exists() and not rd.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['Bystedt layercut derivative • native root reflow'];cu=ob.data
p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());raw=p.reshape(-1,65,3).astype(float)
restored=np.empty(len(raw),bool);cu.attributes['native_restored_nonfringe_flow'].data.foreach_get('value',restored)
mask=restored&(raw[:,:,2].max(1)>1.877);ids=np.flatnonzero(mask);assert len(ids)>100
q=raw.copy();t=np.linspace(0,1,65);u=np.clip((t-t[9])/.15,0,1);fade=u*u*(3-2*u)
e=np.maximum(raw[mask,:,2]-1.877,0);q[mask,:,2]-=.70*e*e/(e+.005)*fade
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get());repairs=0
for i in ids:
    for j in np.flatnonzero(q[i,:,2]!=raw[i,:,2]):
        hit,n,_,dist=bv.find_nearest(Vector(q[i,j]));gap=(Vector(q[i,j])-hit).dot(n)
        if dist<.025 and gap<.002:q[i,j]=np.array(hit+n*.002);repairs+=1
assert np.array_equal(q[:,:10],raw[:,:10]) and np.array_equal(q[~mask],raw[~mask]) and np.isfinite(q).all()
ob.data=cu.copy();ob.data.attributes['position'].data.foreach_set('vector',q.astype(np.float32).ravel())
attr='native_settled_restored_crown';assert not ob.data.attributes.get(attr)
ob.data.attributes.new(attr,'BOOLEAN','CURVE').data.foreach_set('value',mask);ob.data.update_tag()
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
out.mkdir(parents=True);rd.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'),compress=True)
(out/'settled_crown_manifest.json').write_text(json.dumps(dict(source=base,source_sha256=digest,selected_fibers=len(ids),selection_attribute=attr,preserved_prefix_points=10,sampled_body_repairs=repairs,max_displacement_m=float(np.linalg.norm(q-raw,axis=2).max()),method='Only210 restored non-fringe strands with maxZ>1.877m. For each point excess e=max(z-1.877,0),subtract.70*e^2/(e+.005);fade in over15% parameter after first10 points. True roots/prefix retained.2mm sampled body guard,not continuous collision proof.'),indent=2),encoding='utf-8')
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';ref=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=ref@cam.matrix_world@ref
for shot in ['03_Side','02_ThreeQuarter','04_Back','05_OppositeSide']:
    s.camera=bpy.data.objects[shot];s.render.filepath=str(rd/(shot+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('RESTORED_CROWN_SETTLED',version,len(ids),flush=True)
