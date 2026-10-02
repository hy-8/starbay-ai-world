"""Remove a failed surface groom; retain the coherent scalp and fringe layers."""
import bpy,sys,re,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION
if OUT.exists():raise RuntimeError('Fresh directory required')
OUT.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier08/Ember_Regent.blend'))
bpy.data.objects.remove(bpy.data.objects['Layered auburn guide groom'],do_unlink=True)
o=bpy.data.objects['Continuous scalp coverage groom'];cu=o.data
xyz=np.empty(len(cu.points)*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,56,3)
rng=np.random.default_rng(991);t=np.linspace(0,1,56)[None,:];phase=rng.uniform(0,6.28,(len(xyz),1))
xyz[:,:,0]+=.0016*np.sin(t*14+phase)*np.sin(np.pi*t)
xyz[:,:,1]+=.0010*np.sin(t*18+phase)*np.sin(np.pi*t)
cu.attributes['position'].data.foreach_set('vector',xyz.ravel())
fly=xyz[::90].copy();t=np.linspace(0,1,56)[None,:]
fly[:,:,0]+=rng.normal(0,.003,(len(fly),1))*np.sin(np.pi*t)
fly[:,:,1]+=rng.normal(0,.004,(len(fly),1))*np.sin(np.pi*t)
fly[:,:,2]+=.0025*np.sin(np.pi*t)
new=bpy.data.hair_curves.new('Fine separated flyaway fibers');new.add_curves([56]*len(fly));new.attributes['position'].data.foreach_set('vector',fly.ravel());new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.broadcast_to(.000022*(1-.95*t)**.6,(len(fly),56)).astype(np.float32).ravel());new.materials.append(cu.materials[0]);ob=bpy.data.objects.new('Sparse natural silhouette hairs',new);bpy.data.collections['05_Hair'].objects.link(ob)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
usage=json.loads((ROOT/'Exports/atelier08/asset_usage.json').read_text(encoding='utf-8'));usage.update({'source':'atelier08','version':VERSION,'groom':'retained continuous scalp coverage, diagonal fringe and separated flyaways; rejected outer guide shell removed','status':'WIP, not reference quality or approved for release'})
(OUT/'asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
print('STUDY_SAVED',str(OUT),flush=True)
