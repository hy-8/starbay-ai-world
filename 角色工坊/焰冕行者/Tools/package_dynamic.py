"""Package the verified dynamic candidate with explicit input lists and hashes."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,argparse
C=Path(__file__).resolve().parents[1];R=C.parents[1];U=R/'星湾UE5'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def archive(path,entries):
    if path.exists():raise FileExistsError(path)
    records=[]
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p,name in sorted(entries,key=lambda x:x[1]):
            assert p.is_file(),p
            z.write(p,name);records.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
        z.writestr('file_manifest.json',json.dumps(records,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    return {'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'files':len(records),'zip_crc':'passed'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='v0.4.0');parser.add_argument('--build-directory');args=parser.parse_args()
    release=Path(args.build_directory) if args.build_directory else R/'星湾发布'/('Ember-'+args.version);out=release/'Archives';out.mkdir(exist_ok=True)
    report=json.loads((U/'Validation/ember_delivery.json').read_text(encoding='utf-8'))
    assert report['input_checks']['status']=='passed'
    assert report['windows']['launched'] and report['windows']['map_loaded']
    dependencies=json.loads((U/'Saved/ember_release_dependencies.json').read_text(encoding='utf-8'))
    assert not dependencies['missing_hard_dependencies'] and not dependencies['rejected_dependencies']
    win=[]
    for p in (release/'Windows').rglob('*'):
        if p.is_file() and p.suffix.lower() not in ['.pdb','.debug','.log'] and not {'Saved','Intermediate'}.intersection(p.relative_to(release).parts):win.append((p,str(p.relative_to(release))))
    for p in release.glob('*.cmd'):win.append((p,p.name))
    win.append((U/'Design/焰冕行者_动态试玩.md','试玩说明.md'))
    win.append((U/'Validation/ember_delivery.json','verification.json'))
    win.append((U/'THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md'))
    sources={U/f for f in dependencies['files']}
    for p in U.glob('Config/*.ini'):
        assert 'SecurityToken=' not in p.read_text(encoding='utf-8-sig'), 'Do not ship generated token'
        sources.add(p)
    sources.update([U/'StarbayUE5.uproject',U/'README.md',U/'THIRD_PARTY_NOTICES.md'])
    # Only committed/reviewed tools and documentation are included, never diagnostics.
    tracked=subprocess.check_output(['D:/Git/cmd/git.exe','-C',str(R),'ls-files','-z'],encoding='utf-8').split('\0')
    for f in tracked:
        p=R/f
        if f and (f.startswith('星湾UE5/Tools/') or f.startswith('星湾UE5/Design/') or f.startswith('星湾UE5/Validation/') or f.startswith('角色工坊/焰冕行者/Tools/')):sources.add(p)
    for sub in ['rig04','motion05']:
        sources.update(p for p in (C/'Exports'/sub).iterdir() if p.suffix in ['.blend','.fbx','.json'])
    sources.add(C/'Exports/v14/Ember_Regent.blend')
    for pattern in ['*.md','*.ps1','Materials/*.png','Materials/*.json','Source/*.obj','Source/*.target','Source/*.mhw','Source/*.mhskel','Source/*sources.json','Source/UE_Reference/*.fbx','Source/UE_Reference/sources.json','Source/UE_Reference/*.md','Source/targets/*.target','Renders/motion05/*.png']:
        sources.update(C.glob(pattern))
    # Morph paths are recorded in the source manifest rather than guessed.
    for record in json.loads((C/'Source/couture_sources.json').read_text(encoding='utf-8')):sources.add(C/'Source'/record['file'])
    sources.add(U/'Preview/UE5_Ember_NativeCast.png');sources.add(U/'Preview/UE5_Ember_Windows.png')
    results=[archive(out/('Starbay-Ember-Windows-'+args.version+'.zip'),win),archive(out/('Starbay-Ember-Editable-'+args.version+'.zip'),[(p,str(p.relative_to(R))) for p in sources])]
    (out/'SHA256SUMS.txt').write_text(''.join(x['sha256']+'  '+x['name']+'\n' for x in results),encoding='utf-8')
    (out/'release_manifest.json').write_text(json.dumps({'version':args.version,'assets':results},indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)
if __name__=='__main__':main()
