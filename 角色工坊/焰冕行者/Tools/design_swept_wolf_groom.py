"""Art-directed scalp-grown medium red hair, replacing surface-traced ribbons.

Angles and free ends are independent by zone. Retain the trimmed short
undercoat from hairrecongroom05, replace its visible reconstructed outer groom.
Blender -- new-version [--detail]. No image planes or visible solid wig.
"""
import bpy,sys,json,re,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:];version=args[0]
if not re.fullmatch(r'[A-Za-z0-9_-]+',version):raise ValueError(version)
out=ROOT/'Exports'/version;render=ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh version required')
out.mkdir(parents=True);render.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Exports/hairrecongroom05/Ember_Regent.blend'))
col=bpy.data.collections['05_Hair'];mat=bpy.data.objects['Cherry asymmetric surface groom'].data.materials[0]
for ob in list(col.objects):
    if ob.type=='CURVES' and ob.name!='Scalp rooted coverage beneath sculpted locks':bpy.data.objects.remove(ob,do_unlink=True)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());C=Vector((0,-.044,1.771))
rng=np.random.default_rng(10603);N=96;t=np.linspace(0,1,N)
LAYERED='--layered' in args

def scalp(theta,az):
    direction=Vector((math.sin(theta)*math.sin(az),-math.sin(theta)*math.cos(az),math.cos(theta)))
    p,n,_,_=bv.ray_cast(C,direction,.35)
    if p is None:raise RuntimeError('Scalp ray missed')
    return np.asarray(p,dtype=float),np.asarray(n,dtype=float)

design=[]
# Independent diagonal front layers from a real off-center part. The opposite
# side remains lighter and clears the ear. Lengths stop outside eye centers.
for side,num in ([(-1,26),(1,18)] if LAYERED else [(-1,46),(1,29)]):
    for k in range(num):
        f=(k+.5)/num;ry=-.134+f*.153;rx=.028+rng.normal(0,.004)
        p,n,_,_=bv.ray_cast(Vector((rx,ry,2.05)),Vector((0,0,-1)),.40)
        if p is None:continue
        delta=p-C;theta=math.acos(np.clip(delta.z/delta.length,-1,1));az=math.atan2(delta.x,-delta.y)
        if side<0:
            endaz=-.47-1.25*f+rng.normal(0,.045)
            endtheta=1.51+.36*f+rng.normal(0,.07)
            lift=rng.uniform(.010,.023)
        else:
            endaz=.77+1.12*f+rng.normal(0,.045)
            endtheta=1.39+.45*f+rng.normal(0,.07)
            lift=rng.uniform(.006,.016)
        if LAYERED:
            if k%3==0:endtheta-=.19
            lift*=rng.uniform(1.0,1.7)
        design.append(dict(zone='swept_front',root_theta=theta,root_az=az,end_theta=endtheta,end_az=endaz,lift=lift,phase=rng.uniform(0,6.28),width=rng.uniform(.0023,.0041),count=510 if side<0 else 390,free=rng.uniform(.004,.018)))
# Layered sides grow from varied patches, and curve backward around ears.
for side in [-1,1]:
    for k in range(31):
        f=(k+.5)/31;az=side*(.70+1.57*f);theta=rng.uniform(.68,1.26)
        design.append(dict(zone='temple',root_theta=theta,root_az=az,end_theta=rng.uniform(1.80,2.03),end_az=az+side*.12,lift=rng.uniform(.005,.014),phase=rng.uniform(0,6.28),width=rng.uniform(.0023,.0038),count=340,free=rng.uniform(.014,.037)))
# Asymmetrical back and nape lengths, with free S-shaped tips instead of a row
# of repeated curled loops or a straight curtain at the coat collar.
for k in range(76):
    f=(k+.5)/76;az=math.pi*.64+math.pi*.72*f;theta=rng.uniform(.24,1.48)
    design.append(dict(zone='nape',root_theta=theta,root_az=az,end_theta=rng.uniform(1.97,2.16),end_az=az+rng.normal(0,.13),lift=rng.uniform(.007,.018),phase=rng.uniform(0,6.28),width=rng.uniform(.0022,.0040),count=430,free=rng.uniform(.015,.052)))

paths=[];radii=[];guides=[]
for i,d in enumerate(design):
    g=[];normals=[];side=1 if math.sin(d['end_az'])>0 else -1
    for u in t:
        easing=u*.78+.22*u*u
        theta=d['root_theta']+(d['end_theta']-d['root_theta'])*easing
        az=d['root_az']+(d['end_az']-d['root_az'])*(u*.65+.35*u*u)
        az+=.095*math.sin(u*8.5+d['phase'])*math.sin(math.pi*u)**2
        p,n=scalp(theta,az)
        height=.0006+d['lift']*math.sin(math.pi*u)**.85
        height+=.003*math.sin(u*7+d['phase'])*math.sin(math.pi*u)**2
        p+=n*height
        free=max(0,(u-.67)/.33)**1.55
        p[2]-=free*d['free']
        p[0]+=side*free*.007*math.sin(u*6+d['phase'])
        if d['zone']=='nape':p[1]+=free*.010
        elif d['zone']=='temple':p[1]+=free*.005
        g.append(p);normals.append(n)
    g=np.asarray(g);normal=np.asarray(normals)
    if LAYERED:
        wave=np.sin(math.pi*t)**1.2
        g[:,0]+=.005*np.sin(t*8+d['phase'])*wave
        g[:,1]+=.004*np.sin(t*7+d['phase']*.9)*wave
        g[:,2]+=.0025*np.sin(t*11+d['phase'])*wave
        if d['zone'] in ['nape','temple']:
            finish=rng.uniform(1.630,1.700) if d['zone']=='nape' else rng.uniform(1.680,1.742)
            free=np.maximum(0,(t-.60)/.40)**1.45
            g[:,2]+=(finish-g[-1,2])*free
            if d['zone']=='nape':g[:,1]+=.020*free
    tangent=np.gradient(g,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-9)
    lateral=np.cross(tangent,normal);lateral/=np.maximum(np.linalg.norm(lateral,axis=1,keepdims=True),1e-9);normal=np.cross(lateral,tangent)
    count=d['count'];phase=rng.uniform(0,6.28,(count,1));width=d['width'];shape=(.78+.22*np.sin(math.pi*t))*(1-.79*t**4)
    across=rng.normal(0,width,(count,1))*shape+.00085*np.sin(t*18+phase)*np.sin(math.pi*t)
    depth=rng.normal(0,width*.65,(count,1))*shape+.00070*np.sin(t*13+phase)*np.sin(math.pi*t)
    # Each fiber receives a different low-frequency bend, so neighboring hairs
    # do not share the exact specular response of an undivided ribbon.
    across+=rng.normal(0,.0010,(count,1))*np.sin(t*6+phase)*np.sin(math.pi*t)
    xyz=g[None,:,:]+lateral[None,:,:]*across[:,:,None]+normal[None,:,:]*depth[:,:,None]
    for j in range(count):
        p,n,_,_=bv.find_nearest(Vector(xyz[j,0]))
        if p is not None:
            delta=np.asarray(p+n*.0004)-xyz[j,0];xyz[j]+=delta[None,:]*(1-t[:,None])**3
    ends=rng.uniform(.86,1,(count,1));q=t*ends*(N-1);lo=np.floor(q).astype(int);hi=np.minimum(N-1,lo+1);blend=(q-lo)[:,:,None]
    xyz=xyz[np.arange(count)[:,None],lo]*(1-blend)+xyz[np.arange(count)[:,None],hi]*blend
    paths.append(xyz.astype(np.float32));radii.append((rng.uniform(.000026,.000042,(count,1))*(1-.975*t)**.65).astype(np.float32));guides.append(g)
xyz=np.concatenate(paths);radius=np.concatenate(radii)
cu=bpy.data.hair_curves.new('Scalp-grown independent swept wolf layers');cu.add_curves([N]*len(xyz));cu.attributes['position'].data.foreach_set('vector',xyz.ravel());cu.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius.ravel());cu.materials.append(mat)
hair=bpy.data.objects.new('Art-directed swept cherry layers',cu);col.objects.link(hair)
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';detail='--detail' in args;scene.cycles.use_denoising=False
scene.render.resolution_x=1800 if detail else 1200;scene.render.resolution_y=2100 if detail else 1400;scene.render.resolution_percentage=100 if detail else 80;scene.cycles.samples=256 if detail else 96
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'version':version,'source':'hairrecongroom05','method':'actual scalp-grown independent three-dimensional front/temple/nape guide families','visible_reconstructed_outer_groom':False,'guides':len(guides),'strands':len(xyz),'undercoat_strands':50460,'seed':10603,'samples':scene.cycles.samples,'status':'candidate requiring artistic review'}
(out/'groom_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');(out/'guide_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8');np.savez_compressed(out/'groom_guides.npz',guides=np.asarray(guides))
print('SWEPT_GROOM_SAVED',report,flush=True)
