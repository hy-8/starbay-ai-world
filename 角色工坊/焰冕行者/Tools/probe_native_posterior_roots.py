"""Read-only posterior root-to-peak aggregates; no visibility inference."""
import bpy, sys, re, json, hashlib
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--')+1:]
version, base = a[:2]
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a[:2])
out = ROOT/'Exports'/(version+'.json')
assert not out.exists()
source = ROOT/'Exports'/base/'Ember_Regent.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
ob = bpy.data.objects['Bystedt layercut derivative • native root reflow']
cu = ob.data
p = np.empty((len(cu.points), 3), np.float32)
cu.attributes['position'].data.foreach_get('vector', p.ravel())
p = p.reshape(-1, 65, 3)
def flag(n):
    v = np.empty(len(p), bool)
    cu.attributes[n].data.foreach_get('value', v)
    return v
fringe, upper = flag('native_resculpted_fringe_sweeps'), flag('native_descending_fine_locks')
other = ~(fringe|upper)
rise = p[:, :, 2].max(1)-p[:, 0, 2]
records = []
def quant(v): return np.quantile(v, [0, .1, .5, .9, 1], axis=0).tolist() if len(v) else []
for name, mask in [('other_primary', other), ('other_posterior_low_roots', other&(p[:, 0, 1] > -.015)&(p[:, 0, 2] < 1.800)), ('other_posterior_low_rising', other&(p[:, 0, 1] > -.015)&(p[:, 0, 2] < 1.800)&(rise > .035)), ('upper', upper)]:
    z = p[mask]
    records.append(dict(region=name, fibers=int(mask.sum()), root_xyz_quantiles_m=quant(z[:, 0]), tip_xyz_quantiles_m=quant(z[:, -1]), elevation_above_root_quantiles_m=quant(rise[mask]), shafts_rising_over35mm=int((rise[mask] > .035).sum())))
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
out.write_text(json.dumps(dict(source=base, source_sha256=digest, source_unchanged=True, records=records, scope='Saved path elevation relative to actual roots. No all-view visibility, scalp attachment or aesthetic acceptance inference.'), indent=2), encoding='utf-8')
print('POSTERIOR_ROOT_RISE_PROBED', json.dumps(records), flush=True)
