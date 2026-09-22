"""Fetch two licensed CC0 PBR material sets from Poly Haven's public API."""
import json,hashlib,requests
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets'/'Materials';OUT.mkdir(parents=True,exist_ok=True)
records=[]
for name in ['cobblestone_floor_01','brown_planks_03']:
    response=requests.get('https://api.polyhaven.com/files/'+name,timeout=30);response.raise_for_status();files=response.json()
    for role,key,fmt in [('color','Diffuse','jpg'),('normal','nor_dx','png'),('roughness','Rough','jpg')]:
        source=files[key]['1k'][fmt]
        dest=OUT/(name+'_'+role+'.'+fmt)
        if not dest.exists() or hashlib.md5(dest.read_bytes()).hexdigest()!=source['md5']:
            response=requests.get(source['url'],timeout=90);response.raise_for_status();data=response.content
            if hashlib.md5(data).hexdigest()!=source['md5']:raise RuntimeError('Checksum mismatch: '+name+' '+role)
            dest.write_bytes(data)
        records.append({'asset':name,'role':role,'file':dest.name,'url':source['url'],
                        'license':'CC0-1.0','sourcePage':'https://polyhaven.com/a/'+name,
                        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
(OUT/'material_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('STARBAY_CC0_MATERIALS_READY',len(records))
