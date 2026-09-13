// Local, deterministic gameplay. The language model is optional for conversations.
export const SAVE_KEY='starbay-open-world-v3';
export const places=[
 {id:'mall',name:'星湾入口',x:26,z:-16,desc:'穿过自动门，就能走进首层大厅。'},
 {id:'service',name:'居民服务台',x:36,z:-26,desc:'街区委托与包裹的交接地点。'},
 {id:'books',name:'城市书屋',x:73,z:-45,desc:'书架之间，留一段慢下来的时间。'},
 {id:'insideCafe',name:'街角咖啡',x:20,z:-44,desc:'大厅中的开放咖啡区。'},
 {id:'rest',name:'中庭休息区',x:49,z:-63,desc:'给走累的人留一张椅子。'},
 {id:'toys',name:'童趣乐园',x:72,z:-60,desc:'小朋友的彩色角落。'},
 {id:'market',name:'晚风小集',x:-105,z:25,desc:'街边的小摊，入夜后亮起暖灯。'},
 {id:'courier',name:'街区驿站',x:-65,z:23,desc:'替邻居捎一件包裹。'},
 {id:'park',name:'口袋公园',x:9,z:40,desc:'住宅楼前的一小片绿意。'},
 {id:'art',name:'光环广场',x:94,z:36,desc:'小型公共雕塑与开放的休憩空间。'},
 {id:'overlook',name:'落日长廊',x:103,z:-32,desc:'在星湾东侧看天色慢慢变化。'},
 {id:'garden',name:'街角花园',x:17,z:25,desc:'树影、长椅和下班后的散步。'},
 {id:'leaf1',name:'公园纸杯',x:7,z:36,hidden:true},
 {id:'leaf2',name:'公园纸袋',x:12,z:39,hidden:true},
 {id:'leaf3',name:'公园空瓶',x:7,z:44,hidden:true}
];
const step=(place,text,extra={})=>({place,text,...extra});
export const templates=[
 {id:'welcome',title:'初来街区',story:'从星湾入口开始，去服务台报到，再找找城市书屋。',reward:30,xp:50,steps:[step('mall','查看入口导览'),step('service','领取街区手册'),step('books','盖下第一枚书屋印章')]},
 {id:'parcel',title:'顺路捎个包裹',story:'驿站有一份公共活动物料，需要送到商场服务台。',reward:35,xp:40,steps:[step('courier','领取活动包裹',{item:'活动包裹'}),step('service','交付活动包裹')]},
 {id:'reading',title:'给休息区送本书',story:'城市书屋想把一本读物放到休息区的共享书角。',reward:25,xp:35,steps:[step('books','取一本共享读物',{item:'共享读物'}),step('rest','放好共享读物')]},
 {id:'coffee',title:'一杯咖啡的散步',story:'取一杯咖啡，沿街走到星湾东侧的落日长廊。',reward:30,xp:40,steps:[step('insideCafe','领取外带咖啡',{item:'外带咖啡'}),step('overlook','在长廊享用咖啡')]},
 {id:'cleanup',title:'让公园干净一点',story:'口袋公园有三件散落的垃圾，按顺序把它们收起来。',reward:40,xp:50,steps:[step('leaf1','捡起纸杯'),step('leaf2','捡起纸袋'),step('leaf3','捡起空瓶')]},
 {id:'night',title:'夜间亮灯巡查',story:'天黑后，确认小集、花园和光环广场的照明。可用「休息」等到夜晚。',reward:50,xp:60,steps:[step('market','检查小集灯光',{time:'night'}),step('garden','检查花园路灯',{time:'night'}),step('art','检查广场照明',{time:'night'})]},
 {id:'sunset',title:'收集一场落日',story:'17:00—19:00，到东侧长廊记录落日。可用「休息」等到 17:30。',reward:40,xp:45,steps:[step('overlook','记录落日纪念',{time:'sunset',item:'落日纪念'})]},
 {id:'stamps',title:'街区漫游印章',story:'去晚风小集、口袋公园和光环广场，认识这片小小的世界。',reward:45,xp:55,steps:[step('market','收集小集印章'),step('park','收集公园印章'),step('art','收集光环印章')]}
];
const template=id=>templates.find(t=>t.id===id), place=id=>places.find(p=>p.id===id);
const fresh=()=>({version:3,minutes:16*60+30,elapsed:0,coins:0,xp:0,discovered:[],active:[{id:'welcome',stage:0}],offers:['parcel','stamps'],completed:[],nextOffer:180,offerCursor:2,tracked:'welcome',player:[4,22],heading:-.34,walking:false});
function validSave(s){
 const num=(v,min,max)=>Number.isFinite(v)&&v>=min&&v<=max;
 return s?.version===3&&num(s.minutes,0,1e9)&&num(s.elapsed,0,1e9)&&num(s.coins,0,1e8)&&num(s.xp,0,1e8)&&num(s.nextOffer,0,1e9)&&Number.isInteger(s.offerCursor)&&s.offerCursor>=0&&s.offerCursor<1e8&&
 Array.isArray(s.player)&&s.player.length===2&&s.player.every(v=>num(v,-135,135))&&num(s.heading,-1e9,1e9)&&typeof s.walking==='boolean'&&
 Array.isArray(s.discovered)&&s.discovered.length<=places.length&&s.discovered.every(id=>place(id)&&!place(id).hidden)&&new Set(s.discovered).size===s.discovered.length&&
 Array.isArray(s.active)&&s.active.length<=3&&s.active.every(q=>template(q.id)&&Number.isInteger(q.stage)&&q.stage>=0&&q.stage<template(q.id).steps.length)&&new Set(s.active.map(q=>q.id)).size===s.active.length&&
 Array.isArray(s.offers)&&s.offers.length<=3&&s.offers.every(id=>template(id)&&id!=='welcome'&&!s.active.some(q=>q.id===id))&&new Set(s.offers).size===s.offers.length&&
 Array.isArray(s.completed)&&s.completed.length<=30&&s.completed.every(q=>template(q.id)&&num(q.day,1,1e9))&&(s.tracked===null||s.active.some(q=>q.id===s.tracked));
}
export class Game{
 constructor(storage,notify=()=>{}){this.storage=storage;this.notify=notify;this.state=fresh();this.resumed=false;this.saveStatus='等待开始';try{const raw=storage.getItem(SAVE_KEY)||storage.getItem('wanda-open-world-v3');if(raw){const parsed=JSON.parse(raw);if(validSave(parsed)){this.state=parsed;this.resumed=true;}else notify('旧存档无法读取，已开始新的旅程。');}}catch{notify('存档读取失败，本次可以继续游玩。');}this.saveTimer=0;}
 get hour(){return (this.state.minutes%1440)/60;}
 get day(){return Math.floor(this.state.minutes/1440)+1;}
 timeAllowed(kind){return !kind||(kind==='night'?(this.hour>=19||this.hour<6):this.hour>=17&&this.hour<19);}
 advance(dt,p,walking){if(!Number.isFinite(dt)||dt<0)return;const s=this.state;s.minutes+=dt*1.2; // Twenty real minutes per day, only while playing.
  if(walking){s.elapsed+=dt;for(const poi of places.filter(p=>!p.hidden)){if(!s.discovered.includes(poi.id)&&Math.hypot(p.x-poi.x,p.z-poi.z)<8){s.discovered.push(poi.id);s.xp+=10;this.notify('发现 '+poi.name+' · +10 探索经验');}}
   if(s.elapsed>=s.nextOffer&&s.offers.length<3){const pool=templates.filter(t=>t.id!=='welcome');for(let k=0;k<pool.length;k++){const id=pool[s.offerCursor++%pool.length].id;if(!s.offers.includes(id)&&!s.active.some(q=>q.id===id)){s.offers.push(id);this.notify('新的街区委托：'+template(id).title+' · 按 J 查看');break;}}s.nextOffer=s.elapsed+180;}}
  this.saveTimer+=dt;
 }
 accept(id){const s=this.state;if(s.active.length>=3||!s.offers.includes(id))return false;s.offers=s.offers.filter(x=>x!==id);s.active.push({id,stage:0});s.tracked=id;this.notify('已接取：'+template(id).title);return true;}
 track(id){if(this.state.active.some(q=>q.id===id))this.state.tracked=id;}
 objective(q){return template(q.id).steps[q.stage];}
 interact(id,p,walking){const poi=place(id);if(!walking||!poi||Math.hypot(p.x-poi.x,p.z-poi.z)>3.2)return {ok:false,reason:'请步行靠近目标，到 3 米内按 F。'};
  const ordered=[...this.state.active].sort((a,b)=>(b.id===this.state.tracked)-(a.id===this.state.tracked));const q=ordered.find(q=>this.objective(q).place===id);
  if(!q)return {ok:true,reason:poi.desc||'这个角落已经收拾好了。'};
  const st=this.objective(q);if(!this.timeAllowed(st.time))return {ok:false,reason:st.time==='night'?'请在 19:00—06:00 进行巡查。':'请在 17:00—19:00 记录落日。'};
  q.stage++;const t=template(q.id);if(q.stage===t.steps.length){this.state.coins+=t.reward;this.state.xp+=t.xp;this.state.completed.unshift({id:q.id,day:this.day});this.state.completed=this.state.completed.slice(0,30);this.state.active=this.state.active.filter(x=>x!==q);if(this.state.tracked===q.id)this.state.tracked=this.state.active[0]?.id||null;return {ok:true,completed:q.id,reason:`完成「${t.title}」 · +${t.reward} 街区币 / +${t.xp} 经验`};}
  return {ok:true,reason:'已完成：'+st.text+'。下一站：'+place(this.objective(q).place).name};
 }
 rest(hour){if(![6,12,17.5,20].includes(hour))return;let delta=(hour*60-this.state.minutes%1440+1440)%1440;if(delta<1)delta=1440;this.state.minutes+=delta;this.notify('休息结束，时间来到 '+this.clockText());}
 clockText(){const h=Math.floor(this.hour),m=Math.floor(this.state.minutes%60);return `第 ${this.day} 天 · ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;}
 inventory(){return this.state.active.flatMap(q=>template(q.id).steps.slice(0,q.stage).filter(s=>s.item).map(s=>s.item));}
 save(p,heading,walking){this.state.player=[p.x,p.z];this.state.heading=heading;this.state.walking=walking;try{this.storage.setItem(SAVE_KEY,JSON.stringify(this.state));this.saveStatus='已保存到本机';this.saveTimer=0;return true;}catch{this.saveStatus='保存失败，请检查浏览器存储';return false;}}
}
