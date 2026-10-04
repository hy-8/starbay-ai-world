"""Replace broad authored fringe guides with independently falling fine locks.

Original project control data only. Keeps actual 3D shape authorship separate
from donor support hair and requires neutral render inspection after baking.
"""
import json, sys
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
folder = root / 'Source/HairReconstruction'
source = folder / 'concert_fringe_control13.json'
target = folder / sys.argv[1]
if target.exists() or target.parent != folder or target.suffix != '.json':
    raise RuntimeError('Fresh original JSON required')
records = json.loads(source.read_text(encoding='utf-8'))
rng = np.random.default_rng(100438)
result = []
for record in records:
    p = np.asarray(record['control_points_m'], float)
    name = record['name']
    if 'segmented crown' in name:
        result.append(record)
        continue
    u = np.linspace(0, 1, len(p))
    side = 1 if 'light' in name else -1
    for layer in range(3):
        # Move independent roots along the scalp instead of duplicating a
        # single thick patch. Short locks expose medium and longer ones.
        cut = [rng.uniform(.72,.84), rng.uniform(.88,.96), 1.][layer]
        q = np.linspace(0, cut, 9)
        pts = np.stack([np.interp(q, u, p[:, j]) for j in range(3)], axis=1)
        t = np.linspace(0, 1, len(pts))
        pts[:, 0] += (layer-1)*.004*(.65+.35*t)
        pts[:, 1] += (layer-1)*.003*np.sin(np.pi*t)
        # Independent gentle bends in depth, not just flat screen-space S's.
        pts[:, 1] += rng.uniform(-.004,.004)*np.sin(np.pi*t)
        pts[:, 0] += side*rng.uniform(-.002,.003)*np.sin(np.pi*t*1.35)
        pts[:, 2] += rng.uniform(-.001,.003)*np.sin(np.pi*t)
        # Short tips sweep laterally; fewer full-length U-turns at the brows.
        if layer==0:
            pts[-2:, 0] += side*np.array([.002,.005])
            pts[-1, 2] += .002
        result.append({'name': name+' / fine independent '+str(layer+1),
                       'control_points_m': np.round(pts,6).tolist()})
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('ORIGINAL_FINE_FRINGE_DESIGN',len(result),str(target))
