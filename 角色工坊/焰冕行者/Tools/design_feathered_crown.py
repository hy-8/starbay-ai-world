"""Derive original, staggered lateral crown guides from the project control map.

This changes guide geometry, not a render filter. No licensed donor vertices
are read or written. Output remains a study requiring actual 3D review.
"""
import json, sys
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
source = root / 'Source/HairReconstruction/concert_fringe_control12.json'
target = root / 'Source/HairReconstruction' / sys.argv[1]
if target.exists() or target.parent != source.parent or target.suffix != '.json':
    raise RuntimeError('Fresh original control JSON required in HairReconstruction')
records = json.loads(source.read_text(encoding='utf-8'))
rng = np.random.default_rng(100434)
result = []
for i, record in enumerate(records):
    p = np.asarray(record['control_points_m'], float)
    name = record['name']
    if 'segmented crown' in name:
        side = 1 if 'light' in name else -1
        # Alternating short lateral cuts and long falling cuts replace paired
        # parallel crown ribbons. Each family has a different end silhouette.
        short = name.endswith('1')
        u = np.linspace(0, 1, len(p))
        if short:
            q = u * rng.uniform(.63, .81)
            p = np.stack([np.interp(q, u, p[:, j]) for j in range(3)], axis=1)
            p[:, 0] += side * rng.uniform(.008, .015) * u**1.4
            p[:, 1] += rng.uniform(.006, .018) * u
            p[:, 2] += rng.uniform(.003, .007) * np.sin(np.pi*u)
            p[-1, 0] += side*.007
            p[-1, 2] += .003
        else:
            p[:, 0] += side*rng.uniform(.002, .006)*np.sin(u*np.pi*1.4)
            p[:, 1] += rng.uniform(-.004, .004)*np.sin(np.pi*u)
            p[:, 2] -= rng.uniform(.001, .004)*np.sin(np.pi*u)
            p[-1, 0] += side*rng.uniform(.001, .004)
        # Independent root locations and one gradual low-frequency bend.
        p[0, 1] += rng.uniform(-.007, .010)
        p[0, 0] += rng.uniform(-.004, .004)
        p[:, 2] += rng.uniform(-.002, .002)*np.sin(np.pi*u)
        name += ' / lateral scissor layer' if short else ' / falling layer'
    else:
        # Keep recognizable framing, but stop every brow lock ending in the
        # same U turn. Changes taper in from midway and leave scalp roots alone.
        u = np.linspace(0, 1, len(p))
        side = 1 if 'light' in name else -1
        p[:, 0] += rng.uniform(-.003, .003)*u**2
        p[:, 2] += rng.uniform(-.002, .006)*u**2
        if 'temple' in name:
            p[:, 0] += side*.003*u**2
            p[-1, 1] += .003
    result.append({'name': name, 'control_points_m': np.round(p, 6).tolist()})
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('ORIGINAL_CROWN_DESIGN', str(target), len(result))
