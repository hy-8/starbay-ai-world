from playwright.sync_api import sync_playwright
from pathlib import Path
import json, math
ROOT=Path(__file__).parent/'第四版回归验证';ROOT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,args=['--enable-webgl','--ignore-gpu-blocklist','--use-angle=d3d11'])
    page=b.new_page(viewport={'width':1600,'height':1000});page.route('**/api/ai/status',lambda route:route.fulfill(json={'available':False}));errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/?v=5',wait_until='networkidle')
    page.wait_for_function('window.starbayDebug?.getState().ready',timeout=120000)
    page.evaluate('starbayDebug.pause(true)')
    page.screenshot(path=str(ROOT/'第三版开放世界.png'))
    # All graph segments must clear old and new physical obstacles.
    blocked=page.evaluate("""async()=>{const {nodeData,edges}=await import('./navigation.js');let out=[];for(const [a,b] of edges)for(let i=0;i<=150;i++){let t=i/150,x=nodeData[a][0]*(1-t)+nodeData[b][0]*t,z=nodeData[a][1]*(1-t)+nodeData[b][1]*t;if(!starbayDebug.validPosition(x,z,.28)){out.push([a,b,x,z]);break;}}return out;}""")
    assert not blocked,blocked
    # Every interaction is reachable from the starter via a conservative 0.5 m grid.
    reachability=page.evaluate("""()=>{const d=starbayDebug,unit=.5,seen=new Set(),queue=[[8,44]],key=(x,z)=>x+','+z;seen.add(key(8,44));let at=0;while(at<queue.length){const [x,z]=queue[at++];for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){const a=x+dx,c=z+dz,k=key(a,c);if(!seen.has(k)&&d.validPosition(a*unit,c*unit,.28)){seen.add(k);queue.push([a,c]);}}}return d.game.places.map(p=>({id:p.id,valid:d.validPosition(p.x,p.z),reachable:seen.has(key(Math.round(p.x/unit),Math.round(p.z/unit)))}));}""")
    assert all(x['valid'] and x['reachable'] for x in reachability),reachability
    # Test independent game states: transactions, temporal gates, cooldowns and persistence.
    engine=page.evaluate("""async()=>{const {Game,SAVE_KEY}=await import('./game.js');let raw=null;const storage={getItem:()=>raw,setItem:(k,v)=>raw=v},g=new Game(storage);const check=(c,m)=>{if(!c)throw Error(m)};let p={x:26,z:-16};
    check(!g.interact('mall',{x:0,z:0},true).ok,'remote completion');check(!g.interact('mall',p,false).ok,'orbit completion');
    for(const [id,x,z] of [['mall',26,-16],['service',36,-26],['books',73,-45]])check(g.interact(id,{x,z},true).ok,'welcome step');
    check(g.state.coins===30&&g.state.completed.length===1,'reward missing');g.interact('books',{x:73,z:-45},true);check(g.state.coins===30,'double reward');
    check(g.accept('parcel'),'accept');check(!g.accept('parcel'),'double accept');g.interact('courier',{x:-65,z:23},true);check(g.inventory().includes('活动包裹'),'inventory');
    g.save({x:-65,z:23},.3,true);const loaded=new Game(storage);check(loaded.resumed&&loaded.state.active.find(q=>q.id==='parcel').stage===1,'save stage');loaded.interact('service',{x:36,z:-26},true);check(loaded.state.coins===65&&!loaded.inventory().length,'delivery');
    const count=g.state.offers.length;g.advance(179,p,true);check(g.state.offers.length===count,'early offer');g.advance(1,p,true);check(g.state.offers.length===count+1,'no offer');g.advance(1,p,true);check(g.state.offers.length===count+1,'offer spam');
    const night=new Game({getItem:()=>null,setItem:()=>{}});night.state.offers=['night','sunset','reading'];night.accept('night');night.accept('sunset');check(!night.accept('reading'),'active limit');check(!night.interact('market',{x:-105,z:25},true).ok,'daytime night quest');night.rest(20);check(night.interact('market',{x:-105,z:25},true).ok,'night quest');check(!night.interact('overlook',{x:103,z:-32},true).ok,'night sunset');night.rest(17.5);check(night.interact('overlook',{x:103,z:-32},true).completed==='sunset','sunset quest');const day=night.day;night.rest(6);check(night.day===day+1,'rollover');
    const corrupt=new Game({getItem:()=>'{broken',setItem:()=>{}});check(!corrupt.resumed,'corrupt save');raw=JSON.stringify({...g.state,coins:-2});check(!new Game(storage).resumed,'invalid save');const denied=new Game({getItem:()=>null,setItem:()=>{throw Error('blocked')}});check(!denied.save(p,0,true),'storage failure');
    return {rewardOnce:true,rangeEnforced:true,inventoryAndReload:true,cooldown:true,timeGates:true,rollover:true,saveValidation:true};}""")
    # Exercise actual F input and the journal accept button.
    page.evaluate('starbayDebug.teleport(26,-16)');page.wait_for_timeout(250);page.keyboard.press('f')
    assert page.evaluate('starbayDebug.game.state().active[0].stage')==1
    page.keyboard.press('j');page.click('[data-accept="parcel"]')
    assert page.evaluate('starbayDebug.game.state().active.some(q=>q.id==="parcel")')
    page.screenshot(path=str(ROOT/'街区任务手册.png'));page.click('#closeJournal')
    page.evaluate('starbayDebug.teleport(-65,23)');page.wait_for_timeout(250);page.keyboard.press('f')
    assert page.evaluate('starbayDebug.game.state().active.find(q=>q.id==="parcel").stage')==1
    page.evaluate('starbayDebug.game.save()');saved=page.evaluate('starbayDebug.game.state()');page.reload(wait_until='networkidle');page.wait_for_function('starbayDebug.getState().ready',timeout=120000)
    restored=page.evaluate('starbayDebug.game.state()');assert restored['player']==saved['player'] and restored['coins']==saved['coins'] and restored['active']==saved['active']
    page.evaluate("document.getElementById('enter').click()");page.wait_for_timeout(250);assert math.dist(page.evaluate('starbayDebug.getState().camera'),[-65,1.72,23])<.01
    page.evaluate('starbayDebug.pause(true)')
    # Time changes must visibly affect light, and screenshots record each phase.
    lighting={}
    for hour,label in [(6.5,'清晨'),(12,'白昼'),(17.5,'落日'),(21,'夜晚')]:
        page.evaluate(f'starbayDebug.game.setHour({hour});starbayDebug.teleport(94,25)')
        page.wait_for_timeout(350);lighting[label]=page.evaluate('starbayDebug.game.lighting()')
        page.screenshot(path=str(ROOT/f'街区{label}.png'))
    assert lighting['夜晚']['streetIntensity']>50 and lighting['夜晚']['starsOpacity']>.7
    assert lighting['白昼']['streetIntensity']==0 and lighting['白昼']['sunIntensity']>2
    page.evaluate("starbayDebug.teleport(-105,23);starbayDebug.game.setHour(20)")
    # Point the walk camera towards the market front, for a useful exterior view.
    page.evaluate("document.getElementById('world').dispatchEvent(new MouseEvent('mousemove',{movementX:1366,buttons:1,bubbles:true}))")
    page.wait_for_timeout(250);page.screenshot(path=str(ROOT/'晚风小集夜景.png'))
    # Existing door, mall and gait behavior remain valid.
    page.evaluate('starbayDebug.teleport(26,-14);starbayDebug.pause(false)');page.keyboard.down('w');page.wait_for_function('starbayDebug.getState().camera[2]<-29',timeout=25000);page.keyboard.up('w')
    assert page.evaluate('starbayDebug.getState().inside')
    page.screenshot(path=str(ROOT/'第三版商场室内.png'))
    page.evaluate('starbayDebug.pause(true)');before=page.evaluate('starbayDebug.getState()');page.evaluate('starbayDebug.step(180)');after=page.evaluate('starbayDebug.getState()')
    assert all(page.evaluate('([x,y,z])=>starbayDebug.validPosition(x,z,.19)',n['position']) for n in after['npcs'])
    moved=sum(math.dist(a['position'],c['position'])>3 for a,c in zip(before['npcs'],after['npcs']));assert moved>=10,moved
    gait=page.evaluate('starbayDebug.gaitAudit()');assert all(x['maxStanceDrift']<.001 and x['maxStanceHeightError']<.001 for x in gait)
    report={'browserErrors':errors,'blockedRoutes':blocked,'reachability':reachability,'gameplay':engine,'saveReload':True,'keyboardInteraction':True,'lighting':lighting,'movedNPCs':moved,'gait':gait}
    (ROOT/'verification_v3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert not errors,errors
    print(json.dumps(report,ensure_ascii=False));b.close()
