"""Package one verified character candidate; preserve all previous releases.

Run with normal Python: package_character.py VERSION OUTPUT.zip
Reference pictures, old candidates, logs and Blender backup files are excluded.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
version, destination = sys.argv[1:]
if not re.fullmatch(r'[A-Za-z0-9_-]+', version):
    raise ValueError('Invalid version directory')
output = Path(destination).resolve()
if output.exists():
    raise FileExistsError('Previous package is protected: ' + str(output))
export = root / 'Exports' / version
manifest = json.loads((export / 'manifest.json').read_text(encoding='utf-8'))
verification = json.loads((export / 'verification.json').read_text(encoding='utf-8'))
assert manifest['version'] == verification['version'] == version
assert len(verification['checks']) == 2
for name, info in manifest['files'].items():
    assert hashlib.sha256((export / name).read_bytes()).hexdigest() == info['sha256'], name
paths = [root / 'README.md', root / 'THIRD_PARTY_NOTICES.md', root / 'Open-Character.ps1']
paths += sorted((root / 'Tools').glob('*.py'))
paths += sorted(p for p in (root / 'Source').rglob('*') if p.suffix in {'.obj', '.target', '.json'})
paths += sorted(p for p in (root / 'Materials').iterdir() if p.suffix in {'.png', '.json'})
paths += sorted(p for p in export.iterdir() if p.suffix in {'.blend', '.fbx', '.glb', '.json'})
views = sorted((root / 'Renders' / version).glob('*.png'))
assert len(views) >= 6
paths += views
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in paths:
        archive.write(path, path.relative_to(root).as_posix())
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(paths)
report = {'version': version, 'file': output.name, 'files': len(paths),
          'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
          'checks': 'Manifest hashes match; all ZIP entries pass CRC; six actual render views included.'}
output.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
