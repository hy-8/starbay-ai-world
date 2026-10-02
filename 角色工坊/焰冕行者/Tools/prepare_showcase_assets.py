"""Extract a reviewed CC0 subset, with checksums and source provenance."""
import zipfile,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'Source/Downloads/makehuman_system_assets_cc0.zip'
dest=ROOT/'Source/ShowcaseCC0';dest.mkdir(exist_ok=True)
prefixes=['skins/young_caucasian_male/','skins/young_caucasian_male2/','skins/young_asian_male/','eyes/','hair/','eyebrows/','clothes/male_elegantsuit01/']+[f'clothes/male_casualsuit{i:02d}/' for i in range(1,7)]
entries=[]
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        if info.is_dir() or not any(info.filename.startswith(p) for p in prefixes):continue
        target=(dest/info.filename).resolve()
        if not target.is_relative_to(dest.resolve()):raise RuntimeError('Invalid archive path')
        data=z.read(info);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=data:raise RuntimeError('Existing local edits protected')
        target.write_bytes(data)
        entries.append({'file':str(target.relative_to(ROOT)).replace('\\','/'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'source':'https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip','license':'CC0; official pack asset table','license_evidence':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','author':'MakeHuman system assets; individual metadata retained','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':entries,'usage':'Texture and tailoring studies; use in final candidate must be separately recorded'}
(ROOT/'Source/showcase_cc0_sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('EXTRACTED',len(entries),'files')
