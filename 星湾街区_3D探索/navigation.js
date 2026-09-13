export const nodeData={nw:[-39,-19],ne:[0,-19],sw:[-39,19],se:[0,19],mall:[26,-16],east:[77,-17],cafe:[-64,-25],west:[-107,-19],northwest:[-39,-72],southwest:[-65,20],garden:[17,25],bikes:[62,21],foyer:[26,-26],lobby:[35,-35],atrium:[49,-45],service:[36,-26],insideCafe:[20,-44],books:[73,-45],toys:[72,-60],rest:[49,-63],market:[-105,25],courier:[-65,23],park:[9,40],art:[94,36],southEast:[94,21],eastLane:[103,-18],overlook:[103,-32]};
export const labels={mall:'星湾入口',cafe:'沿街店铺',garden:'街角花园',bikes:'共享单车点',west:'西侧人行道',southwest:'西南街角',northwest:'西北街角',east:'东侧街道',atrium:'商场中庭',service:'服务台',insideCafe:'室内咖啡区',books:'城市书屋',toys:'童趣乐园',rest:'室内休息区',market:'晚风小集',courier:'街区驿站',park:'口袋公园',art:'光环广场',overlook:'落日长廊'};
export const destinations=Object.keys(labels);
export const edges=[['nw','ne',1],['sw','se',1],['nw','sw',1],['ne','se',1],['ne','mall'],['mall','east'],['nw','cafe'],['cafe','west'],['nw','northwest'],['sw','southwest'],['se','garden'],['garden','bikes'],['mall','foyer'],['foyer','lobby'],['foyer','service'],['lobby','atrium'],['lobby','insideCafe'],['atrium','books'],['atrium','rest'],['books','toys'],['rest','toys'],['southwest','courier'],['courier','market'],['garden','park'],['bikes','southEast'],['southEast','art'],['east','eastLane'],['eastLane','overlook']];
export const adjacency=Object.fromEntries(Object.keys(nodeData).map(k=>[k,[]]));
for(const [a,b,cross] of edges){adjacency[a].push({to:b,cross:!!cross});adjacency[b].push({to:a,cross:!!cross});}
export function route(from,to){
 if(!nodeData[from]||!nodeData[to])return [];
 const dist=Object.fromEntries(Object.keys(nodeData).map(k=>[k,Infinity])),prev={},queue=new Set(Object.keys(nodeData));dist[from]=0;
 while(queue.size){const u=[...queue].reduce((a,b)=>dist[a]<dist[b]?a:b);queue.delete(u);if(u===to)break;for(const {to:v} of adjacency[u]){const a=nodeData[u],b=nodeData[v],d=dist[u]+Math.hypot(a[0]-b[0],a[1]-b[1]);if(d<dist[v]){dist[v]=d;prev[v]=u;}}}
 const result=[to];while(result[0]!==from&&prev[result[0]])result.unshift(prev[result[0]]);return result[0]===from?result:[];
}
