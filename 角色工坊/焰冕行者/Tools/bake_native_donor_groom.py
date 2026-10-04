"""Bake the CC0 donor's evaluated curves without changing modifier settings.

Requires the locally licensed Hair Editor library. Never overwrites a cache.
The unmodified source control distinguishes donor defects from fitting bugs.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Source/HairEditorCC0/hair/haireditor/hair.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));records=[]
for name in ['basic_short_hair','straight_hair_to_shoulder']:
 ob=bpy.data.objects[name];cu=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
 p=np.empty(len(cu.points)*3,np.float32);cu.attributes['position'].data.foreach_get('vector',p)
 r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
 sizes=np.array([len(c.points) for c in cu.curves],np.int32)
 path=ROOT/'Source/HairEditorCC0'/('native_'+name+'_evaluated.npz')
 if not path.exists():np.savez_compressed(path,positions=p.reshape(-1,3),radii=r,sizes=sizes,matrix=np.array(ob.matrix_world))
 else:
  old=np.load(path)
  if not np.array_equal(old['positions'],p.reshape(-1,3)) or not np.array_equal(old['radii'],r):raise RuntimeError('Existing cache differs; choose a fresh source folder')
 records.append({'style':name,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'curves':len(sizes),'points':len(r),'modifier_changes':'none'})
report={'source':'https://files2.makehumancommunity.org/functional/haireditor.zip','author':'Tomas Klecer','license':'CC0','license_evidence':'https://static.makehumancommunity.org/assets/assetpacks/index.html','library_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'files':records}
dest=ROOT/'Source/native_donor_groom_sources.json'
if dest.exists():raise RuntimeError('Existing provenance preserved')
dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('NATIVE_DONOR_BAKED',len(records),flush=True)
