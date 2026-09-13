import * as THREE from 'three';
import {places,templates} from './game.js';
const $=id=>document.getElementById(id),t=id=>templates.find(q=>q.id===id),p=id=>places.find(q=>q.id===id);
export function createGameUI(game,scene,{position,walking,release,notify,save}){
 let opened=false,near=null,timer=0;
 const ring=new THREE.Mesh(new THREE.TorusGeometry(.85,.045,8,36),new THREE.MeshBasicMaterial({color:0xffd694,transparent:true,opacity:.85,depthTest:true}));ring.rotation.x=-Math.PI/2;scene.add(ring);
 const pin=new THREE.Mesh(new THREE.OctahedronGeometry(.22),new THREE.MeshBasicMaterial({color:0xffd694}));scene.add(pin);
 const trash=places.filter(p=>p.hidden).map(p=>{const ob=new THREE.Mesh(new THREE.BoxGeometry(.2,.25,.2),new THREE.MeshStandardMaterial({color:0xe9d5b3,roughness:.8}));ob.position.set(p.x,.25,p.z);scene.add(ob);return {id:p.id,ob};});
 function toggle(force){opened=force??!opened;$('journal').hidden=!opened;if(opened){release();renderJournal();}}
 function renderJournal(){
  const s=game.state;
  $('journalStats').textContent=`Lv.${1+Math.floor(s.xp/100)} · ${s.xp} 经验 · ${s.coins} 街区币 · ${s.discovered.length}/12 地点 · ${game.saveStatus}`;
  $('activeQuests').innerHTML=s.active.map(q=>{const task=t(q.id);return `<article class="quest"><span class="tag">${s.tracked===q.id?'正在追踪':'进行中'} · ${q.stage}/${task.steps.length}</span><h3>${task.title}</h3><p>${task.story}</p><ol>${task.steps.map((st,i)=>`<li class="${i<q.stage?'done':i===q.stage?'current':''}">${st.text} · ${p(st.place).name}${st.time==='night'?' · 夜间':st.time==='sunset'?' · 17:00—19:00':''}</li>`).join('')}</ol><button data-track="${q.id}">追踪此任务</button><small>奖励 ${task.reward} 币 / ${task.xp} 经验</small></article>`;}).join('')||'<p>暂时没有进行中的任务，去看看新的街区委托。</p>';
  $('questOffers').innerHTML=s.offers.map(id=>{const q=t(id);return `<article class="quest"><h3>${q.title}</h3><p>${q.story}</p><button data-accept="${id}" ${s.active.length>=3?'disabled':''}>接取委托</button><small>${q.reward} 币 / ${q.xp} 经验</small></article>`;}).join('')||'<p>街区暂时很安静。继续步行探索，新的委托会在稍后出现。</p>';
  $('inventory').textContent='任务物品：'+(game.inventory().join('、')||'背包空空，轻装出发。');
  $('discoveries').innerHTML=places.filter(q=>!q.hidden).map(q=>`<div class="place ${s.discovered.includes(q.id)?'found':''}"><strong>${s.discovered.includes(q.id)?'◆':'◇'} ${q.name}</strong><span>${q.desc}</span></div>`).join('');
  $('completedQuests').textContent=s.completed.slice(0,8).map(q=>`第 ${q.day} 天 · ${t(q.id).title}`).join(' / ')||'你的街区故事才刚开始。';
 }
 $('journalButton').onclick=()=>toggle();$('closeJournal').onclick=()=>toggle(false);
 $('journal').onclick=e=>{const accept=e.target.dataset.accept,track=e.target.dataset.track;if(accept){game.accept(accept);save();renderJournal();}if(track){game.track(track);save();renderJournal();}};
 $('saveGame').onclick=()=>{save();notify(game.saveStatus);if(opened)renderJournal();};
 $('time').onclick=()=>{release();$('restPanel').hidden=!$('restPanel').hidden;};$('closeRest').onclick=()=>$('restPanel').hidden=true;
 $('restPanel').onclick=e=>{if(e.target.dataset.hour){game.rest(Number(e.target.dataset.hour));$('restPanel').hidden=true;save();}};
 $('residents').onclick=()=>{release();document.body.classList.toggle('npc-open');};
 function interact(){if(opened)return;if(!near){notify('靠近导览点或当前任务目标，到 3 米内按 F。');return;}const result=game.interact(near.id,position(),walking());notify(result.reason);save();}
 function update(dt){
  timer+=dt;const q=game.state.active.find(q=>q.id===game.state.tracked),goal=q?p(game.objective(q).place):null;
  ring.visible=pin.visible=!!goal;if(goal){ring.position.set(goal.x,.16,goal.z);pin.position.set(goal.x,2.5+Math.sin(timer*2)*.13,goal.z);pin.rotation.y+=dt;}
  const clean=game.state.active.find(q=>q.id==='cleanup');trash.forEach(({id,ob},i)=>ob.visible=!!clean&&i>=clean.stage);
  near=null;if(walking()){const candidates=places.filter(x=>!x.hidden||game.state.active.some(q=>game.objective(q).place===x.id));candidates.sort((a,b)=>Math.hypot(a.x-position().x,a.z-position().z)-Math.hypot(b.x-position().x,b.z-position().z));if(candidates[0]&&Math.hypot(candidates[0].x-position().x,candidates[0].z-position().z)<=3.2)near=candidates[0];}
  $('interaction').hidden=!near||opened;const nq=near&&[...game.state.active].sort((a,b)=>(b.id===game.state.tracked)-(a.id===game.state.tracked)).find(q=>game.objective(q).place===near.id);if(near)$('interaction').textContent='F · '+(nq?game.objective(nq).text:'看看'+near.name);
  $('clock').textContent=game.clockText();$('wallet').textContent=`Lv.${1+Math.floor(game.state.xp/100)} · ${game.state.coins} 币 · ${game.state.discovered.length}/12 地点`;
  $('questTitle').textContent=q?t(q.id).title:'自由探索';
  $('questObjective').textContent=q?game.objective(q).text+' · '+goal.name:'沿街走走，新的委托会不时出现。';
  if(goal){const dx=goal.x-position().x,dz=goal.z-position().z,dir=(dz< -5?'北':dz>5?'南':'')+(dx>5?'东':dx< -5?'西':'');$('questDistance').textContent=`${walking()?Math.round(Math.hypot(dx,dz))+' 米 · '+dir+'方 · ':''}${q.stage+1}/${t(q.id).steps.length} 步${game.timeAllowed(game.objective(q).time)?'':' · 需要等待合适时间'}`;}else $('questDistance').textContent='按 J 打开任务与探索手册';
  $('offerCount').textContent=game.state.offers.length+' 条待接委托';
 }
 function map(c,px,pz){for(const poi of places.filter(p=>!p.hidden)){c.strokeStyle=game.state.discovered.includes(poi.id)?'#d9bc86':'#7b9689';c.strokeRect(px(poi.x)-2,pz(poi.z)-2,4,4);}const q=game.state.active.find(q=>q.id===game.state.tracked);if(q){const poi=p(game.objective(q).place);c.strokeStyle='#ffd483';c.lineWidth=2;c.beginPath();c.arc(px(poi.x),pz(poi.z),5,0,Math.PI*2);c.stroke();c.lineWidth=1;}}
 return {update,toggle,interact,map,isOpen:()=>opened};
}
