"""Original city-mall fit-out. All geometry remains editable and material-batched."""
import math,random

def build_interior(box,rod,ball,text,collider,mat):
 r=random.Random(404)
 for name,color in [('v4Oak',(.43,.28,.15)),('v4Ivory',(.83,.79,.68)),('v4Teal',(.035,.23,.23)),('v4Clay',(.62,.25,.15)),('v4Ink',(.035,.055,.07)),('v4Pink',(.67,.36,.34)),('v4Blue',(.17,.32,.48)),('v4Paper',(.90,.86,.76))]:mat(name,color)
 mat('v4Light',(1,.87,.65),.45,0,1.6);mat('v4Screen',(.06,.38,.47),.3,0,.8)
 def solid(n,p,d,m):box(n,p,d,m);collider(p[0],p[1],d[0],d[1])
 def chair(x,y,angle=0,color='v4Teal'):
  # The whole chair footprint is solid, including the back and legs.
  box('v4 upholstered seat',(x,y,.52),(.58,.58,.16),color,angle)
  dx,dy=-math.sin(angle)*.25,math.cos(angle)*.25
  box('v4 chair back',(x+dx,y+dy,.89),(.59,.12,.68),color,angle)
  for a in [-.22,.22]:
   for b in [-.22,.22]:rod('v4 chair leg',(x+a,y+b,.16),(x+a,y+b,.49),.024,'v4Ink')
  collider(x,y,.72,.72)
 def plant(x,y,scale=1):
  solid('v4 ceramic pot',(x,y,.39*scale),(.60*scale,.60*scale,.65*scale),'v4Ivory')
  for i in range(8):
   a=i*math.tau/8;xx=x+math.cos(a)*.28*scale;yy=y+math.sin(a)*.28*scale
   rod('v4 stems',(x,y,.6*scale),(xx,yy,1.45*scale),.018*scale,'leaf2')
   ball('v4 broad leaves',(xx,yy,1.3*scale),(.22*scale,.16*scale,.40*scale),'leaf2',12,8)
 def cup(x,y,z):
  rod('v4 ceramic cup',(x,y,z),(x,y,z+.17),.085,'v4Paper',16)
  rod('v4 coffee',(x,y,z+.173),(x,y,z+.177),.071,'interiorWood',16)
 def shop_header(title,x,y,width,color):
  box('v4 shop portal',(x,y,3.95),(width,.32,.85),color)
  text('v4 shop identity',title,(x,y-.19,3.78),.43,'v4Paper')
  box('v4 shop light ribbon',(x,y-.22,3.48),(width,.10,.065),'v4Light')
 # Boutique: warm timber display wall, hanging outfits, an island and mirrors.
 box('v4 boutique rug',(25,72,.13),(22,15,.025),'v4Ivory')
 box('v4 boutique wall',(25,79.3,2.2),(23,.28,4.3),'v4Oak')
 shop_header('慢 衣  /  URBAN EDIT',25,66.5,19,'v4Teal')
 for x in [17,25,33]:
  solid('v4 garment rack footprint',(x,76,.24),(5,.85,.16),'v4Ink')
  for dx in [-2.2,2.2]:rod('v4 garment rack',(x+dx,76,.3),(x+dx,76,2.55),.035,'gold')
  rod('v4 garment rail',(x-2.2,76,2.55),(x+2.2,76,2.55),.04,'gold')
  for j in range(6):
   xx=x-1.7+j*.68;col=['v4Ivory','v4Blue','v4Clay','v4Pink','v4Teal','v4Ink'][j]
   rod('v4 hanger',(xx,76,2.52),(xx,76,2.33),.015,'gold')
   box('v4 hanging coat',(xx,76,1.88),(.48,.22,.91),col)
   for side in [-1,1]:box('v4 coat sleeve',(xx+side*.29,76,2.02),(.17,.24,.62),col,side*.18)
   box('v4 coat placket',(xx,75.88,1.91),(.025,.015,.79),'v4Paper')
 solid('v4 boutique display island',(24,70,.64),(4,1.6,1.0),'v4Oak')
 for x in [22.8,24,25.2]:
  for k in range(3):box('v4 folded knitwear',(x,70,1.18+k*.12),(.85,.75,.10),['v4Pink','v4Ivory','v4Blue'][k])
 for x in [12.2,37.8]:
  solid('v4 fitting mirror frame',(x,76,1.6),(.24,2.1,2.9),'gold')
  box('v4 fitting mirror',(x-.13,76,1.6),(.02,1.85,2.64),'glass2')
 plant(34,69,1.1)
 # Technology shop: laptop islands, phone stands, screen wall and stools.
 box('v4 tech wall',(58,79.25,2.2),(18,.3,4.3),'v4Ink')
 shop_header('极 客  /  DIGITAL LAB',58,69,17,'v4Ink')
 for x in [52,57,62]:
  box('v4 backlit tech display',(x,79,2.25),(3.5,.12,1.9),'v4Screen')
  text('v4 screen typography',['CONNECTED','CREATE','PLAY'][int((x-52)/5)],(x,78.90,2.17),.30,'v4Paper')
 for x in [53,61]:
  solid('v4 tech island',(x,74,.73),(4,1.5,1.25),'v4Ivory')
  for dx in [-1,1]:
   box('v4 laptop keyboard',(x+dx,74,1.41),(.65,.45,.035),'silver')
   box('v4 laptop screen shell',(x+dx,74.23,1.66),(.66,.04,.48),'v4Ink')
   box('v4 laptop screen',(x+dx,74.20,1.66),(.60,.018,.42),'v4Screen')
  chair(x,72.4,0,'v4Blue')
 # Food corner: menu boards, ordering counter, trays and usable circulation.
 shop_header('一 碗 一 日  /  CITY KITCHEN',79,70,17,'v4Clay')
 box('v4 kitchen backdrop',(79,79.35,2.1),(18,.25,4.0),'v4Ivory')
 for x,label in [(73,'现煮面食'),(79,'今日简餐'),(85,'鲜果茶饮')]:
  box('v4 menu board',(x,79.1,2.9),(4.6,.13,1.25),'v4Teal')
  text('v4 menu',label,(x,79.0,2.85),.32,'v4Paper')
 solid('v4 deli counter',(79,77.5,.78),(15,1.45,1.28),'v4Oak')
 box('v4 deli worktop',(79,77.5,1.46),(15.3,1.6,.12),'v4Ivory')
 for x in [73,75,78,81,84]:
  box('v4 food tray',(x,77.3,1.55),(.85,.65,.06),'silver')
  for k in range(3):ball('v4 buns',(x-.25+k*.25,77.3,1.7),(.13,.13,.13),'cream')
 for x in [76,84]:
  solid('v4 dining table',(x,73,.83),(1.3,1.1,.12),'v4Ivory')
  rod('v4 table stem',(x,73,.16),(x,73,.78),.085,'v4Ink')
  chair(x-.95,73,-math.pi/2,'v4Clay');chair(x+.95,73,math.pi/2,'v4Clay');cup(x,73,.91)
 # Existing coffee shop gets an espresso machine, a pastry case, cups and full chairs.
 box('v4 espresso machine',(14,41.7,1.63),(.85,1.2,.70),'silver')
 box('v4 espresso panel',(15,41.7,1.69),(.045,.82,.36),'v4Ink')
 for y in [41.4,41.9]:rod('v4 espresso spout',(15.05,y,1.68),(15.05,y,1.48),.025,'silver');cup(14.9,y,1.32)
 box('v4 pastry display base',(14,46,1.35),(1.9,2.6,.13),'v4Oak')
 for y in [45.2,46,46.8]:
  for x in [13.6,14.3]:ball('v4 croissant',(x,y,1.56),(.20,.12,.11),'gold',14,8)
 for y in [40,44,48]:
  box('v4 coffee menu',(10.6,y,2.8),(.16,2.6,1.3),'v4Ink')
 for y in [53,59]:
  for x in [15,23]:
   cup(x-.22,y,.97);box('v4 cafe book',(x+.20,y,.985),(.35,.43,.06),'v4Clay')
   for side in [-1,1]:
    box('v4 cafe chair back',(x+side*1.10,y,.85),(.12,.48,.68),'interiorCoral')
    for yy in [-.17,.17]:rod('v4 cafe chair leg',(x+side*.9,y+yy,.14),(x+side*.9,y+yy,.47),.023,'v4Ink')
    collider(x+side*.9,y,.58,.62)
 # Books: front-facing tables and reading seats.
 for y in [40,51]:
  solid('v4 book display island',(79,y,.61),(3.6,1.6,1.0),'v4Oak')
  for x in [77.8,78.6,79.4,80.2]:
   for z in [1.16,1.24,1.32]:box('v4 stacked books',(x,y,z),(.61,.88,.075),r.choice(['v4Pink','v4Blue','v4Ivory','v4Teal']))
 for x in [79,82]:chair(x,57,math.pi,'v4Blue')
 # Public fit-out visible from the main entrance.
 for x in [52,64]:
  solid('v4 directory pedestal',(x,31,1.12),(1.15,.65,1.94),'v4Ink')
  box('v4 directory screen',(x,30.65,1.38),(.88,.025,1.18),'v4Screen')
  text('v4 directory','1F\n逛街 · 美食\n阅读 · 休息',(x,30.61,1.68),.15,'v4Paper')
 for x in [47,68]:plant(x,30,1.15)
 for x in [40,43]:
  box('v4 desk terminal',(x,28,1.56),(.65,.15,.46),'v4Ink')
  box('v4 terminal display',(x,27.91,1.56),(.59,.02,.39),'v4Screen')
  box('v4 leaflet stand',(x+.7,27.8,1.45),(.3,.35,.30),'v4Paper')
 # Paired vending machines, recycling stations, a gallery and decorative ceiling fins.
 for x,col in [(85,'v4Clay'),(87,'v4Teal')]:
  solid('v4 vending machine',(x,28,1.24),(1.5,1.0,2.18),col)
  box('v4 vending window',(x,27.47,1.42),(1.08,.04,1.26),'v4Ink')
  for z in [.99,1.4,1.8]:
   for xx in [-.36,0,.36]:rod('v4 beverage',(x+xx,27.42,z),(x+xx,27.42,z+.24),.085,r.choice(['v4Pink','v4Blue','v4Paper']))
  text('v4 vending title','DRINKS',(x,27.4,2.16),.16,'v4Paper')
 for x,y in [(46,35),(86,61),(39,72)]:
  solid('v4 recycling station',(x,y,.68),(.9,.55,1.10),'v4Teal')
  box('v4 bin opening',(x,y-.29,.94),(.62,.025,.18),'v4Ink')
 for x in [43,48,53,58,63]:
  box('v4 suspended timber fin',(x,48,5.43),(.12,23,.38),'v4Oak')
  box('v4 inset light',(x+.15,48,5.41),(.055,21,.045),'v4Light')
 for x in [42,48,54]:
  box('v4 ceiling banner',(x,58,4.55),(2.8,.10,1.5),'v4Teal')
  text('v4 wayfinding banner',['COFFEE','CITY LIFE','BOOKS'][int((x-42)/6)],(x,57.93,4.45),.24,'v4Paper')
 # Low gallery panels with original abstract compositions.
 for x in [45,50,55]:
  box('v4 gallery frame',(x,79.25,2.3),(3.1,.15,2.1),'gold')
  box('v4 gallery paper',(x,79.14,2.3),(2.9,.04,1.9),'v4Paper')
  ball('v4 abstract sun',(x-.55,79.08,2.55),(.45,.035,.45),'v4Clay',24,12)
  box('v4 abstract horizon',(x+.2,79.06,1.95),(1.7,.045,.42),'v4Teal')
 return {'version':4,'zones':['慢衣服饰店','极客数码体验区','一碗一日餐饮区','咖啡陈设','书屋展台','商场公共设施'],'originalDesign':True}
