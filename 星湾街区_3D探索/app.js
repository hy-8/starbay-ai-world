import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {Sky} from './vendor/Sky.js';
import {Game,places,templates} from './game.js';
import {createDaylight} from './daylight.js';
import {createGameUI} from './game-ui.js';
import {bindPerson,posePerson,inspectFeet} from './people.js';
import {nodeData,labels,destinations,edges,adjacency,route} from './navigation.js';
const $=id=>document.getElementById(id),canvas=$('world');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.85;
const scene=new THREE.Scene();scene.background=new THREE.Color('#a3b4bb');scene.fog=new THREE.FogExp2('#adb9b7',.0019);
const camera=new THREE.PerspectiveCamera(64,innerWidth/innerHeight,.08,800);camera.position.set(-43,17,48);
const controls=new OrbitControls(camera,canvas);controls.target.set(27,12,-26);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.48;controls.minDistance=3;controls.maxDistance=260;controls.update();
const hemi=new THREE.HemisphereLight(0xc3d7e5,0x4b4437,1.75);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffd3a0,3.1);sun.position.set(-80,75,70);sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-140,right:140,top:120,bottom:-120,near:1,far:350});sun.shadow.bias=-.0003;sun.shadow.normalBias=.1;sun.target.position.set(0,0,-10);scene.add(sun,sun.target);
const sky=new Sky();sky.scale.setScalar(1000);scene.add(sky);const uniforms=sky.material.uniforms;uniforms.turbidity.value=7;uniforms.rayleigh.value=1.5;uniforms.mieCoefficient.value=.005;uniforms.sunPosition.value.copy(sun.position).normalize();
const pmrem=new THREE.PMREMGenerator(renderer),envScene=new THREE.Scene();envScene.add(sky.clone());scene.environment=pmrem.fromScene(envScene,.04).texture;scene.environmentIntensity=.3;
for(const [x,z] of [[26,-28],[45,-43],[70,-46],[49,-67],[19,-49]]){const light=new THREE.PointLight(0xffe3b1,38,21,1.3);light.position.set(x,4.8,z);scene.add(light);}
let manifest,mode='orbit',ready=false,people=true,aiEnabled=false,aiAvailable=false,aiBusy=false,modelName='',simTime=0,selected=null,lastAI=0,aiCursor=0,day=false,yaw=0,pitch=0,paused=false;
const keys=new Set(),npcs=[],doors=[],clock=new THREE.Clock();let doorAmount=0;
const game=new Game(localStorage,toast);
const daylight=createDaylight(scene,sun,hemi,sky,renderer);
function saveGame(){const p=mode==='walk'?camera.position:{x:game.state.player[0],z:game.state.player[1]};return game.save(p,mode==='walk'?yaw:game.state.heading,mode==='walk');}
const gameUI=createGameUI(game,scene,{position:()=>camera.position,walking:()=>mode==='walk',release:()=>{keys.clear();document.exitPointerLock();},notify:toast,save:saveGame});
window.addEventListener('pagehide',saveGame);
document.addEventListener('visibilitychange',()=>{keys.clear();clock.getDelta();if(document.hidden)saveGame();});
const nodes=Object.fromEntries(Object.entries(nodeData).map(([k,[x,z]])=>[k,new THREE.Vector3(x,.14,z)]));
const names=['林予安','陈知夏','沈伯伯','小禾','陆远','宋青','顾伯伯','小宇','江川','程雨','梁爷爷','小木'];
function toast(s){$('toast').textContent=s;$('toast').style.opacity=1;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').style.opacity=0,4500);}
function inside(p){const i=manifest?.interior;return !!i&&p.x>i.minX&&p.x<i.maxX&&p.z<i.maxZ&&p.z>i.minZ;}
function validPosition(x,z,r=.28){if(!manifest)return true;const b=manifest.bounds;return x>=b[0]&&x<=b[1]&&z>=b[2]&&z<=b[3]&&!manifest.colliders.some(c=>Math.abs(x-c.x)<c.w/2+r&&Math.abs(z-c.z)<c.d/2+r);}
function green(){return simTime%46<21;}
function schedule(n,d,source='本地需求',reason='根据当前需要选择去处'){
 if(!destinations.includes(d))return;n.intent={destination:d,source,reason,time:simTime};
 if(n.path.length&&n.root.position.distanceTo(nodes[n.node])>.2){n.pendingGoal=d;return;}setGoal(n,d);
}
function setGoal(n,d){n.destination=d;n.path=route(n.node,d).slice(1);n.wait=0;n.edgeEntered=false;n.pendingGoal=null;n.arrived=false;}
function choose(n){const allowed=n.spec.id==='child'?['mall','atrium','toys','rest','insideCafe']:destinations;
 const isNight=game.hour>=19||game.hour<6;
 const target=allowed.filter(d=>d!==n.node).map(d=>({d,score:Math.random()*.8+(isNight&&['rest','market','insideCafe','art'].includes(d)?.7:0)+(['garden','rest'].includes(d)?n.needs.energy*1.3:0)+(['cafe','insideCafe'].includes(d)?n.needs.thirst*1.2:0)+(['mall','books','toys','atrium'].includes(d)?n.needs.interest:0)})).sort((a,b)=>b.score-a.score)[0].d;schedule(n,target,'本地需求','按休息、饮水和逛街需求选择目的地');}
function stop(n,dt,state){n.speedNow=THREE.MathUtils.damp(n.speedNow,0,14,dt);n.state=state;posePerson(n,dt,0);}
function advanceNPC(n,dt){
 n.needs.energy=Math.min(1,n.needs.energy+dt*.002);n.needs.thirst=Math.min(1,n.needs.thirst+dt*.0015);n.needs.interest=Math.min(1,n.needs.interest+dt*.001);
 if(n.talking>0){n.talking-=dt;stop(n,dt,'停步交谈');return;}
 if(n.wait>0){n.wait-=dt;stop(n,dt,['rest','garden'].includes(n.destination)?'休息，看一会儿周围':'在'+labels[n.destination]+'停留');return;}
 if(!n.path.length){if(!n.arrived){n.arrived=true;n.escort=false;n.wait=6+Math.random()*10;if(['garden','rest'].includes(n.destination))n.needs.energy=.05;if(['cafe','insideCafe'].includes(n.destination))n.needs.thirst=.05;n.needs.interest*=.5;stop(n,dt,'到达'+labels[n.destination]);return;}choose(n);}
 if(!n.path.length){stop(n,dt,'观察周围');return;}
 if(n.escort&&mode==='walk'&&n.root.position.distanceTo(camera.position)>8){stop(n,dt,'带路中：停下来等你跟上');return;}
 const next=n.path[0],target=nodes[next],edge=adjacency[n.node].find(e=>e.to===next),p=n.root.position;
 if(edge.cross&&!n.edgeEntered&&!green()){stop(n,dt,'等待行人绿灯');return;}
 const delta=target.clone().sub(p);delta.y=0;const distance=delta.length();
 if(distance<.14){p.copy(target);n.node=next;n.path.shift();n.edgeEntered=false;if(n.pendingGoal)setGoal(n,n.pendingGoal);posePerson(n,dt,0);return;}
 let wanted=delta.clone().normalize();const separation=new THREE.Vector3();
 for(const other of npcs){if(other===n)continue;const v=p.clone().sub(other.root.position);v.y=0;const d=v.length();if(d>.005&&d<.85)separation.addScaledVector(v.normalize(),(.85-d)*.7);}
 wanted.add(separation).normalize();const desiredYaw=Math.atan2(wanted.x,wanted.z),error=Math.atan2(Math.sin(desiredYaw-n.root.rotation.y),Math.cos(desiredYaw-n.root.rotation.y));
 n.root.rotation.y+=THREE.MathUtils.clamp(error,-dt*3.4,dt*3.4);
 const remaining=Math.atan2(Math.sin(desiredYaw-n.root.rotation.y),Math.cos(desiredYaw-n.root.rotation.y));
 const targetSpeed=n.spec.speed*Math.max(0,Math.cos(remaining))*(n.escort?.83:1);n.speedNow=THREE.MathUtils.damp(n.speedNow,targetSpeed,5,dt);
 const forward=new THREE.Vector3(Math.sin(n.root.rotation.y),0,Math.cos(n.root.rotation.y)),travel=Math.min(distance,n.speedNow*dt),candidate=p.clone().addScaledVector(forward,travel);let actual=0;
 if(validPosition(candidate.x,candidate.z,.20)){actual=p.distanceTo(candidate);p.copy(candidate);n.edgeEntered=true;n.blocked=0;}else{n.blocked+=dt;n.speedNow=0;if(n.blocked>.4)n.root.rotation.y=Math.atan2(delta.x,delta.z);}
 n.state=actual>.0001?(n.escort?'为你带路，前往':edge.cross?'过斑马线，前往':'走向')+labels[n.destination]:'转身或调整路线';posePerson(n,dt,actual);
}
function showNPC(n,open=true){selected=n;if(open&&mode==='walk')document.body.classList.add('npc-open');$('npcname').textContent=n.name+' · '+n.spec.label;$('npcstate').textContent=n.state;$('speech').textContent=n.say||'你好，我在附近走走。你想去哪儿？';showIntent(n);}
function showIntent(n){const dest=n.pendingGoal||n.destination;$('intent').textContent=`目标：${labels[dest]} · ${n.pendingGoal?'走完当前路段后转向':n.path.length?'正在执行':'已到达'}`;$('intentSource').textContent=`决定来自：${n.intent.source}　${n.intent.reason}`;$('needs').textContent=`休息 ${Math.round(n.needs.energy*100)}% · 饮水 ${Math.round(n.needs.thirst*100)}%`;}
function nearest(){return npcs.reduce((b,n)=>!b||n.root.position.distanceTo(camera.position)<b.root.position.distanceTo(camera.position)?n:b,null);}
async function askAI(n,message='',silent=false){
 if(aiBusy){if(!silent)toast('正在处理另一次对话，请稍候。');return;}
 if(!aiEnabled||!aiAvailable){if(!silent){const matches=[['小集','market'],['公园','park'],['光环','art'],['驿站','courier'],['长廊','overlook'],['书','books'],['咖啡','insideCafe'],['玩','toys'],['休息','rest'],['商场','atrium'],['星湾','mall']],d=matches.find(([w])=>message.includes(w))?.[1];if(d){schedule(n,d,'本地关键词','从你的文字中识别目的地');n.escort=true;n.say='可以，去'+labels[d]+'吧。';}else n.say='我准备去'+labels[n.destination]+'。开启 AI 后可以自由聊天。';showNPC(n);}return;}
 aiBusy=true;if(!silent){n.talking=110;$('send').disabled=true;$('speech').textContent='正在想怎么回答你…';}
 try{const r=await fetch(message?'/api/chat':'/api/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n.name,kind:n.spec.id,age:n.spec.age,personality:n.personality,state:n.state,currentNode:n.node,currentZone:inside(n.root.position)?'推测室内':'外部街区',worldTime:game.clockText(),destination:n.destination,needs:n.needs,history:n.history.slice(-6),message:message||'根据现在的需要选择接下来的目的地。'}),signal:AbortSignal.timeout(105000)});
  const data=await r.json();if(!r.ok)throw Error(data.error||'AI unavailable');n.say=data.say||'我想在附近走走。';n.aiDecisions++;
  if(data.destination){schedule(n,data.destination,data.destinationSource==='user'?'你的指令（AI 对话）':'Qwen 本地 AI',data.reason||'理解对话和当前需求后选择');if(message&&/带|跟|一起/.test(message))n.escort=true;}
  if(message)n.history.push({role:'user',content:message},{role:'assistant',content:n.say});if(selected===n)showNPC(n,!silent);$('model').textContent=`Qwen 本地 AI · 已完成 ${npcs.reduce((s,x)=>s+x.aiDecisions,0)} 次决定`;
 }catch(e){if(!silent){n.say='我还没想好，我们先在附近看看吧。';showNPC(n);toast('AI 暂时未响应，普通寻路继续运行。');}console.warn('AI:',e.message);}
 finally{aiBusy=false;n.talking=message?2:0;$('send').disabled=false;}
}
async function detectAI(){try{const d=await(await fetch('/api/ai/status')).json();aiAvailable=d.available;modelName=d.model||'';return d.available;}catch{return false;}}
async function load(){try{
 const loader=new GLTFLoader();manifest=await(await fetch('./assets/scene.json?v=5')).json();const environment=await loader.loadAsync('./assets/starbay_environment.glb?v=5',e=>{if(e.total)$('loadstatus').textContent='街区与室内 '+Math.round(e.loaded/e.total*100)+'%';});
 environment.scene.traverse(o=>{if(o.isMesh){o.castShadow=!o.name.startsWith('EntryDoor');o.receiveShadow=true;}if(o.name==='EntryDoor_L'||o.name==='EntryDoor_R')doors.push({ob:o,x:o.position.x,side:o.name.endsWith('_L')?-1:1});});scene.add(environment.scene);daylight.bind(environment.scene);daylight.update(game.hour);
 const specs=await(await fetch('./assets/npc_catalog.json?v=5')).json(),models=await Promise.all(specs.map(s=>loader.loadAsync('./assets/'+s.file+'?v=5'))),starts=['garden','mall','rest','toys','west','insideCafe','northwest','atrium','books','east','southwest','mall'];
 for(let i=0;i<12;i++){const spec=specs[i%4],rig=bindPerson(models[i%4],spec),start=starts[i];rig.root.position.copy(nodes[start]);if(i===11)rig.root.position.x+=.7;scene.add(rig.root);
  const n={...rig,name:names[i],personality:spec.id==='elder'?'慢慢散步，喜欢休息和看书':spec.id==='child'?'和家人在商场活动，喜欢童趣区':spec.id==='woman'?'喜欢咖啡和书店，乐于指路':'下班后散步，乐于指路',node:start,path:[],destination:start,pendingGoal:null,wait:0,arrived:true,edgeEntered:false,talking:0,speedNow:0,blocked:0,escort:false,state:'观察周围',say:'',needs:{energy:Math.random(),thirst:Math.random(),interest:Math.random()},intent:{source:'本地需求',reason:'刚到街区',destination:start},history:[],aiDecisions:0};npcs.push(n);posePerson(n,0,0);choose(n);}
 ready=true;$('enter').disabled=false;$('enter').textContent=game.resumed?'继续我的街区旅程 →':'开始街区生活 →';$('loadstatus').textContent='星湾街区 · 虚构世界 / 都市居民 / 昼夜委托';showNPC(npcs[0]);aiEnabled=await detectAI();$('ai').textContent='AI：'+(aiEnabled?'开':'未连接');$('model').textContent=aiEnabled?`${modelName} · 在本机运行`:'本地行为运行中';if(aiEnabled){lastAI=simTime;askAI(npcs[0],'',true);}
}catch(e){$('loadstatus').textContent='加载失败：'+e.message;console.error(e);}}
function walk(lock=true,position=[4,1.72,22],heading=-.34){if(!ready)return;mode='walk';controls.enabled=false;camera.position.set(...position);yaw=heading;pitch=0;camera.rotation.order='YXZ';camera.rotation.set(pitch,yaw,0);document.body.classList.add('exploring','walking');if(lock)canvas.requestPointerLock().catch(()=>{});}
function orbit(){mode='orbit';document.exitPointerLock();document.body.classList.remove('walking');document.body.classList.add('exploring');controls.enabled=true;camera.position.set(-81,105,113);controls.target.set(6,6,-7);controls.update();}
$('enter').onclick=()=>{const [x,z]=game.state.player;walk(true,validPosition(x,z)?[x,1.72,z]:[4,1.72,22],game.state.heading);toast('按 J 查看委托 · 靠近金色目标按 F 互动。');};$('newshops').onclick=()=>{walk(false,[49,1.72,-66],0);toast('左侧慢衣服饰，前方数码体验，右侧餐饮区；点击画面后用 WASD 探索。');};$('walk').onclick=()=>walk();$('orbit').onclick=orbit;$('aerial').onclick=orbit;$('home').onclick=()=>walk(false);$('entrance').onclick=()=>{walk(false,[26,1.72,-14],0);toast('前方是自动门，按 W 可以走进大厅。');};
// Rest controls and the continuous clock are managed by game-ui/daylight.
$('people').onclick=()=>{people=!people;npcs.forEach(n=>n.root.visible=people);$('people').textContent='NPC：'+(people?'开':'关');};
$('ai').onclick=async()=>{if(!aiAvailable)await detectAI();aiEnabled=aiAvailable&&!aiEnabled;$('ai').textContent='AI：'+(aiEnabled?'开':aiAvailable?'关':'未连接');toast(aiEnabled?'Qwen 会理解聊天、选择目的地。步态和避让由本地程序执行。':'AI 已关闭，普通行走和目的地选择继续运行。');};
$('aiHelp').onclick=()=>{$('aiExplanation').hidden=!$('aiExplanation').hidden;};
$('send').onclick=()=>{const text=$('chat').value.trim();if(text&&selected){$('chat').value='';askAI(selected,text);}};$('chat').onkeydown=e=>{e.stopPropagation();if(e.code==='Enter')$('send').click();};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.code==='KeyJ'&&!e.repeat){gameUI.toggle();keys.clear();return;}if(e.code==='KeyF'&&!e.repeat){gameUI.interact();return;}if(e.code==='Escape'){gameUI.toggle(false);$('restPanel').hidden=true;}if(gameUI.isOpen()||!$('restPanel').hidden)return;keys.add(e.code);if(['KeyW','KeyA','KeyS','KeyD','Space'].includes(e.code))e.preventDefault();if(e.code==='KeyE'&&ready){const n=nearest();if(mode==='walk'&&n.root.position.distanceTo(camera.position)>6){toast('靠近路人到 6 米以内，再按 E。');return;}showNPC(n);n.talking=20;document.exitPointerLock();$('chat').focus();}});
document.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',()=>keys.clear());document.addEventListener('pointerlockchange',()=>{if(document.pointerLockElement!==canvas)keys.clear();});
canvas.addEventListener('mousemove',e=>{if(mode==='walk'&&(document.pointerLockElement===canvas||e.buttons===1)){yaw-=e.movementX*.0023;pitch=THREE.MathUtils.clamp(pitch-e.movementY*.0023,-1.4,1.4);camera.rotation.set(pitch,yaw,0);}});
const raycaster=new THREE.Raycaster();canvas.addEventListener('click',e=>{if(!ready)return;if(mode==='walk'){canvas.requestPointerLock().catch(()=>{});return;}raycaster.setFromCamera(new THREE.Vector2(e.clientX/innerWidth*2-1,1-e.clientY/innerHeight*2),camera);const hit=raycaster.intersectObjects(npcs.map(n=>n.root),true)[0];if(hit){const n=npcs.find(n=>{let o=hit.object;while(o){if(o===n.root)return true;o=o.parent;}return false;});if(n)showNPC(n);}});
function map(){const c=$('minimap').getContext('2d'),indoor=inside(camera.position)&&mode==='walk',scale=indoor?2.9:.9,cx=indoor?49:0,cz=indoor?-51:0,px=x=>135+(x-cx)*scale,pz=z=>100+(z-cz)*scale;c.clearRect(0,0,270,200);c.fillStyle=indoor?'#bac0aa':'#566158';if(indoor)c.fillRect(px(8),pz(-81),82*scale,60*scale);else{c.fillRect(0,pz(-13),270,26*scale);c.fillRect(px(-32.5),0,25*scale,200);}if(manifest)for(const o of manifest.colliders){c.fillStyle='#77897b';c.fillRect(px(o.x-o.w/2),pz(o.z-o.d/2),Math.max(1,o.w*scale),Math.max(1,o.d*scale));}c.font='10px Microsoft YaHei';c.fillStyle=indoor?'#20352a':'#eadab4';for(const key of indoor?['atrium','books','insideCafe','rest','toys']:['mall'])c.fillText(labels[key],px(nodes[key].x)-12,pz(nodes[key].z)-5);if(people)for(const n of npcs){c.fillStyle=n===selected?'#edb86e':'#e9eee4';c.beginPath();c.arc(px(n.root.position.x),pz(n.root.position.z),n===selected?3:1.8,0,Math.PI*2);c.fill();}gameUI.map(c,px,pz);c.fillStyle='#268bb4';c.beginPath();c.arc(px(camera.position.x),pz(camera.position.z),3.5,0,Math.PI*2);c.fill();$('signal').textContent=indoor?'1F · 星湾商场':green()?'行人绿灯':'行人等候';$('zone').textContent=indoor?'星湾商场 · 首层大厅':'虚构世界 · 星湾街区';}
function updateDoors(dt){const near=(mode==='walk'&&Math.hypot(camera.position.x-26,camera.position.z+21)<7)||people&&npcs.some(n=>Math.hypot(n.root.position.x-26,n.root.position.z+21)<6);doorAmount=THREE.MathUtils.damp(doorAmount,near?1:0,4,dt);doors.forEach(d=>d.ob.position.x=d.x+d.side*2*doorAmount);}
let uiTimer=0,frames=0,frameTime=0;
function tick(){requestAnimationFrame(tick);const rawDt=clock.getDelta(),dt=document.hidden?0:Math.min(rawDt,.10);if(!paused)simTime+=dt;if(mode==='orbit')controls.update();else if(document.activeElement.tagName!=='INPUT'&&!paused&&!gameUI.isOpen()&&$('restPanel').hidden){let x=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0),z=(keys.has('KeyS')?1:0)-(keys.has('KeyW')?1:0),l=Math.hypot(x,z)||1,s=(keys.has('ShiftLeft')?4.8:2.7)*dt;x/=l;z/=l;const dx=(x*Math.cos(yaw)+z*Math.sin(yaw))*s,dz=(-x*Math.sin(yaw)+z*Math.cos(yaw))*s;if(validPosition(camera.position.x+dx,camera.position.z))camera.position.x+=dx;if(validPosition(camera.position.x,camera.position.z+dz))camera.position.z+=dz;camera.position.y=1.72;}
 if(people&&!paused)for(const n of npcs)advanceNPC(n,dt);updateDoors(dt);
 if(ready){if(!paused&&document.body.classList.contains('exploring'))game.advance(dt,camera.position,mode==='walk');daylight.update(game.hour);gameUI.update(dt);if(game.saveTimer>10)saveGame();}
 if(ready&&aiEnabled&&people&&!aiBusy&&!paused&&simTime-lastAI>40){lastAI=simTime;const n=npcs[(++aiCursor)%npcs.length];if(!n.escort)askAI(n,'',true);}
 uiTimer+=dt;frames++;frameTime+=rawDt;if(uiTimer>.25){uiTimer=0;map();if(selected){$('npcstate').textContent=selected.state;showIntent(selected);}if(frameTime>2){$('diagnostic').textContent=Math.round(frames/frameTime)+' FPS';frames=0;frameTime=0;}}
 renderer.render(scene,camera);
}
window.addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();});
window.starbayDebug={getState:()=>({ready,mode,aiEnabled,aiBusy,modelName,simTime,doorAmount,inside:inside(camera.position),npcs:npcs.map(n=>({name:n.name,kind:n.spec.id,state:n.state,node:n.node,path:n.path,destination:n.destination,pendingGoal:n.pendingGoal,position:n.root.position.toArray(),yaw:n.root.rotation.y,phase:n.phase,walkBlend:n.walkBlend,feet:inspectFeet(n),intent:n.intent,aiDecisions:n.aiDecisions})),camera:camera.position.toArray(),triangles:renderer.info.render.triangles}),route,validPosition,walk:()=>walk(false),select:i=>showNPC(npcs[i]),approach:i=>{const n=npcs[i];walk(false,[n.root.position.x,1.72,n.root.position.z+3],0);showNPC(n);},pause:value=>paused=value,setTime:t=>simTime=t,teleport:(x,z)=>walk(false,[x,1.72,z],0),goal:(i,d)=>schedule(npcs[i],d,'验证','目的地验证'),step:seconds=>{for(let t=0;t<seconds;t+=1/60){simTime+=1/60;npcs.forEach(n=>advanceNPC(n,1/60));}},poseLineup:()=>{paused=true;for(let i=0;i<4;i++){npcs[i].root.position.set(31+i*1.5,.14,-32);npcs[i].root.rotation.y=0;npcs[i].walkBlend=0;posePerson(npcs[i],.1,0);}walk(false,[33.25,1.65,-26],0);},rigTest:(i,dist)=>posePerson(npcs[i],1/60,dist)};
window.starbayDebug.gaitAudit=()=>{
 paused=true;const reports=[];
 for(let i=0;i<4;i++){
  const n=npcs[i];n.root.position.set(i*2,.14,0);n.root.rotation.y=0;n.phase=0;n.walkBlend=1;posePerson(n,0,0);
  let previous=inspectFeet(n),drift=0,heightError=0;const d=n.spec.stepLength/.6/120;
  for(let frame=0;frame<120;frame++){
   n.root.position.z+=d;posePerson(n,1/60,d);const feet=inspectFeet(n);
   feet.forEach((f,k)=>{if(f.stance&&previous[k].stance&&f.phase>previous[k].phase){drift=Math.max(drift,Math.hypot(f.world[0]-previous[k].world[0],f.world[2]-previous[k].world[2]));heightError=Math.max(heightError,Math.abs(f.world[1]-(.14+n.spec.footHeight)));}});previous=feet;
  }
  for(let f=0;f<120;f++)posePerson(n,1/60,0);
  reports.push({kind:n.spec.id,maxStanceDrift:drift,maxStanceHeightError:heightError,idleBlend:n.walkBlend,idleFeet:inspectFeet(n)});
 }
 return reports;
};
window.starbayDebug.followUntil=(i,target,seconds)=>{
 paused=true;const n=npcs[i];let elapsed=0;
 while(elapsed<seconds){camera.position.copy(n.root.position).add(new THREE.Vector3(0,1.58,2.8));simTime+=1/30;npcs.forEach(p=>advanceNPC(p,1/30));elapsed+=1/30;if(n.node===target&&!n.path.length)return {arrived:true,elapsed,node:n.node,position:n.root.position.toArray(),intent:n.intent};}
 return {arrived:false,node:n.node,state:n.state,destination:n.destination,pending:n.pendingGoal};
};
window.starbayDebug.look=(heading,tilt=0)=>{yaw=heading;pitch=tilt;camera.rotation.set(pitch,yaw,0);};
window.starbayDebug.game={state:()=>JSON.parse(JSON.stringify(game.state)),places,templates,accept:id=>game.accept(id),track:id=>game.track(id),interact:id=>game.interact(id,camera.position,mode==='walk'),advance:seconds=>game.advance(seconds,camera.position,mode==='walk'),rest:h=>game.rest(h),save:saveGame,lighting:()=>daylight.inspect(),setHour:h=>{game.state.minutes=Math.floor(game.state.minutes/1440)*1440+h*60;daylight.update(h);},journal:()=>gameUI.toggle(true)};
load();tick();
