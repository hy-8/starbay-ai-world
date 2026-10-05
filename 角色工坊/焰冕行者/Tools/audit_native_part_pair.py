"""Only compare local side-part edits against their saved source."""
import bpy,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];output=ROOT/'Exports/native_part_pair07.json'
if output.exists():raise RuntimeError('Fresh pair audit required')
name='Bystedt layercut derivative • native root reflow'
def read(version):
 path=ROOT/'Exports'/version/'Ember_Regent.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 data=bpy.data.objects[name].data;p=np.empty((len(data.points),3),np.float32);data.attributes['position'].data.foreach_get('vector',p.ravel())
 return p.reshape(-1,65,3),hashlib.sha256(path.read_bytes()).hexdigest()
before,beforehash=read('nativefrontwave10');after,afterhash=read('nativepart12')
data=bpy.data.objects[name].data;mask=np.empty(len(data.curves),bool);data.attributes['native_part_cover'].data.foreach_get('value',mask)
assert np.array_equal(before[:,0],after[:,0]) and np.array_equal(before[~mask],after[~mask])
output.write_text(json.dumps(dict(source='nativefrontwave10',source_sha256=beforehash,candidate='nativepart12',candidate_sha256=afterhash,changed_fibers=int(mask.sum()),all_roots_exactly_equal=True,unselected_primary_exactly_equal=True,scope='Static local coordinate pair; no artistic or collision approval'),indent=2),encoding='utf-8')
print('NATIVE_PART_PAIR_PASS',flush=True)
