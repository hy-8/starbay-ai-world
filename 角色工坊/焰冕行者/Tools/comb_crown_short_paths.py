"""Recomb inspected short high crown fibers using existing roots and arc budgets."""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(r'D:\星湾世界_模型归档\starbay-ai-world\角色工坊\焰冕行者')
a=sys.argv[sys.argv.index('--')+1:];version,base,selection=a[:3]
assert all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in a[:3])
save='--save' in a;save_only='--save-only' in a;assert not save_only or save
max_arc=.150 if '--high-tips' in a else .065
root_loft='--root-loft' in a
feather_projection='--feather-projection' in a;assert not feather_projection or root_loft
out=ARCHIVE/'Renders'/version;modeldir=ARCHIVE/'Exports'/version
assert not out.exists() and (not save or not modeldir.exists())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'Exports'/base/'Ember_Regent.blend';before=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
name='Bystedt layercut derivative • native root reflow';ob=bpy.data.objects[name];cu=ob.data
assert np.array_equal(np.array(ob.matrix_world),np.eye(4))
old=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',old.ravel());p=old.copy()
counts=np.array([c.points_length for c in cu.curves]);off=np.r_[0,np.cumsum(counts)]
folder=ARCHIVE/'Renders'/selection;sm=json.loads((folder/'edit_id_manifest.json').read_text())
assert sm['source_sha256']==before and sm['edited_object']==name
if feather_projection:
 cam=bpy.data.objects[sm['selection_rule']['camera']];view=np.array(cam.matrix_world.inverted());proj=np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1200,y=1400,scale_x=1,scale_y=1));brush_matrix=proj@view
 cx,cy,rx,ry=sm['selection_rule']['normalized_ellipse']
selected=np.load(folder/'local_projected_indices.npz')['selected']
mask=np.zeros(len(counts),bool);mask[selected]=True
for key in ['native_inner_curtain_shift','native_resculpted_fringe_sweeps','native_curved_projected_tips']:
 flags=np.empty(len(counts),bool);cu.attributes[key].data.foreach_get('value',flags);assert not flags[mask].any()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def gap(v):
 h,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-h).dot(n))
stats=[];used=[]
for i in selected:
 q=old[off[i]:off[i+1]].astype(float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 if not root_loft and not (.008<arc[-1]<=max_arc and q[0,2]>1.850 and q[-1,2]>1.835):continue
 used.append(int(i));rh,rn,_,_=bv.find_nearest(Vector(q[0]))
 heading=Vector(q[-1]-q[0]);heading-=rn*heading.dot(rn)
 if heading.length<.002:
  heading=Vector((1 if q[0,0]>.043 else -1,.35,0));heading-=rn*heading.dot(rn)
 heading.normalize();v=q.copy();last=Vector(q[0])
 # Follow the scalp in substeps so sparse mixed-count controls do not jump across it.
 for j in ([] if root_loft else range(1,len(q))):
  if arc[j]<=.003:last=Vector(q[j]);continue
  remaining=float(arc[j]-arc[j-1]);cursor=float(arc[j-1])
  while remaining>1e-8:
   step=min(.001,remaining);h,n,_,_=bv.find_nearest(last)
   original=Vector(q[j]-q[j-1]);original-=n*original.dot(n)
   target=heading-n*heading.dot(n)
   if original.length<1e-9:original=target.copy()
   if target.length<1e-9:target=original.copy()
   original.normalize();target.normalize();weight=float(smooth((cursor-.003)/.012))
   direction=original*(1-weight)+target*weight
   if direction.length<1e-9:direction=target
   direction.normalize();nh,nn,_,_=bv.find_nearest(h+direction*step)
   oldgap=max(.00055,gap(q[j]));loft=.0015+.0020*np.sin(np.pi*min(1.,(cursor+step)/arc[-1]))
   clearance=oldgap*(1-weight)+min(oldgap,loft)*weight
   last=nh+nn*clearance;cursor+=step;remaining-=step
  v[j]=last
 delta=v-q
 if root_loft:
  brush=np.ones(len(q))
  if feather_projection:
   clip=np.c_[q,np.ones(len(q))]@brush_matrix.T;ndc=clip[:,:3]/clip[:,3,None]
   radius=np.sqrt(((ndc[:,0]*.5+.5-cx)/rx)**2+((.5-ndc[:,1]*.5-cy)/ry)**2)
   brush=1-smooth((radius-.35)/.65)
  for j,x in enumerate(q):
   h,n,_,_=bv.find_nearest(Vector(x));clearance=float((Vector(x)-h).dot(n))
   weight=float(smooth((arc[j]-.003)/.008)*smooth((x[2]-1.850)/.015))
   delta[j]=-np.array(n)*max(0.,clearance-.003)*weight*brush[j]
 delta[arc<=.003]=0
 cap=.008 if root_loft else .012
 magnitude=float(np.linalg.norm(delta,axis=1).max());delta*=min(1.,cap/max(magnitude,1e-12))
 qs=np.vstack([q,(q[:-1]+q[1:])*.5]);ds=np.vstack([delta,(delta[:-1]+delta[1:])*.5]);moving=np.linalg.norm(ds,axis=1)>1e-7
 qs=qs[moving];ds=ds[moving];limits=[min(.0003,gap(x))-1e-6 for x in qs];scale=1.
 for _ in range(8):
  if all(gap(x+d*scale)>=g for x,d,g in zip(qs,ds,limits)):break
  scale*=.5
 else:scale=0.
 p[off[i]:off[i+1]]=q+delta*scale
 stats.append([int(i),scale,float(np.linalg.norm(delta*scale,axis=1).max()),float(arc[-1]),float(np.linalg.norm(np.diff(p[off[i]:off[i+1]].astype(float),axis=0),axis=1).sum())])
assert stats and np.isfinite(p).all() and np.array_equal(p[off[:-1]],old[off[:-1]])
cu.attributes['position'].data.foreach_set('vector',p.ravel());cu.update_tag();modelhash=None
out.mkdir(parents=True);np.savez_compressed(out/'local_crown_comb_stats.npz',stats=np.array(stats),selected=np.array(used))
if save:
 modeldir.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(modeldir/'Ember_Regent.blend'),compress=True);modelhash=digest(modeldir/'Ember_Regent.blend')
s=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=192;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.render.resolution_x,s.render.resolution_y=1200,1400;s.render.resolution_percentage=100
cam=bpy.data.objects['03_Side'].copy();cam.data=cam.data.copy();s.collection.objects.link(cam);cam.name='05_OppositeSide';mirror=Matrix.Diagonal((-1.,1.,1.,1.));cam.matrix_world=mirror@cam.matrix_world@mirror
images={}
for shot in ['03_Side','05_OppositeSide','04_Back','02_ThreeQuarter','01_Front']:
 if save_only:break
 s.camera=bpy.data.objects[shot];dest=out/(shot+'.png');s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);images[dest.name]=digest(dest)
assert digest(source)==before
st=np.array(stats)
m=dict(source=base,source_sha256=before,source_unchanged=True,selection=selection,object=name,selected_fibers=len(used),changed_fibers=int((st[:,2]>1e-7).sum()),scale_quantiles=np.quantile(st[:,1],[0,.5,1]).tolist(),max_displacement_m=float(np.linalg.norm(p-old,axis=1).max()),arc_length_change_quantiles_m=np.quantile(st[:,4]-st[:,3],[0,.5,1]).tolist(),positions_sha256=hashlib.sha256(p.tobytes()).hexdigest(),model_saved=save,model_sha256=modelhash,images_sha256=images,method='Inspected projected primary selection intersect original arc(8,65]mm,rootZ>1.850,tipZ>1.835. Preserve root3mm controls. Scalp-tangent integration in <=1mm substeps; direction blends over12mm toward root-tip chord projected at root. Degenerate tangent falls toward side from partX43mm. Original positive normal offset blends toward 1.5..3.5mm loft. Whole-fiber12mm displacement cap and control/midpoint body-gap backtracking. No topology/radius/material changes; tips and individual arc lengths may change. Not continuous collision or artistic completion.')
m['maximum_original_arc_m']=max_arc
m['changed_fibers_threshold_m']=1e-7
m['exact_changed_fibers']=int(np.count_nonzero(np.logical_or.reduceat(np.any(p!=old,axis=1),off[:-1])))
m['method']=m['method'].replace('(8,65]mm',f'(8,{max_arc*1000:g}]mm')
m['root_loft']=root_loft
m['feather_projection']=feather_projection
if root_loft:m['method']='All inspected crown primary fibers; accepted frontal groups excluded. Keep roots and first3mm controls. Move along original closest-body normal toward3mm positive clearance, weighted by8mm arc onset after3mm and Z1.850..1.865 smooth transition. Whole-fiber8mm cap and body-gap backtracking at controls/midpoints. Controls belowZ1.850 exact. No topology/radius/material changes; upper tips and individual arc lengths can change. Not continuous collision/artistic completion.'
if feather_projection:m['method']+=' Multiply each point by projected ellipse brush, full strength within normalized radius0.35, smoothly zero by radius1; avoids full-fiber selection boundary steps.'
(out/'crown_comb_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
if save:(modeldir/'crown_comb_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('CROWN_COMB_FINISHED',version,len(used),flush=True)
