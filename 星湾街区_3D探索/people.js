import * as THREE from './vendor/three.module.js';
const TAU=Math.PI*2,clamp=THREE.MathUtils.clamp;
export function bindPerson(model,spec){
 const root=model.scene.clone(true),joints={};root.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}if(['Hips','Torso','Head','UpperLeg_L','UpperLeg_R','LowerLeg_L','LowerLeg_R','Foot_L','Foot_R','UpperArm_L','UpperArm_R','LowerArm_L','LowerArm_R'].includes(o.name))joints[o.name]=o;});
 if(Object.keys(joints).length!==13)throw Error('Character joint map incomplete: '+spec.id+' '+Object.keys(joints).length);
 return {root,spec,joints,phase:0,walkBlend:0,animationTime:0,footTargets:{},lastDistance:0};
}
export function posePerson(n,dt,distance){
 const s=n.spec,j=n.joints;n.animationTime+=dt;n.lastDistance=distance;n.walkBlend=THREE.MathUtils.damp(n.walkBlend,distance>.00001?1:0,12,dt);
 n.phase=(n.phase+distance/(s.stepLength/.6))%1;
 j.Hips.position.y=s.hipHeight+(Math.cos(n.phase*TAU*2)*s.height*.003-s.height*.012)*n.walkBlend;
 j.Torso.rotation.x=s.id==='elder'?.07:0;j.Torso.rotation.z=Math.sin(n.phase*TAU)*.015*n.walkBlend;j.Head.rotation.x=s.id==='elder'?-.035:Math.sin(n.animationTime*1.4)*.008;
 for(const [side,offset,sign] of [['L',0,1],['R',.5,-1]]){
  const phase=(n.phase+offset)%1;let forward,lift=0;
  if(phase<.6)forward=s.stepLength*(.5-phase/.6);else{const t=(phase-.6)/.4;forward=s.stepLength*(-.5+t);lift=Math.sin(Math.PI*t)*s.height*(s.id==='elder'?.035:.058);}
  forward*=n.walkBlend;lift*=n.walkBlend;
  const down=j.Hips.position.y-(s.footHeight+lift),d=clamp(Math.hypot(down,forward),.03,s.legUpper+s.legLower-.0001);
  const a=Math.acos(clamp((s.legUpper**2+d*d-s.legLower**2)/(2*s.legUpper*d),-1,1));
  const hip=-Math.atan2(forward,down)-a,knee=Math.PI-Math.acos(clamp((s.legUpper**2+s.legLower**2-d*d)/(2*s.legUpper*s.legLower),-1,1));
  j['UpperLeg_'+side].rotation.x=hip;j['LowerLeg_'+side].rotation.x=knee;j['Foot_'+side].rotation.x=-hip-knee;
  j['UpperArm_'+side].rotation.x=Math.cos((n.phase+offset)*TAU)*.29*n.walkBlend;j['UpperArm_'+side].rotation.z=sign*.055;j['LowerArm_'+side].rotation.x=-.10-.10*n.walkBlend;
  n.footTargets[side]={forward,height:s.footHeight+lift,phase,stance:phase<.6};
 }
 n.root.updateMatrixWorld(true);
}
export function inspectFeet(n){return ['L','R'].map(side=>({side,...n.footTargets[side],world:n.joints['Foot_'+side].getWorldPosition(new THREE.Vector3()).toArray()}));}
