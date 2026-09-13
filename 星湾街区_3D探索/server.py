"""Local-only scene server. Ollama decisions are validated data, never executable code."""
import json, os, re, sys, threading, urllib.request, urllib.error, webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
ROOT=Path(__file__).resolve().parent
LOCK=threading.Lock()
DESTINATIONS={'mall','cafe','garden','bikes','west','southwest','northwest','east','atrium','service','insideCafe','books','toys','rest','market','courier','park','art','overlook'}
def requested_destination(message):
    clauses=re.findall(r'(?:前往|想去|改去|去|找)([^，。！？]+)',message)
    if not clauses:return None
    clause=clauses[-1]
    for words,dest in [(['小集','集市'],'market'),(['驿站'],'courier'),(['公园'],'park'),(['光环','雕塑'],'art'),(['长廊','落日'],'overlook'),(['书店','书屋','books'],'books'),(['咖啡','insideCafe'],'insideCafe'),(['童趣','玩具','toys'],'toys'),(['服务台','service'],'service'),(['休息区','rest'],'rest'),(['中庭','atrium'],'atrium'),(['入口','门口'],'mall'),(['花园','garden'],'garden'),(['单车','bikes'],'bikes')]:
        if any(word in clause for word in words):return dest
    return None
def ollama(path,body=None,timeout=5):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request('http://127.0.0.1:11434'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)
def models():
    names=[x['name'] for x in ollama('/api/tags').get('models',[])]
    preferred=os.environ.get('STARBAY_AI_MODEL','qwen3.5:4b')
    return preferred if preferred in names else next((n for n in names if not any(k in n for k in ['bge','embed','270m'])),None)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,fmt,*args):print(fmt%args,flush=True)
    def respond(self,data,status=200):
        raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/api/health':return self.respond({'app':'starbay-explorer','version':5})
        if self.path=='/api/ai/status':
            try:
                model=models();return self.respond({'available':bool(model),'model':model})
            except Exception:return self.respond({'available':False,'model':None})
        return super().do_GET()
    def do_POST(self):
        if self.path not in ['/api/decision','/api/chat']:return self.respond({'error':'not found'},404)
        origin=self.headers.get('Origin','')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:return self.respond({'error':'origin rejected'},403)
        if not LOCK.acquire(False):return self.respond({'error':'AI busy; local behavior continues'},409)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<12000:return self.respond({'error':'invalid body size'},400)
            data=json.loads(self.rfile.read(length));model=models()
            if not model:return self.respond({'error':'No local language model'},503)
            context={k:data.get(k) for k in ['worldTime','name','kind','age','personality','state','currentNode','currentZone','destination','message','needs','history']}
            system='你是星湾街区三维体验中的虚构路人，用符合年龄和性格的简短中文交谈。你负责理解对话和选择目的地，实际行走由程序执行。可去的目的地：mall星湾入口；cafe沿街店铺；garden街角花园；bikes共享单车；west西侧人行道；southwest西南街角；northwest西北街角；east东侧街道；atrium商场中庭；service服务台；insideCafe室内咖啡区；books城市书屋；toys童趣乐园；rest室内休息区；market晚风小集；courier街区驿站；park口袋公园；art光环广场；overlook落日长廊。夜间可以去小集、室内或广场散步。整个星湾世界是虚构设定，不对应任何真实城市、商场或商家。不要把这个世界说成任何真实地名。用户要求带路时优先选择相应目的地。不要声称已经到达，不要猜东西南北方向或真实营业信息。只输出JSON：say一句不超过45字的对话、destination上述ID之一、reason一句不超过25字的选择原因。如果是child，只可选择mall/atrium/insideCafe/toys/rest。'
            result=ollama('/api/chat',{'model':model,'stream':False,'think':False,'format':'json','keep_alive':'10m','messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(context,ensure_ascii=False)}],'options':{'temperature':.7,'num_predict':180,'num_ctx':2048}},timeout=100)
            reply=json.loads(result['message']['content']);dest=reply.get('destination')
            allowed={'mall','atrium','insideCafe','toys','rest'} if data.get('kind')=='child' else DESTINATIONS
            if dest not in allowed:dest=None
            requested=requested_destination(str(data.get('message','')))
            if requested in allowed:
                dest=requested
                reply['reason']='按你指定的最终目的地前往，中间路点由寻路程序处理'
            say=str(reply.get('say',''))[:160]
            return self.respond({'say':say,'destination':dest,'destinationSource':'user' if requested in allowed else 'model','reason':str(reply.get('reason',''))[:80],'model':model,'source':'ollama'})
        except Exception as e:return self.respond({'error':str(e)[:240]},503)
        finally:LOCK.release()

if __name__=='__main__':
    for port in range(8765,8785):
        try:
            req=urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.3)
            if json.load(req).get('app')=='starbay-explorer':
                if '--no-browser' not in sys.argv:webbrowser.open(f'http://127.0.0.1:{port}')
                sys.exit(0)
        except Exception:pass
        try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
        except OSError:continue
    else:raise RuntimeError('No available local port')
    (ROOT/'server-port.txt').write_text(str(port))
    print(f'Starbay explorer: http://127.0.0.1:{port}',flush=True)
    if '--no-browser' not in sys.argv:webbrowser.open(f'http://127.0.0.1:{port}')
    server.serve_forever()
