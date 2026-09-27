"""Import licensed local Epic combat template sources without overwriting edits."""
from pathlib import Path
import argparse,hashlib,shutil,json
P=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--engine-root',default='D:/Program Files/Epic Games/UE_5.6');a=ap.parse_args()
    source=Path(a.engine_root)/'Templates/TemplateResources/Standard/Variant_Combat/Content'
    target=P/'Content/Variant_Combat';plan=[]
    for part in ['Anims','Blueprints','Input','Materials','UI','VFX']:
        assert (source/part).is_dir(),source/part
        for p in (source/part).rglob('*.uasset'):
            dest=target/p.relative_to(source)
            if dest.exists() and digest(dest)!=digest(p):raise RuntimeError('Preserve modified template asset: '+str(dest))
            plan.append((p,dest))
    for p,dest in plan:
        if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    (P/'Saved').mkdir(exist_ok=True)
    (P/'Saved/combat_template_import.json').write_text(json.dumps({'source':str(source),'files':[{'path':str(d.relative_to(P)),'sha256':digest(d)} for _,d in plan]},indent=2),encoding='utf-8')
    print('Verified local Epic combat assets:',len(plan))
if __name__=='__main__':main()
