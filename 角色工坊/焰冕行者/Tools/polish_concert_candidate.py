"""Fit groom silhouette, standing collar and hardware on a fresh candidate."""
import bpy,sys,json,re,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[sys.argv.index('--')+1]
if not re.fullmatch('[A-Za-z0-9_-]+',VERSION):raise ValueError(VERSION)
OUT=ROOT/'Exports'/VERSION
if OUT.exists():raise RuntimeError('Fresh output required')
OUT.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/atelier07/Ember_Regent.blend'))
col=bpy.data.collections
# Clamp only excess crown volume against an anatomical envelope. The previous
# guide layer's arches were visibly too high; native undergroom roots stay put.
o=bpy.data.objects['Layered auburn guide groom'];cu=o.data
xyz=np.empty(len(cu.points)*3,dtype=np.float32);cu.attributes['position'].data.foreach_get('vector',xyz);xyz=xyz.reshape(-1,64,3)
cx=xyz[:,:,0];cy=xyz[:,:,1]+.031
roof=1.774+.116*np.sqrt(np.maximum(.015,1-(cx/.122)**2-(cy/.159)**2))
xyz[:,:,2]=np.minimum(xyz[:,:,2],roof)
cu.attributes['position'].data.foreach_set('vector',xyz.ravel())

# Additional fringe is combed diagonally over the hairline, avoiding the former
# broad bare forehead. Each guide ends at a distinct height outside the iris.
body=max((o for o in col['01_Body'].objects if o.type=='MESH' and not o.hide_render and 'high-poly' not in o.name),key=lambda o:len(o.data.vertices))
bpy.context.view_layer.update();bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
rng=np.random.default_rng(809);points=[];radii=[];N=64;t=np.linspace(0,1,N)[None,:,None]
for side in [-1,1]:
    for k in range(16):
        f=k/15;x=(-.019 if side==1 else -.010)+rng.uniform(-.006,.006);y=-.080+f*.074
        h,n,_,_=bv.ray_cast(Vector((x,y,2.1)),Vector((0,0,-1)),.5)
        if h is None:continue
        p=np.array([h+n*.0004,(side*.058,-.143+.04*f,1.876-.015*f),(side*.083,-.166+.025*f,1.798),(side*(.035+.042*f),-.151+.012*f,1.733+f*.012)],dtype=np.float32)
        num=200;tt=t*rng.uniform(.87,1,(num,1,1))
        centers=p[0]*(1-tt)**3+3*p[1]*(1-tt)**2*tt+3*p[2]*(1-tt)*tt**2+p[3]*tt**3
        phase=rng.uniform(0,6.28,(num,1));spread=np.sin(np.pi*tt[:,:,0])**.6
        centers[:,:,0]+=(rng.normal(0,.003,(num,1))+.0008*np.sin(tt[:,:,0]*15+phase))*spread
        centers[:,:,1]+=rng.normal(0,.0015,(num,1))*spread
        points.append(centers.astype(np.float32));radii.append((rng.uniform(.000022,.000033,(num,1))*(1-.96*tt[:,:,0])**.7).astype(np.float32))
points=np.concatenate(points);radii=np.concatenate(radii)
fr=bpy.data.hair_curves.new('Diagonal fringe fine fibers');fr.add_curves([N]*len(points));fr.attributes['position'].data.foreach_set('vector',points.ravel());fr.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel());fr.materials.append(cu.materials[0]);fo=bpy.data.objects.new('Fitted diagonal face framing fringe',fr);col['05_Hair'].objects.link(fo)

def mesh(name,verts,faces,mat,collection):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);col[collection].objects.link(ob);me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    md=ob.modifiers.new('Subdivided garment','SUBSURF');md.levels=2;md.render_levels=2
    md=ob.modifiers.new('Sewn thickness','SOLIDIFY');md.thickness=.002
    return ob
leather=bpy.data.materials['Atelier oxblood matte leather'];metal=bpy.data.materials['Atelier smoked silver']
# Slim standing collar at the back/side of the neck changes the business-jacket
# silhouette into a stage frock coat. It is open at the throat.
verts=[];faces=[];nu=9;nv=85
for i in range(nu):
    u=i/(nu-1)
    for j in range(nv):
        a=.90+(2*math.pi-1.8)*j/(nv-1)
        verts.append(((.088+.007*u)*math.sin(a),-.018-(.083+.008*u)*math.cos(a),1.522+.072*u-.008*math.cos(a)))
for i in range(nu-1):
    for j in range(nv-1):faces.append((i*nv+j,(i+1)*nv+j,(i+1)*nv+j+1,i*nv+j+1))
mesh('Tailored standing rear collar',verts,faces,leather,'03_OuterRobe')

# Belt formerly floated beyond the narrowed frock waist. Constrain each point
# to the actual jacket surface along its local horizontal normal.
suit=bpy.data.objects['Fitted CC0 male_elegantsuit01'];bpy.context.view_layer.update();sbv=BVHTree.FromObject(suit,bpy.context.evaluated_depsgraph_get())
for ob in col['06_Regalia'].objects:
    if ob.name.startswith('Atelier fitted waist belt'):
        for v in ob.data.vertices:
            p,n,_,_=sbv.find_nearest(v.co)
            if p is not None:v.co=p+n*.004

# Skin microstructure: physically small bump from object-space cellular pores,
# preserving the photographed color texture and the original UV layout.
skin=bpy.data.materials['Porcelain warm skin'];nt=skin.node_tree;p=nt.nodes.get('Principled BSDF')
tc=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2100;noise.inputs['Detail'].default_value=2
nt.links.new(tc.outputs['Object'],noise.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.000055
nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal']);p.inputs['Subsurface Weight'].default_value=.055
p.inputs['Roughness'].default_value=.48

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ember_Regent.blend'))
usage=json.loads((ROOT/'Exports/atelier07/asset_usage.json').read_text(encoding='utf-8'));usage.update({'source':'atelier07','version':VERSION,'refinement':'scalp envelope fitting, separate diagonal fringe, standing collar, belt surface fit, small skin micro-bump','status':'unapproved real 3D study'})
(OUT/'asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf-8')
print('POLISH_SAVED',str(OUT),flush=True)
