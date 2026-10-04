"""Trim the inherited undercoat; retain free-form visible outer layers.

Read a protected version, create a fresh candidate. Actual fiber lengths,
not a viewport density change. Crown compression and independent nape bends.
"""
import bpy,sys,json,re
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version,source=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in [version,source]):raise ValueError(args)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports'/source/'Ember_Regent.blend'))
rng=np.random.default_rng(100404)
ob=bpy.data.objects['Scalp rooted coverage beneath sculpted locks'];cu=ob.data
p=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,3)
sizes=np.array([len(c.points) for c in cu.curves]);offset=0;trimmed=[];nr=[];lengths=[]
for size in sizes:
 strand=p[offset:offset+size];offset+=size
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(strand,axis=0),axis=1))]
 if '--support' in args:
  limit=rng.uniform(.040,.064) if strand[0,2]>1.815 else rng.uniform(.026,.045)
 else:limit=rng.uniform(.012,.023)
 length=min(float(arc[-1]),limit);lengths.append(length)
 q=np.linspace(0,length,16);res=np.stack([np.interp(q,arc,strand[:,axis]) for axis in range(3)],axis=1)
 trimmed.append(res);nr.append(np.linspace(.000036,.000003,16))
new=bpy.data.hair_curves.new('True short supporting undercoat');new.add_curves([16]*len(sizes));new.attributes['position'].data.foreach_set('vector',np.array(trimmed,np.float32).ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.array(nr,np.float32).ravel())
for m in cu.materials:new.materials.append(m)
ob.data=new
design=json.loads((ROOT/'Exports'/source/'guide_design.json').read_text(encoding='utf-8'))
outer=bpy.data.objects['Free-space sculpted rock hair'];cu=outer.data
p=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',p);p=p.reshape(-1,72,3)
p[:,:,2]-=np.maximum(0,p[:,:,2]-1.881)*.45
t=np.linspace(0,1,72);idx=0
for g in design:
 count=g['count']
 if g['zone']=='nape':
  fall=np.maximum(0,(t-.48)/.52)**1.35;phase=rng.uniform(0,6.28)
  p[idx:idx+count,:,2]-=fall[None,:]*rng.uniform(.035,.065)
  p[idx:idx+count,:,1]+=.014*fall[None,:]
  p[idx:idx+count,:,0]+=.006*np.sin(t*7+phase)[None,:]*fall[None,:]
 idx+=count
cu.attributes['position'].data.foreach_set('vector',p.ravel())
if '--shaft' in args:
 r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,72)
 # Keep thickness through the shaft; the old profile thinned much too early,
 # leaving long locks almost transparent before reaching their tips.
 r=r[:,0:1]*(1-.985*t[None,:]**4)**.60
 cu.attributes['radius'].data.foreach_set('value',r.astype(np.float32).ravel())
go=bpy.data.objects['Visible layer design guides']
for sp,g in zip(go.data.splines,design):
 phase=rng.uniform(0,6.28)
 for point,u in zip(sp.points,t):
  point.co.z-=max(0,point.co.z-1.881)*.45
  if g['zone']=='nape':
   fall=max(0,(u-.48)/.52)**1.35;point.co.z-=.05*fall;point.co.y+=.014*fall;point.co.x+=.006*np.sin(u*7+phase)*fall
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=192;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
report={'version':version,'source':source,'support_layers':'--support' in args,'gentler_shaft_taper':'--shaft' in args,'method':'undercoat physically cut by root zone; compressed crown peaks; independently extended wavy nape','undercoat_strands':len(sizes),'undercoat_length_range_m':[min(lengths),max(lengths)],'status':'candidate requiring all-angle review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FINISHED_FREEFORM',version,flush=True)
