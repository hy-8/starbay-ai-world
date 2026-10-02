"""Fit a continuous undergroom and separate layered flyaway fibers."""
import bpy,sys,re,json,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION
if OUT.exists():raise RuntimeError('Fresh output required')
OUT.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier06/Ember_Regent.blend'))
hair=bpy.data.objects['Layered auburn guide groom'];cu=hair.data
xyz=np.empty(len(cu.points)*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,64,3)
rng=np.random.default_rng(307)
# Reduce the overly high arch of the prior crown guides; underlying coverage is
# loaded separately. Keep this as a sparse secondary layer, not a solid cap.
idx=np.arange(0,len(xyz),4);xyz=xyz[idx].copy()
t=np.linspace(0,1,64)[None,:]
mask=np.clip((xyz[:,:,2]-1.77)/.13,0,1)
xyz[:,:,2]-=.028*mask*np.sin(np.pi*t)
xyz[:,:,1]-=.010*mask*np.sin(np.pi*t)
phase=rng.uniform(0,6.28,(len(xyz),1))
xyz[:,:,0]+=.0012*np.sin(t*22+phase)*np.sin(np.pi*t)
xyz[:,:,1]+=.0008*np.sin(t*19+phase)*np.sin(np.pi*t)
new=bpy.data.hair_curves.new('Secondary comb layers');new.add_curves([64]*len(xyz));new.attributes['position'].data.foreach_set('vector',xyz.ravel())
rad=(rng.uniform(.000020,.000028,(len(xyz),1))*(1-.95*t)**.7).astype(np.float32);new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel());new.materials.append(cu.materials[0]);hair.data=new

with bpy.data.libraries.load(str(ROOT/'Exports/atelier05/Ember_Regent.blend'),link=False) as (src,dst):
    dst.objects=['Native medium auburn strand groom']
under=dst.objects[0];bpy.data.collections['05_Hair'].objects.link(under);under.name='Continuous scalp coverage groom'
old=under.data;positions=np.empty(len(old.points)*3,dtype=np.float32);old.attributes['position'].data.foreach_get('vector',positions);positions=positions.reshape(-1,56,3)
positions=positions[::2].copy();t=np.linspace(0,1,56)[None,:]
# Break equal-length back ends and flatten the former straight nape curtain.
phase=rng.uniform(0,6.28,(len(positions),1));free=np.clip((t-.5)/.5,0,1)
positions[:,:,0]+=.004*np.sin(t*10+phase)*free
positions[:,:,2]+=.013*free*np.sin(phase)
back=positions[:,:,1]>.00;positions[:,:,2]+=back*.035*free
new=bpy.data.hair_curves.new('Continuous scalp rooted fine fibers');new.add_curves([56]*len(positions));new.attributes['position'].data.foreach_set('vector',positions.ravel())
rad=(rng.uniform(.000024,.000035,(len(positions),1))*(1-.96*t)**.7).astype(np.float32);new.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad.ravel());new.materials.append(hair.data.materials[0]);under.data=new

# A physical fiber shader and neutral rim prevent the broad pink coating of the
# previous lighting study. High sample tests remain necessary for fine strands.
mat=hair.data.materials[0]
for n in mat.node_tree.nodes:
    if n.type=='VALTORGB':n.color_ramp.elements[0].color=(.004,.0006,.0008,1);n.color_ramp.elements[1].color=(.025,.003,.004,1)
    if n.type=='BSDF_HAIR_PRINCIPLED':n.inputs['Roughness'].default_value=.43;n.inputs['Radial Roughness'].default_value=.60

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
usage=json.loads((ROOT/'Exports/atelier06/asset_usage.json').read_text(encoding='utf-8'))
usage.update({'source':'atelier06','version':VERSION,'groom':'continuous rooted undergroom plus sparse individually directed surface fibers; earlier crown void repaired','status':'candidate; requires actual render inspection'})
(OUT/'asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
print('GROOM_REFINED',flush=True)
