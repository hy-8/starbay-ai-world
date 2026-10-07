"""Paired discrete turn/segment evidence; local indices are not synchronized."""
import bpy, sys, re, json, hashlib, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]; version, base, candidate, attribute = a
assert all(re.fullmatch('[A-Za-z0-9_-]+', v) for v in a)
out = ROOT / 'Exports' / version; assert not out.exists()
def read(ver):
    path = ROOT / 'Exports' / ver / 'Ember_Regent.blend'; digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    cu = bpy.data.objects['Bystedt layercut derivative • native root reflow'].data
    p = np.empty((len(cu.points), 3), np.float32); cu.attributes['position'].data.foreach_get('vector', p.ravel())
    return p.reshape(-1, 65, 3), digest
old, oldhash = read(base); new, newhash = read(candidate)
cu = bpy.data.objects['Bystedt layercut derivative • native root reflow'].data
mask = np.empty(len(new), bool); cu.attributes[attribute].data.foreach_get('value', mask)
def turns(p):
    d = np.diff(p.astype(float), axis=1); lengths = np.linalg.norm(d, axis=2)
    n = d / np.maximum(lengths[..., None], 1e-10)
    angles = np.degrees(np.arccos(np.clip(np.sum(n[:, :-1] * n[:, 1:], axis=2), -1, 1)))
    return lengths, angles
ol, oa = turns(old); nl, na = turns(new)
# This is only a finite-point shape diagnostic, not a physical collision proof.
bad = (na > 85) & ((na - oa) > 30) & (new[:, 1:-1, 2] > 1.860)
bad[:, 43:] = False; flagged = mask & bad.any(axis=1)
peak = new[:, :, 2].max(axis=1); extreme = mask & (peak > 1.900)
def quant(v): return np.quantile(v, [0, .5, .9, .99, 1]).tolist() if len(v) else []
out.mkdir(parents=True)
np.savez_compressed(out/'local_continuity_flags.npz', flagged=flagged, extreme=extreme)
summary = dict(source=base, source_sha256=oldhash, candidate=candidate, candidate_sha256=newhash,
    selected_fibers=int(mask.sum()), upper_new_sharp_turn_fibers=int(flagged.sum()),
    selected_peaks_above_1_900m=int(extreme.sum()), source_selected_peak_quantiles_m=quant(old[mask, :, 2].max(axis=1)),
    candidate_selected_peak_quantiles_m=quant(peak[mask]),
    source_selected_max_turn_quantiles_deg=quant(oa[mask].max(axis=1)),
    candidate_selected_max_turn_quantiles_deg=quant(na[mask].max(axis=1)),
    candidate_max_turn_of_flagged_quantiles_deg=quant(na[flagged].max(axis=1)),
    method='Saved65-point shafts; flag new turns>85deg and increase>30deg, vertexZ>1.860m, vertex index1-43, within declared edited set. Separate geometric peak>1.900m flag. No visibility inference.',
    scope='Discrete geometric diagnostic; local flags only. No continuous curve/segment/body/animation or art acceptance.')
(out/'continuity_probe.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print('CONTINUITY_PROBE', json.dumps(summary), flush=True)
