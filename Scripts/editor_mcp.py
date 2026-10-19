"""Sequential client for Epic's native loopback MCP. No third-party dependencies."""
import argparse, json, urllib.request

class EditorMCP:
    def __init__(self, url='http://127.0.0.1:8000/mcp'):
        self.url, self.session, self.seq = url, None, 0
        self.rpc('initialize', {'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'stealth-project-tools','version':'1'}})
        self.rpc('notifications/initialized', {}, notification=True)
    def rpc(self, method, params, notification=False):
        self.seq += 1
        payload={'jsonrpc':'2.0','method':method,'params':params}
        if not notification: payload['id']=self.seq
        headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.session: headers['Mcp-Session-Id']=self.session
        request=urllib.request.Request(self.url,json.dumps(payload).encode(),headers)
        with urllib.request.urlopen(request,timeout=180) as response:
            self.session=response.headers.get('Mcp-Session-Id',self.session)
            if 'text/event-stream' in response.headers.get('Content-Type',''):
                raw=''
                for line in response:
                    decoded=line.decode()
                    if decoded.startswith('data:'):
                        item=json.loads(decoded[5:].strip())
                        if item.get('id')==self.seq:
                            raw=json.dumps(item);break
            else: raw=response.read().decode()
        if not raw.strip(): return {}
        if raw.lstrip().startswith('data:') or 'event:' in raw:
            messages=[json.loads(line[5:].strip()) for line in raw.splitlines() if line.startswith('data:')]
            data=next((m for m in messages if m.get('id')==self.seq),messages[-1])
        else: data=json.loads(raw)
        if 'error' in data: raise RuntimeError(data['error'])
        return data.get('result',data)
    def tool(self,name,arguments):
        result=self.rpc('tools/call',{'name':name,'arguments':arguments})
        if result.get('isError'): raise RuntimeError(result)
        return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('tool');parser.add_argument('arguments',nargs='?',default='{}')
    args=parser.parse_args()
    print(json.dumps(EditorMCP().tool(args.tool,json.loads(args.arguments)),indent=2))
