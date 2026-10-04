"""Recomb real baked locks into independent volumetric sublocks.

Keeps every existing root and the short coverage layer. Local source/derived
Royalty Free and CC BY-SA geometry is never exported as a standalone asset.
The result is a fresh unapproved still study requiring actual render review.
"""
import bpy,sys,re,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
version,source_version,design_version=args[:3]
PRESERVE_WIDTH='--preserve-width' in args
GENTLE='--gentle-cuts' in args
REAR_ONLY='--rear-only' in args
REFERENCE_FLOW='--reference-flow' in args
COVERAGE_LAYER='--coverage-layer' in args
SEPARATE_OVERLAYERS='--separate-overlayers' in args
TAPERED_NAPE='--tapered-nape' in args
if COVERAGE_LAYER and not REFERENCE_FLOW:raise ValueError('Coverage-layer requires reference-flow')
if SEPARATE_OVERLAYERS and not COVERAGE_LAYER:raise ValueError('Separate-overlayers requires coverage-layer')
if TAPERED_NAPE and not SEPARATE_OVERLAYERS:raise ValueError('Tapered-nape requires separate-overlayers')
if not all(re.fullmatch('[A-Za-z0-9_-]+',v) for v in args[:3]):raise ValueError(args)
if source_version not in {'regionalgroom19','smoothflow02'}:
 raise ValueError('This experimental grouping requires the visible canonical regionalgroom19 rear; recombed sources could duplicate hidden original geometry')
if source_version=='smoothflow02' and not (REFERENCE_FLOW and REAR_ONLY and PRESERVE_WIDTH):
 raise ValueError('The surface-covered smoothflow02 checkpoint requires reference-flow, rear-only and preserve-width')
out,render=ROOT/'Exports'/version,ROOT/'Renders'/version
if out.exists() or render.exists():raise RuntimeError('Fresh output required')
out.mkdir(parents=True);render.mkdir(parents=True)
source=ROOT/'Exports'/source_version/'Ember_Regent.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
body=bpy.data.objects['CC0 male body • retained topology'];bpy.context.view_layer.update()
bv=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
C=np.array([0,-.044,1.771]);rng=np.random.default_rng(100441)

def read(ob):
 cu=ob.data;sizes=[len(c.points) for c in cu.curves]
 if len(set(sizes))!=1:raise RuntimeError('Uniform point counts required')
 N=sizes[0];p=np.empty(len(cu.points)*3,np.float32)
 cu.attributes['position'].data.foreach_get('vector',p)
 r=np.empty(len(cu.points),np.float32);cu.attributes['radius'].data.foreach_get('value',r)
 return p.reshape(-1,N,3),r.reshape(-1,N)

front=next(o for o in bpy.data.objects if not o.hide_render and o.name.startswith('Authored frontal revision'))
rear=bpy.data.objects['Ddr Rcs derivative • whole rear locks']
if rear.hide_render or any(o.name.startswith('Volumetric recomb') and not o.hide_render for o in bpy.data.objects):
 raise ValueError('Canonical rear must be visible, without an already-recombed visible replacement')
original=bpy.data.objects['Licensed Ddr Rcs derivative • actual native curves']
original_p,_=read(original)
records=json.loads((ROOT/'Exports/nativeasset02/licensed_groom_design.json').read_text(encoding='utf-8'))
rear_groups=[];offset=0
for record in records:
 count=record['fibers'];group=original_p[offset:offset+count];offset+=count
 if not count:continue
 center=np.median(group,axis=0);root,end=center[0],center[-1]
 discarded=record['kind']=='asymmetric extended wavy bang'
 discarded|=end[1]<-.132 and end[2]>1.725
 discarded|=end[1]<-.098 and root[1]<-.034 and end[2]>1.700
 discarded|=root[1]<-.070 and root[2]<1.821
 if not discarded:rear_groups.append({'name':'retained side/rear','count':count})
assert offset==len(original_p)
assert sum(r['count'] for r in rear_groups)==len(rear.data.curves)
design=json.loads((ROOT/'Exports'/design_version/'authored_fringe_design.json').read_text(encoding='utf-8'))
front_groups=[{'name':r['name'],'count':r['assigned_visible_fibers']} for r in design]
assert sum(r['count'] for r in front_groups)==len(front.data.curves)

col=bpy.data.collections.new('05_Volumetric_Sublock_Flow');bpy.context.scene.collection.children.link(col)
report=dict(version=version,source=source_version,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            design_source=design_version,method='Sort real roots into smaller sublocks, recomb coherent spatial flow, varied along-growth layer cuts; preserve all roots',
            components=[],status='unreviewed actual 3D study',
            license='Project original frontal roots/design; Ddr Rcs Royalty Free rear; Bystedt CC BY-SA short support retained',
            collision_scope='Nearest-body point checks only; not exhaustive scalp/clothing/motion validation')
for ob,groups,is_rear in [(front,front_groups,False),(rear,rear_groups,True)]:
 if REAR_ONLY and not is_rear:continue
 raw,radii=read(ob);N=raw.shape[1];t=np.linspace(0,1,N)
 result=raw.copy();offset=0;sublocks=0;repairs=0;shortened=0;coverage_count=0
 for group_index,record in enumerate(groups):
  count=record['count'];p=raw[offset:offset+count].astype(float)
  parent=np.median(p,axis=0);root=parent[0];tip=parent[-1]
  direction=parent[min(6,N-1)]-root
  normal=root-C;normal/=max(np.linalg.norm(normal),1e-8)
  across=np.cross(direction,normal);across/=max(np.linalg.norm(across),1e-8)
  ordered=np.argsort((p[:,0]-root)@across)
  # Existing flat card widths become independently flowing small patches.
  # Every actual donor/authored root remains represented, including rear scalp.
  parts=[ordered[k::3] for k in range(3)] if COVERAGE_LAYER else np.array_split(ordered,3 if is_rear else 2)
  if SEPARATE_OVERLAYERS:
   # The intact base spans all root positions; overlying locks use adjacent
   # smaller root patches, rather than two full-width interleaved fans.
   coverage=ordered[2::3]
   rest=ordered[np.arange(len(ordered))%3!=2]
   halves=np.array_split(rest,2);parts=[halves[0],halves[1],coverage]
  for child,ids in enumerate(parts):
   if not len(ids):continue
   if COVERAGE_LAYER and child==2:
    # An interleaved third of every complete native lock spans the entire
    # original cross-section. Keep these actual points wholly unchanged.
    # It supplies continuous lower coverage under the independently cut layers.
    coverage_count+=len(ids)
    continue
   sublocks+=1;old=p[ids];base=np.median(old,axis=0)
   q=1.
   crown='segmented crown' in record['name']
   if is_rear and root[2]>1.814:
    # Different cut lengths make short overlying crown leaves while the third
    # sublock and all lower growth keep coverage to the sides and nape.
    q=([.88,.96,1.] if GENTLE else [.66,.83,1.])[child]
   elif is_rear:q=([.96,1.,1.] if GENTLE else [.88,.96,1.])[child]
   elif crown:q=[.85,1.][child]
   else:q=[.91,1.][child]
   if REFERENCE_FLOW:
    q=([.82,.94,1.] if root[2]>1.814 else [.97,1.,1.])[child]
   original_base=base.copy()
   if q<1:
    base=np.stack([np.interp(t*q,t,base[:,j]) for j in range(3)],axis=1)
    shortened+=len(ids)
   tangent=np.gradient(base,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
   radial=base-C;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-8)
   n=radial-tangent*np.sum(radial*tangent,axis=1)[:,None]
   n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-8)
   a=np.cross(tangent,n)
   phase=(group_index*2.399963+child*1.72)%6.283185
   strength=.0045 if is_rear else (.0035 if crown else .0018)
   if REFERENCE_FLOW:strength=.0065
   envelope=np.sin(np.pi*t)**1.3
   base+=a*(strength*np.sin(t*2.2*np.pi+phase)*envelope)[:,None]
   normal_strength=.0075 if SEPARATE_OVERLAYERS else (.0025 if is_rear else .0015)
   base+=n*(normal_strength*np.sin(t*1.5*np.pi+phase*.65)*envelope)[:,None]
   # Lift short side leaves away from the smooth outer shell at their tips.
   if is_rear and child==0 and root[2]>1.814:
    side=1 if tip[0]>=0 else -1
    base[:,0]+=side*.006*t**3
    base[:,1]+=.003*t**3
   if REFERENCE_FLOW and tip[1]>.025 and tip[2]<1.726 and root[2]<1.831:
    # Long tapered nape grows underneath the shortened upper layers. Move
    # actual points with a smooth root-zero envelope; keep the original root.
    extension=.030+.017*(.5+.5*np.sin(group_index*1.731+child))
    if TAPERED_NAPE:
     # A long central neck fall and shorter outer ends create a tapered
     # silhouette, rather than uniformly extending the old round hem.
     extension=.038+.040*np.exp(-(tip[0]/.052)**2)+.009*(.5+.5*np.sin(group_index*1.731+child))
    base[:,2]-=extension*t**2.8
    base[:,1]+=.012*t**2.8
    if TAPERED_NAPE:
     base[:,0]+=.005*np.sin(t*1.65*np.pi+phase)*t**2
     base[:,1]+=.004*np.sin(t*1.40*np.pi+phase*.60)*t**2
   for j,index in enumerate(ids):
    s=base.copy()
    if PRESERVE_WIDTH:
     residual=old[j]-original_base
     if q<1:residual=np.stack([np.interp(t*q,t,residual[:,k]) for k in range(3)],axis=1)
     s+=residual*(1-(.28 if COVERAGE_LAYER else .65)*t[:,None])
    else:s+=(old[j,0]-base[0])[None,:]*(1-t[:,None])**2.0
    width=rng.normal(0,.0011 if is_rear else .0009)
    depth=rng.normal(0,.0010)
    volume=(1-np.exp(-t*16))*(.14+.86*(1-t)**.7)
    s+=(a*width+n*depth)*volume[:,None]
    phi=rng.uniform(0,6.283185)
    s+=n*(.00045*np.sin(t*7+phi)*np.sin(np.pi*t))[:,None]
    if rng.random()<.64:
     fraction=rng.uniform(.88,.999)
     s=np.stack([np.interp(t*fraction,t,s[:,k]) for k in range(3)],axis=1)
    for k,point in enumerate(s):
     hit,hn,face,dist=bv.find_nearest(Vector(point));gap=(Vector(point)-hit).dot(hn)
     if k and gap<.00075 and dist<.035:
      s[k]=np.array(hit+hn*.0009);repairs+=1
    s[0]=old[j,0] # exact real root preserved
    result[offset+index]=s.astype(np.float32)
  offset+=count
 assert offset==len(raw)
 assert np.isfinite(result).all() and np.array_equal(result[:,0],raw[:,0])
 cu=ob.data.copy();cu.attributes['position'].data.foreach_set('vector',result.ravel())
 new=bpy.data.objects.new('Volumetric recomb • '+('retained rear' if is_rear else 'authored front'),cu)
 col.objects.link(new);new.matrix_world=ob.matrix_world.copy();ob.hide_render=True;ob.hide_viewport=True
 report['components'].append(dict(object=new.name,strands=len(raw),parent_locks=len(groups),volumetric_sublocks=sublocks,
                                 cut_strands=shortened,body_clearance_repairs=repairs,all_roots_preserved_exactly=True,
                                 untouched_interleaved_coverage_curves=coverage_count))
scene=bpy.context.scene;pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64 if '--draft' in args else 192
scene.cycles.use_denoising=False;scene.cycles_curves.shape='THICK'
scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.resolution_percentage=80 if '--draft' in args else 100
report.update(draft='--draft' in args,samples=scene.cycles.samples,
              preserve_actual_lock_width=PRESERVE_WIDTH,gentle_along_growth_cuts=GENTLE,rear_only=REAR_ONLY,
              processing_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
report['reference_flow']=REFERENCE_FLOW
report['interleaved_original_coverage_layer']=COVERAGE_LAYER
report['separate_narrow_overlying_root_patches']=SEPARATE_OVERLAYERS
report['tapered_central_nape_extension']=TAPERED_NAPE
if source_version=='smoothflow02':report['license']+='; Abhay Pratap Royalty Free flow-derived scalp support retained'
(out/'flow_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ember_Regent.blend'))
for name in ['01_Front','02_ThreeQuarter','03_Side','04_Back']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(render/(name+'.png'))
 bpy.ops.render.render(write_still=True)
print('VOLUMETRIC_RECOMB_RENDERED',version,flush=True)
