"""Local Hunyuan3D shape-only experiment. Does not claim finished hair.

Run with the isolated Hunyuan runtime; large dependencies stay outside repo.
Every seed/version writes a new raw reconstruction directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('version')
parser.add_argument('--seed', type=int, default=10203)
parser.add_argument('--steps', type=int, default=40)
parser.add_argument('--resolution', type=int, default=384)
args = parser.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+', args.version):
    raise ValueError('Invalid version')
out = ROOT / 'Source/HairReconstruction' / args.version
out.mkdir(exist_ok=False)
os.environ['HF_HOME'] = 'D:/models/HF-hair-cache'
os.environ['HY3DGEN_MODELS'] = 'D:/models/HY3D-hair-cache'
os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, 'D:/tools/Hunyuan3D-2-hair')
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.shapegen.pipelines import instantiate_from_config
from accelerate import init_empty_weights
from safetensors import safe_open
import yaml

torch.set_num_threads(6)
model = Path('D:/models/Hunyuan3D-2mini-hair')
image = ROOT / 'Source/HairReconstruction/hair_input01.png'
start = time.time()
print('LOADING_SHAPE_ONLY', flush=True)
config = yaml.safe_load((model / 'hunyuan3d-dit-v2-mini/config.yaml').read_text())
weights = model / 'hunyuan3d-dit-v2-mini/model.fp16.safetensors'
components = {}
# Meta parameters + mmap assignment avoid allocating the original fp32
# network and an extra copy of every weight on this 16 GB host.
with safe_open(weights, framework='pt', device='cpu') as checkpoint:
    keys = list(checkpoint.keys())
    for name in ['model', 'vae', 'conditioner']:
        print('MMAP_COMPONENT', name, flush=True)
        with init_empty_weights(include_buffers=False):
            module = instantiate_from_config(config[name])
        if name == 'vae':
            # Shape generation only decodes latents. The released inference
            # checkpoint intentionally omits the unused surface encoder.
            module.encoder = None
            module.pre_kl = None
        prefix = name + '.'
        state = {k[len(prefix):]: checkpoint.get_tensor(k) for k in keys if k.startswith(prefix)}
        result = module.load_state_dict(state, strict=(name != 'vae'), assign=True)
        if result.missing_keys:
            raise RuntimeError(f'Uninitialized parameters: {name}: {result.missing_keys}')
        if any(p.is_meta for p in module.parameters()):
            raise RuntimeError('Remaining meta parameters')
        components[name] = module
        del state
pipeline = Hunyuan3DDiTFlowMatchingPipeline(
    **components,
    scheduler=instantiate_from_config(config['scheduler']),
    image_processor=instantiate_from_config(config['image_processor']),
    device='cpu', dtype=torch.float16)
# This upstream class exposes the offload method but does not initialize the
# Diffusers-style components property referenced by it. Supply actual modules.
pipeline.components = components
pipeline._exclude_from_cpu_offload = []
pipeline.enable_model_cpu_offload(device='cuda')
# This upstream pipeline reads self.device in sampling, rather than
# _execution_device. Accelerate hooks move modules, not this metadata.
pipeline.device = torch.device('cuda:0')
print('RECONSTRUCTING', args.seed, args.steps, args.resolution, flush=True)
mesh = pipeline(
    image=Image.open(image), num_inference_steps=args.steps,
    guidance_scale=5.0,
    generator=torch.Generator(device='cuda').manual_seed(args.seed),
    octree_resolution=args.resolution, num_chunks=4000,
    mc_algo='mc', output_type='trimesh')[0]
if mesh is None:
    raise RuntimeError('No mesh returned')
mesh.export(out / 'raw_hair.glb')
mesh.export(out / 'raw_hair.obj')
parts = mesh.split(only_watertight=False)
connected = max(parts, key=lambda m: len(m.vertices))
np.savez_compressed(out / 'connected_hair.npz',
                    vertices=connected.vertices.astype(np.float32),
                    faces=connected.faces.astype(np.int32))
(out / 'cleanup.json').write_text(json.dumps({
    'source': 'raw_hair.glb', 'components': len(parts),
    'retained_vertices': len(connected.vertices), 'retained_faces': len(connected.faces),
    'method': 'retained largest connected wig; discarded detached fragments'
}, indent=2), encoding='utf-8')

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

report = {
    'version': args.version, 'status': 'raw shape; requires fitting and visual review',
    'input': str(image.relative_to(ROOT)), 'input_sha256': sha256(image),
    'input_kind': 'generated transparent wig reference, not a render of the character',
    'model': 'tencent/Hunyuan3D-2mini', 'subfolder': 'hunyuan3d-dit-v2-mini',
    'weights_sha256': sha256(model / 'hunyuan3d-dit-v2-mini/model.fp16.safetensors'),
    'source_repo': 'https://github.com/Tencent/Hunyuan3D-2',
    'source_commit': 'f8db63096c8282cb27354314d896feba5ba6ff8a',
    'license': 'TENCENT HUNYUAN 3D 2.0 COMMUNITY LICENSE AGREEMENT; see model LICENSE',
    'seed': args.seed, 'steps': args.steps, 'guidance_scale': 5.0,
    'octree_resolution': args.resolution, 'num_chunks': 4000,
    'precision': 'fp16', 'memory_mode': 'mmap/meta parameter assignment + component CPU offload',
    'texture_pipeline': False, 'vertices': len(mesh.vertices), 'faces': len(mesh.faces),
    'bounds': mesh.bounds.tolist(), 'elapsed_seconds': round(time.time() - start, 2),
    'mesh_sha256': sha256(out / 'raw_hair.glb'),
}
(out / 'reconstruction.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print('RAW_SHAPE_SAVED', report, flush=True)
