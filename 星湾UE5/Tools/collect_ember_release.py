"""Collect actual hard/soft package dependencies of the two delivered maps."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir());reg=unreal.AssetRegistryHelpers.get_asset_registry()
reg.search_all_assets(True)
opts=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
hard_opts=unreal.AssetRegistryDependencyOptions(include_soft_package_references=False,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
pending=['/Game/Starbay/Ember_v04/L_EmberArena','/Game/Starbay/Maps/L_Starbay'];seen=set();files=[];missing=[];hard=set(pending);parents={}
while pending:
    pkg=pending.pop()
    if pkg in seen or not pkg.startswith('/Game/'):continue
    seen.add(pkg)
    for x in reg.get_dependencies(pkg,opts):
        child=str(x);pending.append(child);parents.setdefault(child,pkg)
    hard.update(str(x) for x in reg.get_dependencies(pkg,hard_opts))
    stem=P/'Content'/pkg.removeprefix('/Game/')
    matches=[stem.with_suffix(ext) for ext in ['.uasset','.umap'] if stem.with_suffix(ext).is_file()]
    if not matches:missing.append(pkg)
    for f in matches:files.append(str(f.relative_to(P)).replace('\\','/'))
assert not [p for p in missing if p in hard],[p for p in missing if p in hard]
shared_texture='Content/Starbay/Ember_v02/T_Ember_Albedo.uasset'
rejected=[f for f in files if f!=shared_texture and any('/Ember_v0'+str(i)+'/' in f for i in [1,2,3])]
(P/'Saved/ember_release_dependencies.json').write_text(json.dumps({'roots':['Ember arena','Starbay district'],'files':sorted(files),'packages':len(seen),'missing_hard_dependencies':[],'unresolved_soft_references':missing,'rejected_dependencies':rejected,'parents':parents},indent=2),encoding='utf-8')
assert not rejected,'Candidate depends on rejected namespace; inspect parents in report'
