"""Check saved native hair against the geometry Blender evaluates after reopening."""
import bpy,sys,json,re,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];output,base=a[:2]
assert all(re.fullmatch('[A-Za-z0-9_.-]+',x) for x in a[:2])
out=ROOT/'Exports'/output;assert not out.exists()
path=ROOT/'Exports'/base/'Ember_Regent.blend';digest=hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();rows=[]
def points(cu):
 p=np.empty((len(cu.points),3),np.float32);cu.attributes['position'].data.foreach_get('vector',p.ravel());return p
for ob in sorted(bpy.data.objects,key=lambda o:o.name):
 if ob.type!='CURVES' or ob.hide_render:continue
 raw=points(ob.data);ev=ob.evaluated_get(deps);actual=points(ev.data)
 same=raw.shape==actual.shape and np.array_equal(raw,actual)
 rows.append(dict(object=ob.name,modifiers=[dict(name=m.name,type=m.type,show_render=m.show_render,show_viewport=m.show_viewport) for m in ob.modifiers],saved_points=len(raw),evaluated_points=len(actual),saved_position_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),evaluated_position_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),positions_exact=bool(same)))
assert len(rows)==4 and all(r['positions_exact'] for r in rows),rows
assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
out.write_text(json.dumps(dict(source=base,source_sha256=digest,source_unchanged=True,frame=1,all_four_saved_evaluated_positions_exact=True,components=rows,scope='Saved frame1 evaluated position comparison; not proof of every shader/render backend, animation or artistic acceptance'),indent=2),encoding='utf-8')
print('SAVED_NATIVE_EVALUATION_PASS',base,flush=True)
