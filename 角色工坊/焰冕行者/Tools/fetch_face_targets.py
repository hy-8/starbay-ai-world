"""Fetch selected explicitly CC0 MakeHuman morphs; never downloads commercial assets."""
from pathlib import Path
import requests, hashlib, json
root=Path(__file__).resolve().parents[1]/'Source'
chosen={
    'head/head-oval.target':.12,
    'head/head-fat-decr.target':.18,
    'nose/nose-greek-incr.target':.25,
    'nose/nose-scale-horiz-decr.target':.24,
    'mouth/mouth-cupidsbow-incr.target':.20,
    'mouth/mouth-upperlip-volume-incr.target':.18,
    'mouth/mouth-lowerlip-middle-up.target':.18,
    'mouth/mouth-scale-vert-decr.target':.18,
    'mouth/mouth-angles-up.target':.07,
    'eyes/l-eye-height1-incr.target':.24,
    'eyes/r-eye-height1-incr.target':.24,
    'eyes/l-eye-height2-incr.target':.30,
    'eyes/r-eye-height2-incr.target':.30,
    'eyes/l-eye-corner1-up.target':.12,
    'eyes/r-eye-corner1-up.target':.12,
}
records=[]
for rel,weight in chosen.items():
    url='https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/targets/'+rel
    data=requests.get(url,timeout=35).content
    if b'explicitly released as CC0' not in data[:2000]:raise RuntimeError('Missing explicit CC0 notice: '+rel)
    file=root/'Morphs'/rel;file.parent.mkdir(exist_ok=True,parents=True)
    if file.exists() and file.read_bytes()!=data:raise RuntimeError('Preserve existing source: '+str(file))
    file.write_bytes(data)
    records.append({'file':'Morphs/'+rel,'url':url,'weight':weight,'license':'CC0; explicit file header','sha256':hashlib.sha256(data).hexdigest()})
(root/'couture_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified explicitly CC0 morph sources:',len(records))
