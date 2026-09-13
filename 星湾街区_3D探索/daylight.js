import * as THREE from 'three';
export function createDaylight(scene,sun,hemi,sky,renderer){
 sky.material.uniforms.uNight={value:0};
 sky.material.fragmentShader='uniform float uNight;\n'+sky.material.fragmentShader.replace('gl_FragColor = vec4( retColor, 1.0 );','gl_FragColor = vec4( mix(retColor, vec3(0.003, 0.006, 0.017), uNight), 1.0 );');sky.material.needsUpdate=true;
 const starsGeo=new THREE.BufferGeometry(),coords=[];let seed=491;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
 for(let i=0;i<550;i++){const a=rnd()*Math.PI*2,y=.15+rnd()*.85,r=Math.sqrt(1-y*y);coords.push(Math.cos(a)*r*390,y*390,Math.sin(a)*r*390);}
 starsGeo.setAttribute('position',new THREE.Float32BufferAttribute(coords,3));const stars=new THREE.Points(starsGeo,new THREE.PointsMaterial({color:0xdceaff,size:.75,transparent:true,opacity:0,depthWrite:false}));scene.add(stars);
 const moon=new THREE.DirectionalLight(0x9ab8ef,0);moon.position.set(65,110,-40);scene.add(moon);
 const moonDisc=new THREE.Mesh(new THREE.SphereGeometry(3,16,12),new THREE.MeshBasicMaterial({color:0xd9e6ff}));moonDisc.position.set(180,230,-180);scene.add(moonDisc);
 const lights=[];
 for(const [x,z] of [[-103,22],[-65,22],[7,38],[94,34],[103,-31],[-43,14],[-43,-14],[9,14],[9,-14],[52,14],[52,-14],[99,14],[99,-14],[-83,-14]]){const l=new THREE.PointLight(0xffcb87,0,26,1.25);l.position.set(x,6,z);scene.add(l);lights.push(l);}
 const lit=[],glass=[];let daylight=1,night=0;
 function bind(root){root.traverse(o=>{if(o.isMesh){for(const m of Array.isArray(o.material)?o.material:[o.material]){if(['lamp','interiorGlow','worldGlow','redLight'].includes(m.name)&&!lit.some(v=>v.m===m))lit.push({m,base:m.emissiveIntensity});if(m.name==='glass1'&&!glass.includes(m))glass.push(m);}}});}
 function update(hour){const altitude=Math.sin((hour-6)/24*Math.PI*2);daylight=THREE.MathUtils.smoothstep(altitude,-.08,.28);night=1-daylight;
  sun.position.set(Math.cos((hour-6)/24*Math.PI*2)*140,altitude*150,45);sun.intensity=Math.max(0,altitude)*2.9;sun.color.setHSL(.08+.045*daylight,.42-.22*daylight,.82);sun.castShadow=altitude>0;
  sky.visible=true;sky.material.uniforms.uNight.value=1-THREE.MathUtils.smoothstep(altitude,-.20,.12);sky.material.uniforms.sunPosition.value.copy(sun.position).normalize();
  scene.background.set('#080f24');scene.fog.color.copy(new THREE.Color('#111c35').lerp(new THREE.Color('#adb9b7'),daylight));
  hemi.intensity=.27+daylight*1.65;hemi.color.set(daylight>.5?0xc3d7e5:0x6e8fbf);moon.intensity=night*.32;moonDisc.visible=night>.6;stars.material.opacity=night*.8;
  scene.environmentIntensity=.065+.235*daylight;renderer.toneMappingExposure=.86+night*.20;
  lights.forEach(l=>l.intensity=night*58);lit.forEach(({m,base})=>m.emissiveIntensity=m.name==='interiorGlow'?base*.8:base*(.08+night*.92));glass.forEach(m=>{m.emissive.set(0xffbe6b);m.emissiveIntensity=night*.22;});
 }
 return {bind,update,inspect:()=>({daylight,night,streetIntensity:lights[0].intensity,sunIntensity:sun.intensity,starsOpacity:stars.material.opacity})};
}
