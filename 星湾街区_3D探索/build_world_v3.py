"""Invented public spaces within the existing neighborhood; Blender coordinates."""
import math
def build_world(box,rod,ball,text,collider,mat,tree):
    mat('worldTeal',(.045,.22,.20));mat('worldClay',(.57,.24,.12));mat('worldGlow',(1,.68,.30),.4,0,3)
    # Three walk-up stalls, all outside the existing sidewalk routes.
    for i,x in enumerate([-115,-105,-95]):
        y=-30
        box('market platform',(x,y,.2),(6,4,.2),'interiorWood')
        box('market counter',(x,y+1,.72),(4.5,.7,1.15),'worldTeal');collider(x,y,5,3)
        for dx in [-2.5,2.5]:rod('market upright',(x+dx,y-1.5,.2),(x+dx,y-1.5,3.6),.07,'silver')
        box('market awning',(x,y,3.5),(5.8,4.1,.15),'worldClay' if i%2 else 'cream')
        for dx in [-2,-1,0,1,2]:ball('market lantern',(x+dx,y+1.6,2.85),(.16,.16,.22),'worldGlow')
        for dx in [-1.6,-.8,0,.8,1.6]:box('market goods',(x+dx,y+.9,1.45),(.45,.4,.3),['yellow','red','greenSign'][i])
        text('market name',['花与果','晚风小集','手作铺'][i],(x,y+1.9,2.55),.38,'ivory',(math.pi/2,0,math.pi))
    box('courier kiosk',(-68,-29,1.4),(4,2.6,2.6),'worldTeal');collider(-68,-29,4,2.6)
    box('courier canopy',(-68,-28,2.9),(5,4,.16),'cream')
    text('courier sign','街 区 驿 站',(-68,-27.6,2.15),.35,'white',(math.pi/2,0,math.pi))
    for x in [-69,-68,-67]:box('parcel',(x,-27,.5),(.6,.6,.75),'gold')
    # Pocket garden with a clear central walking path and places to sit.
    for x in [0,18]:
        box('pocket planter',(x,-44,.35),(4,9,.5),'ivory');collider(x,-44,4,9)
        box('pocket soil',(x,-44,.64),(3.8,8.8,.1),'soil');tree(x,-45,.7)
        for y in [-41,-43,-47]:ball('pocket shrubs',(x,y,.95),(1.4,1,.45),'leaf2')
    for x,y in [(3,-48),(13,-48)]:
        box('park seat',(x,y,.6),(3,.65,.16),'interiorWood');box('park seat back',(x,y-.3,1),(3,.15,.65),'interiorWood');collider(x,y,3,.85)
    box('park sign',(4,-35,1.1),(1.8,.18,1.8),'worldTeal');text('park words','口袋公园\n慢一点  看看树',(4,-34.85,1.45),.22,'ivory',(math.pi/2,0,math.pi))
    # Small sculpture court. Sculptural ring, low planters and a walkable open front.
    box('art paving',(99,-39,.135),(19,15,.05),'ivory')
    box('art plinth',(101,-40,.42),(4,3,.65),'stone');collider(101,-40,4,3)
    for i in range(48):
        a=i*math.tau/48;b=(i+1)*math.tau/48
        rod('light ring',(101+math.cos(a)*2,-40,3.4+math.sin(a)*2),(101+math.cos(b)*2,-40,3.4+math.sin(b)*2),.14,'gold',8)
        rod('ring glow',(101+math.cos(a)*1.82,-39.93,3.4+math.sin(a)*1.82),(101+math.cos(b)*1.82,-39.93,3.4+math.sin(b)*1.82),.035,'worldGlow',6)
    text('sculpture caption','光 环 广 场',(101,-38.4,.55),.28,'white',(math.pi/2,0,math.pi))
    for x in [91,107]:
        box('art planter',(x,-43,.45),(2,4,.6),'worldTeal');collider(x,-43,2,4)
        ball('art shrub',(x,-43,1),(1,1.7,.6),'leaf2')
    # The east-side lane stays open beside the mall.
    box('promenade paving',(103,32,.135),(10,20,.05),'ivory')
    for y in range(24,43,3):
        rod('promenade rail',(108,y,.2),(108,y,1.2),.055,'silver')
    rod('promenade handrail',(108,24,1.2),(108,42,1.2),.065,'silver');collider(108,33,.2,18)
    box('promenade bench',(105,38,.6),(3,.65,.15),'interiorWood');collider(105,38,3,.85)
    text('promenade sign','落日长廊 · SUNSET WALK',(104,25.5,2),.32,'worldTeal')
    # Physical guideposts mark each extension; warm lights are animated in the browser.
    for x,y in [(-103,-22),(-65,-22),(7,-34),(94,-34),(103,29)]:
        rod('district light pole',(x,y,.2),(x,y,5.6),.065,'dark')
        ball('district light',(x,y,5.6),(.24,.24,.34),'worldGlow')
    text('extension note','街区生活 / 扩展设计',(-105,-27.7,3.55),.30,'white',(math.pi/2,0,math.pi))
