"""Read every saved particle's complete keys; compare with first-cache bake.
This is ordinary read-only existing-geometry inspection, not generative input.
"""
import bpy,json,hashlib,collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Source/FabMediumLayered/hairstyle.blend'
output=ROOT/'Source/FabMediumLayered/complete_key_audit01.json'
if output.exists():raise RuntimeError('Preserve audit')
old=np.load(ROOT/'Source/FabMediumLayered/fabcontrol01/licensed_particle_paths.npz')['positions']
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=bpy.data.objects['HairStyle'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());rows=[];offset=0
for ps in ev.particle_systems:
 counts=collections.Counter();lengths=[];rootdelta=[];tipdelta=[];keys_total=0
 for i,particle in enumerate(ps.particles):
  q=np.array([k.co[:] for k in particle.hair_keys],np.float32)
  counts[len(q)]+=1;keys_total+=len(q)
  assert len(q)>1 and np.isfinite(q).all()
  lengths.append(float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum()))
  rootdelta.append(float(np.linalg.norm(q[0]-old[offset+i,0])))
  tipdelta.append(float(np.linalg.norm(q[-1]-old[offset+i,-1])))
 rows.append(dict(name=ps.name,actual_key_count_distribution=dict(sorted(counts.items())),total_keys=keys_total,
  complete_key_length_quantiles_m=np.quantile(lengths,[0,.1,.5,.9,.99,1]).tolist(),
  baked_root_difference_quantiles_m=np.quantile(rootdelta,[0,.5,.9,.99,1]).tolist(),
  baked_tip_difference_quantiles_m=np.quantile(tipdelta,[0,.5,.9,.99,1]).tolist()))
 offset+=len(ps.particles)
report=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),all_particles_read=offset,groups=rows,
 purpose='Test whether using first particle cache step count truncated other hairs. Complete keys compared against bake 01.')
output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
