from pathlib import Path
from playwright.sync_api import sync_playwright
import json
P=Path(__file__).parent
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,args=['--enable-webgl','--ignore-gpu-blocklist','--use-angle=d3d11'])
 page=b.new_page(viewport={'width':1600,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 # Isolated art-review camera, no modification of the player's browser or save.
 source=(P/'app.js').read_text(encoding='utf-8')+'''\nwindow.artShot=(a,target,lineup=false)=>{paused=true;aiEnabled=false;mode='walk';controls.enabled=false;document.body.classList.add('exploring');if(lineup){for(let i=0;i<4;i++){npcs[i].root.position.set(31+i*1.35,.14,-32);npcs[i].root.rotation.y=0;posePerson(npcs[i],.5,0);}}camera.position.set(...a);camera.lookAt(...target);renderer.render(scene,camera);return {drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};};'''
 page.route('**/app.js*',lambda route:route.fulfill(body=source,content_type='application/javascript'))
 page.route('**/api/ai/status',lambda route:route.fulfill(json={'available':False}))
 page.goto('http://127.0.0.1:8765/?v=5',wait_until='networkidle');page.wait_for_function('starbayDebug.getState().ready',timeout=120000)
 page.evaluate('starbayDebug.pause(true);starbayDebug.game.setHour(12)')
 blocked=page.evaluate("""async()=>{const {nodeData,edges}=await import('./navigation.js');let out=[];for(const [a,b] of edges)for(let i=0;i<=150;i++){let t=i/150,x=nodeData[a][0]*(1-t)+nodeData[b][0]*t,z=nodeData[a][1]*(1-t)+nodeData[b][1]*t;if(!starbayDebug.validPosition(x,z,.28)){out.push([a,b,x,z]);break;}}return out;}""")
 gait=page.evaluate('starbayDebug.gaitAudit()')
 page.add_style_tag(content='body>*:not(#world):not(script){display:none!important}')
 shots=[('第四版_四类都市居民',[33.02,1.3,-28.2],[33.02,1.04,-32],True),('第四版_成年男性近景',[31,1.62,-30.92],[31,1.58,-32],True),('第四版_成年女性近景',[32.35,1.5,-30.92],[32.35,1.49,-32],True),('第四版_商场全景',[46,2.1,-40],[49,1.9,-74],False),('第四版_慢衣服饰店',[26,1.72,-65],[25,1.7,-76],False),('第四版_数码体验区',[57,1.72,-68],[57,1.5,-76],False),('第四版_餐饮区',[79,1.72,-69],[79,1.6,-77],False),('第四版_咖啡陈设',[19,1.72,-43],[14,1.5,-44],False)]
 stats=[]
 for name,a,target,lineup in shots:
  stat=page.evaluate('([a,t,l])=>artShot(a,t,l)',[a,target,lineup]);page.wait_for_timeout(500);page.screenshot(path=str(P/(name+'.png')));stats.append({'shot':name,**stat})
 report={'blockedRoutes':blocked,'gait':gait,'errors':errors,'shots':stats}
 (P/'verification_art_v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
 assert not blocked,blocked
 assert all(r['maxStanceDrift']<.006 and r['maxStanceHeightError']<.004 for r in gait),gait
 assert not errors,errors
 b.close()
