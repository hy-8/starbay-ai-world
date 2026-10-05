"""Explicit art-directed posterior lock skeleton, no root-index/random guides.

Author a small set of full spatial paths first, then cover existing follicles
with their local flow. All pre-existing mesh/UV/shape-key data is retained.
Use a fresh version. Construction controls are editable, but re-baking is
required after editing; no assertion of live grooming or simulation.
"""
import bpy, sys, re, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version,source_version=args[:2]
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:2]):raise ValueError(args)
out,renders=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or renders.exists():raise RuntimeError('Fresh output required')
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.view_layer.update()
bv=BVHTree.FromObject(bpy.data.objects['CC0 male body • retained topology'],bpy.context.evaluated_depsgraph_get())
rear=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Original posterior shag'))
if not np.allclose(np.array(rear.matrix_world),np.eye(4)):raise RuntimeError('Neutral groom required')
N=len(rear.data.curves[0].points)
raw=np.empty(len(rear.data.points)*3,np.float32);rear.data.attributes['position'].data.foreach_get('vector',raw)
raw=raw.reshape(-1,N,3);roots=raw[:,0].astype(float)
t=np.linspace(0,1,N)

# Spatial knots authored for this head. Unequal crown, diagonal occipital
# layers, a light ear-side passage, and separate longer neck layers.
design=[]
def lock(name,points):design.append(dict(name=name,knots_m=points))
lock('crown left deep sweep',[[.018,-.003,1.864],[.016,.025,1.884],[-.012,.045,1.886],[-.052,.060,1.868],[-.080,.065,1.850],[-.101,.074,1.826],[-.093,.087,1.813]])
lock('crown left short loose exit',[[.000,-.004,1.866],[-.014,.019,1.888],[-.043,.026,1.875],[-.080,.049,1.864],[-.101,.067,1.850],[-.106,.080,1.831],[-.122,.084,1.833]])
lock('crown right long sweep',[[.038,.000,1.862],[.053,.019,1.880],[.080,.039,1.872],[.104,.038,1.850],[.116,.041,1.822],[.129,.057,1.802],[.123,.064,1.788]])
lock('crown right rear wave',[[.016,.031,1.862],[.024,.052,1.885],[.052,.071,1.875],[.077,.075,1.850],[.075,.079,1.826],[.096,.087,1.800],[.102,.079,1.787]])
lock('crown left rear counter wave',[[-.028,.027,1.858],[-.038,.035,1.878],[-.055,.065,1.874],[-.077,.081,1.851],[-.065,.087,1.825],[-.078,.088,1.800],[-.096,.082,1.795]])
lock('right rear high overlap',[[.030,.049,1.850],[.041,.064,1.871],[.043,.084,1.857],[.071,.088,1.837],[.055,.090,1.816],[.069,.103,1.790],[.085,.105,1.778]])
lock('left occipital diagonal',[[-.015,.052,1.844],[-.030,.067,1.858],[-.033,.084,1.847],[-.020,.092,1.827],[-.028,.094,1.805],[-.020,.090,1.777],[-.039,.097,1.750],[-.037,.100,1.731]])
lock('right occipital diagonal',[[.017,.061,1.837],[.023,.077,1.851],[.038,.082,1.834],[.025,.089,1.813],[.028,.092,1.781],[.019,.084,1.757],[.028,.091,1.731],[.040,.095,1.720]])
lock('right back lateral short',[[.046,.052,1.841],[.065,.064,1.851],[.077,.081,1.831],[.068,.089,1.811],[.059,.100,1.789],[.080,.100,1.758],[.079,.097,1.747]])
lock('left back lateral short',[[-.053,.049,1.839],[-.074,.061,1.851],[-.086,.074,1.833],[-.079,.089,1.809],[-.098,.084,1.777],[-.091,.090,1.750],[-.108,.085,1.753]])
lock('central back medium interleave',[[.010,.072,1.820],[.000,.084,1.826],[-.009,.090,1.807],[.002,.092,1.783],[-.010,.084,1.754],[-.003,.100,1.727],[-.013,.098,1.699]])
lock('left back medium interleave',[[-.047,.066,1.816],[-.053,.078,1.827],[-.045,.091,1.809],[-.057,.094,1.781],[-.047,.083,1.752],[-.062,.094,1.726],[-.075,.089,1.702]])
lock('right back medium interleave',[[.047,.064,1.819],[.055,.078,1.829],[.050,.092,1.808],[.063,.095,1.778],[.050,.085,1.750],[.061,.091,1.724],[.072,.086,1.709]])
lock('central neck long loose',[[.000,.077,1.798],[.005,.085,1.795],[-.002,.091,1.777],[-.020,.078,1.742],[-.010,.071,1.705],[-.016,.078,1.668],[-.009,.078,1.641],[-.022,.082,1.625]])
lock('left neck long loose',[[-.035,.072,1.790],[-.045,.084,1.780],[-.040,.089,1.762],[-.055,.083,1.727],[-.040,.075,1.700],[-.052,.088,1.664],[-.059,.084,1.646]])
lock('right neck long loose',[[.040,.068,1.792],[.050,.080,1.777],[.038,.090,1.753],[.050,.084,1.722],[.034,.078,1.690],[.047,.087,1.657],[.053,.082,1.644]])
lock('central neck inner long',[[.014,.074,1.768],[.023,.077,1.755],[.012,.082,1.728],[.029,.075,1.700],[.019,.077,1.665],[.032,.083,1.632]])
lock('left lower outside wave',[[-.065,.043,1.780],[-.093,.070,1.785],[-.090,.078,1.752],[-.077,.082,1.714],[-.088,.075,1.680],[-.079,.078,1.657]])
lock('right lower outside wave',[[.068,.045,1.783],[.095,.069,1.783],[.097,.079,1.752],[.081,.083,1.717],[.094,.078,1.683],[.087,.081,1.665]])
lock('left neck fine medium',[[-.018,.075,1.784],[-.030,.089,1.774],[-.023,.089,1.749],[-.035,.084,1.721],[-.031,.093,1.686],[-.041,.089,1.663]])
lock('right neck fine medium',[[.023,.074,1.785],[.016,.089,1.774],[.026,.092,1.748],[.020,.086,1.718],[.030,.096,1.684],[.022,.094,1.660]])

# The right side is deliberately not an exact mirror: one long passage and
# one shorter open ear section have different bends/lengths.
lock('left ear upper passage',[[-.074,-.035,1.823],[-.086,-.024,1.839],[-.106,-.012,1.829],[-.117,.016,1.800],[-.100,.035,1.780],[-.117,.052,1.754]])
lock('right ear upper passage',[[.075,-.032,1.826],[.089,-.020,1.840],[.105,-.004,1.827],[.115,.021,1.803],[.102,.039,1.779],[.112,.054,1.762]])
lock('left temple short backward',[[-.070,-.063,1.820],[-.090,-.068,1.822],[-.103,-.064,1.800],[-.108,-.043,1.781],[-.089,-.024,1.770],[-.105,-.007,1.750]])
lock('right temple open short',[[.071,-.060,1.822],[.091,-.060,1.829],[.101,-.046,1.812],[.103,-.024,1.791],[.096,-.003,1.777],[.109,.015,1.758]])
lock('left behind ear medium',[[-.085,.010,1.800],[-.100,.015,1.808],[-.108,.030,1.791],[-.105,.043,1.766],[-.086,.057,1.749],[-.103,.060,1.716],[-.107,.052,1.690]])
lock('right behind ear medium',[[.085,.012,1.802],[.100,.019,1.811],[.109,.033,1.793],[.107,.047,1.769],[.090,.061,1.748],[.105,.066,1.716],[.109,.059,1.700]])
lock('left behind ear long',[[-.084,.034,1.792],[-.100,.050,1.793],[-.094,.060,1.766],[-.083,.070,1.729],[-.090,.079,1.693],[-.078,.080,1.669]])
lock('right behind ear long',[[.084,.036,1.795],[.101,.053,1.798],[.099,.065,1.770],[.087,.076,1.732],[.097,.084,1.699],[.086,.088,1.680]])
lock('left mid high connector',[[-.065,.003,1.844],[-.080,.022,1.859],[-.105,.037,1.847],[-.114,.059,1.826],[-.102,.069,1.803],[-.119,.077,1.786]])
lock('right mid high connector',[[.066,.009,1.843],[.083,.029,1.859],[.105,.044,1.845],[.117,.057,1.822],[.103,.068,1.797],[.120,.076,1.777]])

if '--design-json' in args:
    design=json.loads(Path(args[args.index('--design-json')+1]).read_text(encoding='utf-8'))
if len(design)<12:raise RuntimeError('Insufficient authored coverage')

def catmull(points):
    # Dense Catmull-Rom followed by actual arc sampling, with no Fourier curl
    # field shared by all locks. Tangents come from the authored knot layout.
    p=np.array(points,float);p=np.vstack([2*p[0]-p[1],p,2*p[-1]-p[-2]])
    result=[]
    for k in range(1,len(p)-2):
        u=np.linspace(0,1,32,endpoint=False)[:,None]
        a,b,c,d=p[k-1:k+3]
        result.append(.5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u))
    dense=np.vstack(result+[p[-2: -1]])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]
    return np.stack([np.interp(t*arc[-1],arc,dense[:,k]) for k in range(3)],axis=1)

guides=[];guide_roots=[];guide_repairs=0
head_envelope='--head-envelope' in args
guide_envelope_points=0
for item in design:
    q=catmull(item['knots_m'])
    hit,nn,_,_=bv.find_nearest(Vector(q[0]));attached=np.array(hit+nn*.00065)
    q+=(attached-q[0])[None]*(1-t[:,None])**3
    if head_envelope:
        # The first authored blockout had 20..40mm of rear air volume and
        # appeared fluffy. Shape the actual guide envelope to this head,
        # preserving loose long neck ends instead of forcing every knot onto
        # a single rounded scalp shell.
        delta=np.zeros_like(q)
        for j in range(1,N):
            hit,nn,_,distance=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(nn)
            crown=np.clip((q[j,2]-1.833)/.04,0,1)
            gate=np.clip((q[j,2]-1.743)/.028,0,1)
            spacing=.005+.006*np.sin(np.pi*t[j])**1.5+.004*crown
            if gap>spacing and distance<.075:
                delta[j]=-np.array(nn)*(gap-spacing)*gate;guide_envelope_points+=1
        for _ in range(3):delta[1:-1]=.25*delta[:-2]+.5*delta[1:-1]+.25*delta[2:]
        q+=delta
    for j in range(1,N):
        hit,nn,_,distance=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(nn)
        if gap<.0012 and distance<.035:
            q[j]=np.array(hit+nn*.0014);guide_repairs+=1
    q[0]=attached;guides.append(q);guide_roots.append(attached)
guides=np.array(guides);guide_roots=np.array(guide_roots)
ribbon_frames='--ribbon-frames' in args
frames=[]
for q in guides:
    tangent=np.gradient(q,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    _,nn,_,_=bv.find_nearest(Vector(q[0]));normal=np.empty_like(q)
    previous=np.array(nn)
    for j in range(N):
        previous-=tangent[j]*np.dot(previous,tangent[j])
        previous/=max(np.linalg.norm(previous),1e-9)
        normal[j]=previous
    across=np.cross(tangent,normal);across/=np.maximum(np.linalg.norm(across,axis=1)[:,None],1e-9)
    frames.append((tangent,normal,across))
labels=np.empty(len(roots),int);neighbor=np.empty((len(roots),3),int);mix=np.empty((len(roots),3),float)
for start in range(0,len(roots),2048):
    distance=np.sum((roots[start:start+2048,None]-guide_roots[None])**2,axis=2)
    indices=np.argsort(distance,axis=1)[:,:3]
    dd=np.take_along_axis(distance,indices,axis=1)
    ww=np.exp(-(dd-dd[:,:1])/.00016);ww/=ww.sum(axis=1)[:,None]
    neighbor[start:start+2048]=indices;mix[start:start+2048]=ww
    labels[start:start+2048]=indices[:,0]

rng=np.random.default_rng(100511)
result=np.empty_like(raw);point_repairs=0;maximum_repair=0.
blending=.35 if '--soft-boundaries' in args else .15
for i,root in enumerate(roots):
    gi=labels[i]
    pure=guides[gi]
    interpolated=np.sum(guides[neighbor[i]]*mix[i,:,None,None],axis=0)
    q=pure*(1-blending)+interpolated*blending
    # Equalize guide attachment with the actual retained follicle. The root
    # patch stays broad; its taper is gradual, leaving a small loose tip spread.
    attached=q[0].copy()
    fraction=rng.uniform(.86,1) if 'neck' in design[gi]['name'] else rng.uniform(.90,1)
    q=np.stack([np.interp(t*fraction,t,q[:,k]) for k in range(3)],axis=1)
    if ribbon_frames:
        tg,nm,ac=frames[gi]
        tg=np.stack([np.interp(t*fraction,t,tg[:,k]) for k in range(3)],axis=1)
        nm=np.stack([np.interp(t*fraction,t,nm[:,k]) for k in range(3)],axis=1)
        ac=np.stack([np.interp(t*fraction,t,ac[:,k]) for k in range(3)],axis=1)
        offset=root-attached
        a,b,d=np.dot(offset,ac[0]),np.dot(offset,nm[0]),np.dot(offset,tg[0])
        taper=1-.82*t**1.25
        # Physical lock cross sections are broad thin ribbons rather than
        # isotropic root-patch pillows. Preserve the true follicle offset at
        # t=0, collapse normal thickness early, retain gradual across spread.
        depth=b*(1-.94*np.minimum(1,t/.42)**2*(3-2*np.minimum(1,t/.42)))
        width=a*taper
        along=d*(1-t)**2.0
        # Small subordinate clumps within each authored main lock break one
        # broad specular surface into multiple fine locks. No macro curl field.
        subcenter=np.round(a/.0035)*.0035
        collapse=.55*t**2.3
        width=width*(1-collapse)+subcenter*taper*collapse
        depth+=.00035*np.sin(np.pi*t)*(np.sin(subcenter*700)+rng.normal(0,.25))
        q+=ac*width[:,None]+nm*depth[:,None]+tg*along[:,None]
    else:
        q+=(root-attached)[None]*(1-.82*t[:,None]**1.25)
    # Only submillimeter strand deviation. Large curls are in explicit knots.
    phase=rng.uniform(0,2*np.pi)
    q[:,0]+=.00035*np.sin(t*7+phase)*np.sin(np.pi*t)
    q[:,1]+=.00025*np.sin(t*8+phase*.7)*np.sin(np.pi*t)
    for j in range(1,N):
        hit,nn,_,distance=bv.find_nearest(Vector(q[j]));gap=(Vector(q[j])-hit).dot(nn)
        if head_envelope and q[j,2]>1.755 and distance<.075 and gap>.020:
            amount=(gap-.020)*min(1,t[j]/.25)
            q[j]-=np.array(nn)*amount
            gap-=amount
        if gap<.0008 and distance<.035:
            amount=.001-gap;q[j]+=np.array(nn)*amount;point_repairs+=1;maximum_repair=max(maximum_repair,amount)
    q[0]=raw[i,0];result[i]=q
assert np.array_equal(result[:,0],raw[:,0]) and np.isfinite(result).all()
data=rear.data.copy();data.attributes['position'].data.foreach_set('vector',result.ravel())
radius=np.empty(len(data.points),np.float32);data.attributes['radius'].data.foreach_get('value',radius);radius=radius.reshape(-1,N)
radius=radius[:,0,None]*(1-.997*t[None]**2.5)**.7
data.attributes['radius'].data.foreach_set('value',radius.astype(np.float32).ravel());rear.data=data

gc=bpy.data.collections.new('Authored posterior knot controls • rebake required');bpy.context.scene.collection.children.link(gc);gc.hide_render=True
for item in design:
    gd=bpy.data.curves.new(item['name'],'CURVE');gd.dimensions='3D'
    sp=gd.splines.new('POLY');sp.points.add(len(item['knots_m'])-1)
    for v,p in zip(sp.points,item['knots_m']):v.co=(*p,1)
    go=bpy.data.objects.new('Control '+item['name'],gd);gc.objects.link(go);go.hide_render=True
out.mkdir(parents=True);renders.mkdir(parents=True)
for gi,item in enumerate(design):item['assigned_fibers']=int((labels==gi).sum())
(out/'authored_posterior_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    method='31 explicitly authored full spatial knot paths for unequal crown, diagonal back, ear passage and loose long nape; actual arc interpolation, restrained local flow blending, original follicle coverage retained',
    original_authored_paths=len(design),flow_interpolation_strength=blending,
    rotation_minimizing_thin_lock_cross_sections=ribbon_frames,
    measured_head_envelope=head_envelope,guide_envelope_points=guide_envelope_points,
    rear_only=True,front_only=False,
    components=[dict(object=rear.name,curves=len(raw),actually_modified_curves=int(np.any(result!=raw,axis=(1,2)).sum()),exact_roots_preserved=True,
        maximum_displacement_m=float(np.linalg.norm(result-raw,axis=2).max()),positions_before_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),positions_after_sha256=hashlib.sha256(result.tobytes()).hexdigest())],
    guide_point_repairs=guide_repairs,fiber_point_repairs=point_repairs,maximum_fiber_point_repair_m=maximum_repair,
    saved_controls='Editable authored knot paths. Native fibers are baked after root attachment, interpolation and point repairs; not live linked.',
    collision_scope='Modified discrete points nearest head/body guard only; not full curve interiors, garment faces, eyes or motion',
    status='Unreviewed authored-flow study, not artistic acceptance')
(out/'shag_cut_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1200,1400;scene.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['02_ThreeQuarter','03_Side','04_Back']:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(renders/(name+'.png'));bpy.ops.render.render(write_still=True)
print('AUTHORED_POSTERIOR_KNOTS_RENDERED',version,len(design),flush=True)
