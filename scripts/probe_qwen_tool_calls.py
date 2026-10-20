import json, os, urllib.request, time
base=os.getenv('OPENAI_API_BASE_URLS','http://vllm:8000/v1').split(';')[0].split(',')[0].rstrip('/')
key=os.getenv('VLLM_API_KEY','')
def call(messages, tools):
    data=json.dumps(dict(model='qwen2.5-14b',messages=messages,tools=tools,temperature=0,max_tokens=120,stream=False)).encode()
    req=urllib.request.Request(base+'/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    with urllib.request.urlopen(req,timeout=45) as r: return json.load(r)['choices'][0]['message']
tools=[{'type':'function','function':{'name':'probe_echo','description':'Echo a synthetic test value','parameters':{'type':'object','properties':{'value':{'type':'string'}},'required':['value'],'additionalProperties':False}}}]
m=[{'role':'user','content':'Call probe_echo with value synthetic-ok. Do not answer before calling it.'}]
t=time.monotonic()
a=call(m,tools)
c=a.get('tool_calls',[])
print(json.dumps({'model':'qwen2.5-14b','probe':'synthetic-no-ERP','tool_calls':c,'latency_seconds':round(time.monotonic()-t,3)}))
if c:
    m += [{'role':'assistant','content':a.get('content'),'tool_calls':c}]
    m += [{'role':'tool','tool_call_id':x['id'],'content':'{"value":"synthetic-ok"}'} for x in c]
    b=call(m,tools)
    print(json.dumps({'tool_reply_accepted': bool(b.get('content')), 'content':b.get('content')}))
