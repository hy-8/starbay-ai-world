"""Fit CC0 anatomical finger segments to the UE bind skeleton before skinning.

Uses the explicitly CC0 MakeHuman rig/weights, preserving original hand topology.
The Epic hand is a joint placement reference, not a source mesh replacement.
"""
import json
from mathutils import Vector
from mathutils.kdtree import KDTree

class HandBinding:
    def __init__(self,root,rig):
        source=root/'Source'
        data=json.loads((source/'default.mhskel').read_text(encoding='utf-8'))
        weights=json.loads((source/'default_weights.mhw').read_text(encoding='utf-8'))
        assert data['license']=='CC0' and weights['license']=='CC0'
        raw=[Vector(tuple(map(float,l.split()[1:4]))) for l in (source/'base.obj').read_text().splitlines() if l.startswith('v ')]
        for line in (source/'male_young.target').read_text().splitlines():
            p=line.split()
            if len(p)==4 and p[0].isdigit():raw[int(p[0])]+=Vector(tuple(map(float,p[1:])))
        points=[Vector((p.x*.115,-p.z*.115,(p.y+8.188)*.115)) for p in raw]
        joint=lambda key:sum((points[i] for i in data['joints'][key]),Vector())/len(data['joints'][key])
        self.transforms={};self.names={};self.native={};vertex_weights={}
        for name,entries in weights['weights'].items():
            if not name.startswith(('finger','wrist','metacarpal')):continue
            side=name[-1].lower();desc=data['bones'][name];h=joint(desc['head']);t=joint(desc['tail'])
            original_h=h.copy();original_t=t.copy()
            if name.startswith('finger'):
                digit,j=name.split('.')[0].replace('finger','').split('-');digit=int(digit);j=int(j)
                ue=['thumb','index','middle','ring','pinky'][digit-1]+'_%02d_'%j+side
                b=rig.data.bones[ue];nh=rig.matrix_world@b.head_local
                if j<3:nt=rig.matrix_world@rig.data.bones[ue.replace('_%02d_'%j,'_%02d_'%(j+1))].head_local
                else:nt=rig.matrix_world@b.tail_local
            else:
                ue='hand_'+side;b=rig.data.bones[ue];nh=rig.matrix_world@b.head_local
                nt=rig.matrix_world@rig.data.bones['middle_01_'+side].head_local
                h=joint(data['bones']['wrist.'+side.upper()]['head'])
                t=joint(data['bones']['finger3-1.'+side.upper()]['head'])
            axis=(t-h).normalized();other=(nt-nh).normalized();q=axis.rotation_difference(other)
            ratio=max(.55,min(1.4,(nt-nh).length/max(.001,(t-h).length)))
            self.transforms[name]=(h,nh,axis,q,ratio);self.names[name]=ue
            if name.startswith('finger'):
                native='grip_'+side.upper()+'_'+['thumb','index','middle','ring','pinky'][digit-1]+'_'+str(j)
                parent='hand_'+side if j==1 else native[:-1]+str(j-1)
                self.native[native]=(original_h,original_t,parent)
                self.names[name]=native
            for idx,w in entries:vertex_weights.setdefault(idx,{})[name]=w
        self.points=points;self.weights=vertex_weights
        self.tree=KDTree(len(vertex_weights))
        for idx in vertex_weights:self.tree.insert(points[idx],idx)
        self.tree.balance()
        self.target_tree=KDTree(len(vertex_weights));self.target_weights={}
        for idx in vertex_weights:
            co=points[idx];ws=vertex_weights[idx];total=sum(ws.values());w={}
            for k,v in ws.items():w[self.names[k]]=w.get(self.names[k],0)+v/total
            self.target_tree.insert(co,idx);self.target_weights[idx]=w
        self.target_tree.balance()

    def fit(self,co):
        return co,{}

    def add_bones(self,rig):
        for name,(h,t,parent) in self.native.items():
            b=rig.data.edit_bones.new(name);b.head=h*100;b.tail=t*100;b.parent=rig.data.edit_bones[parent]

    def staff_center(self):
        h=self.native['grip_L_middle_1'][0]
        return h+Vector((-.004,-.022,.004))

    def skin(self,co):
        hits=self.target_tree.find_n(co,4)
        if hits[0][2]>.025 or sum(self.weights[hits[0][1]].values())<.9:return None
        out={}
        for _,idx,dist in hits:
            factor=1/max(.001,dist)**3
            for k,v in self.target_weights[idx].items():out[k]=out.get(k,0)+v*factor
        total=sum(out.values());return {k:v/total for k,v in out.items()}
