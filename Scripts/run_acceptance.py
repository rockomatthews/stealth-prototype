"""Native-MCP acceptance checks. Start our editor and enable project toolset first.
Writes actual observations to Saved/acceptance.json. Leaves solo practice open.
"""
import json,time
from pathlib import Path
from editor_mcp import EditorMCP

client=EditorMCP()
project_tool='stealth_tools.StealthProjectTools'
app_tool='EditorToolset.EditorAppToolset'

def unpack(result):
    if result.get('structuredContent') is not None: return result['structuredContent']
    texts=[b['text'] for b in result.get('content',[]) if b.get('type')=='text']
    if not texts: return result
    try: return json.loads(texts[0])
    except ValueError: return texts[0]

def call(toolset,tool,**arguments):
    data=unpack(client.tool('call_tool',{'toolset_name':toolset,'tool_name':tool,'arguments':arguments}))
    if isinstance(data,dict) and 'returnValue' in data:return data['returnValue']
    return data

def report():return json.loads(call(project_tool,'runtime_report'))
def action(player_index,action):return call(project_tool,'exercise',player_index=player_index,action=action)
def start(count):
    call('editor_toolset.toolsets.object.ObjectTools','set_properties',
         instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},
         values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
    call('editor_toolset.toolsets.object.ObjectTools','set_properties',
         instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},
         values=json.dumps({'PlayNumberOfClients':count,'RunUnderOneProcess':True,
             'PlayNetMode':'PIE_Standalone' if count==1 else 'PIE_ListenServer',
             'NewWindowWidth':640,'NewWindowHeight':360,'ClientWindowWidth':640,'ClientWindowHeight':360}))
    call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InEditorFloating','warmupSeconds':2})
def stop():call(app_tool,'StopPIE')

def wait_for(predicate,seconds=12):
    end=time.monotonic()+seconds
    last=None
    while time.monotonic()<end:
        last=report()
        if predicate(last):return last
        time.sleep(.3)
    raise AssertionError('Timed out; last state: '+json.dumps(last))

def server(data):return next(w for w in data['worlds'] if w['netMode']!=3)
def local_pawn(data,spy=None):
    return next(p for p in server(data)['pawns'] if spy is None or p['spy']==spy)

checks=[]
def check(name,fn):
    try:
        observed=fn();checks.append({'name':name,'passed':True,'observed':observed});print('PASS',name,flush=True)
    except Exception as error:
        checks.append({'name':name,'passed':False,'error':str(error)});print('FAIL',name,str(error),flush=True)
    Path(__file__).resolve().parents[1].joinpath('Saved/acceptance.json').write_text(json.dumps(checks,indent=2))

if __name__=='__main__':
    check('project identity',lambda:call(project_tool,'identity'))
    start(1)
    check('solo practice and skeletal character',lambda:wait_for(lambda d:len(d['worlds'])==1 and server(d)['practice'] and all(p['mesh'] for p in server(d)['pawns'])))
    action(0,'role')
    check('practice switches to merc',lambda:wait_for(lambda d:not local_pawn(d)['spy']))
    action(0,'role')
    check('practice switches back to spy',lambda:wait_for(lambda d:local_pawn(d)['spy']))
    action(0,'place_ledge');time.sleep(.5);action(0,'traverse')
    check('spy catches ledge',lambda:wait_for(lambda d:local_pawn(d)['traversal']==2 and local_pawn(d)['motionDuration']==0))
    time.sleep(.6);action(0,'traverse')
    check('spy climbs onto platform',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0 and local_pawn(d)['z']>270))
    action(0,'place_ledge');time.sleep(.5);action(0,'traverse');time.sleep(.7);action(0,'drop')
    check('spy drops from hanging',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0 and local_pawn(d)['z']<110))
    action(0,'place_vault');time.sleep(.5);action(0,'traverse')
    check('low vault completes',lambda:wait_for(lambda d:local_pawn(d)['x']>-250 and local_pawn(d)['traversal']==0))
    action(0,'place_open');time.sleep(.5);action(0,'traverse')
    check('unmarked space does not create traversal',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0))
    stop();start(4)
    check('four networked worlds with 2v2',lambda:wait_for(lambda d:len(d['worlds'])==4 and all(w['spies']==2 and w['mercs']==2 and w['phase']==1 and not w['practice'] and len(w['pawns'])==4 and sum(p['local'] for p in w['pawns'])==1 for w in d['worlds']),25))
    # Player 2 is the second spy and is owned by a remote client.
    action(2,'place_ledge');time.sleep(1);action(2,'traverse')
    check('remote spy hanging replicates',lambda:wait_for(lambda d:all(any(p['traversal']==2 and p['motionDuration']==0 for p in w['pawns']) for w in d['worlds'])))
    time.sleep(.6);action(2,'traverse')
    check('remote climb completes on all clients',lambda:wait_for(lambda d:all(any(p['spy'] and p['z']>270 and p['traversal']==0 for p in w['pawns']) for w in d['worlds'])))
    action(2,'damage')
    check('death and respawn restore remote player',lambda:wait_for(lambda d:all(len(w['pawns'])==4 and all(p['health']==100 for p in w['pawns']) for w in d['worlds']),12))
    action(2,'place_terminal');time.sleep(1);action(2,'hack')
    check('remote hacking replicates',lambda:wait_for(lambda d:all(w['hack']>.02 for w in d['worlds'])))
    action(2,'release');action(0,'expire')
    check('merc timer victory replicates',lambda:wait_for(lambda d:all(w['phase']==3 for w in d['worlds'])))
    check('round resets',lambda:wait_for(lambda d:all(w['phase']==1 and w['hack']==0 for w in d['worlds']),14))
    action(2,'place_terminal');time.sleep(.7);action(0,'near_complete');action(2,'hack')
    check('spy hack victory replicates',lambda:wait_for(lambda d:all(w['phase']==2 for w in d['worlds'])))
    stop();start(1)
    print(json.dumps({'passed':sum(c['passed'] for c in checks),'total':len(checks)}),flush=True)
