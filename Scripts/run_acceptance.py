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
def pad(index,key):
    action(index,'pad_'+key+'_down');time.sleep(.15);action(index,'pad_'+key+'_up')
def start(count):
    call('editor_toolset.toolsets.object.ObjectTools','set_properties',
         instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},
         values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
    call('editor_toolset.toolsets.object.ObjectTools','set_properties',
         instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},
         values=json.dumps({'PlayNumberOfClients':count,'RunUnderOneProcess':True,
             'PlayNetMode':'PIE_Standalone' if count==1 else 'PIE_ListenServer',
             'NewWindowWidth':960 if count==1 else 640,'NewWindowHeight':540 if count==1 else 360,'ClientWindowWidth':640,'ClientWindowHeight':360}))
    call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InEditorFloating','warmupSeconds':2})
    action(0,'automation_on');time.sleep(.25)
def stop():
    if call(app_tool,'IsPIERunning'):call(app_tool,'StopPIE')

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
def player(data,index):return sorted(server(data)['pawns'],key=lambda p:p['playerId'])[index]
def synced(data,index,predicate):
    identity=player(data,index)['playerId']
    return len(data['worlds'])==4 and all(any(p['playerId']==identity and predicate(p) for p in w['pawns']) for w in data['worlds'])
def aligned(data,index):
    target=player(data,index)
    return synced(data,index,lambda p:sum((p[k]-target[k])**2 for k in ['x','y','z'])<25**2)

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
    check('spy camera is actually third person and HUD draws',lambda:wait_for(lambda d:local_pawn(d)['actualCameraOffset']>200 and local_pawn(d).get('hudShown') and local_pawn(d).get('hudLastDraw',-1)>=0))
    check('controller bindings installed',lambda:wait_for(lambda d:all(k in local_pawn(d)['inputKeys'] for k in ['Gamepad_Left2D','Gamepad_Right2D','Gamepad_FaceButton_Bottom','Gamepad_FaceButton_Right','Gamepad_FaceButton_Left','Gamepad_FaceButton_Top','Gamepad_LeftTrigger','Gamepad_RightTrigger','Gamepad_DPad_Right'])))
    action(0,'place_open');time.sleep(.3)
    baseline=local_pawn(report())
    action(0,'pad_drift_down');time.sleep(.5);action(0,'pad_drift_up')
    check('stick dead zone prevents drift',lambda:wait_for(lambda d:abs(local_pawn(d)['x']-baseline['x'])<2 and abs(local_pawn(d)['y']-baseline['y'])<2))
    action(0,'pad_move_down');time.sleep(.5);action(0,'pad_move_up')
    check('left stick moves character',lambda:wait_for(lambda d:local_pawn(d)['x']>baseline['x']+30))
    action(0,'pad_look_down');time.sleep(.5);action(0,'pad_look_up')
    check('right stick turns camera',lambda:wait_for(lambda d:abs(local_pawn(d)['viewYaw'])>15))
    pad(0,'y')
    check('controller Y lowers spy goggles',lambda:wait_for(lambda d:local_pawn(d)['nightvision'] and abs(local_pawn(d)['gogglePitch'])<3 and local_pawn(d)['gamepad']))
    pad(0,'y')
    check('controller Y raises spy goggles',lambda:wait_for(lambda d:not local_pawn(d)['nightvision'] and local_pawn(d)['gogglePitch']<-100))
    pad(0,'b')
    check('controller B crouches',lambda:wait_for(lambda d:local_pawn(d)['crouched']))
    pad(0,'b');pad(0,'role')
    check('controller practice role and first-person camera',lambda:wait_for(lambda d:not local_pawn(d)['spy'] and local_pawn(d)['cameraDistance']==0 and local_pawn(d)['actualCameraOffset']<100))
    action(0,'pad_lt_down')
    check('controller LT aims merc',lambda:wait_for(lambda d:local_pawn(d)['aiming'] and local_pawn(d)['cameraFOV']<67))
    action(0,'pad_lt_up')
    check('releasing LT restores camera',lambda:wait_for(lambda d:not local_pawn(d)['aiming'] and local_pawn(d)['cameraFOV']>83))
    pad(0,'y')
    check('controller Y toggles merc flashlight',lambda:wait_for(lambda d:local_pawn(d)['flashlight']))
    pad(0,'role')
    action(0,'role')
    check('practice switches to merc',lambda:wait_for(lambda d:not local_pawn(d)['spy']))
    action(0,'role')
    check('practice switches back to spy',lambda:wait_for(lambda d:local_pawn(d)['spy']))
    action(0,'place_ledge');time.sleep(.5);pad(0,'a')
    check('spy catches ledge',lambda:wait_for(lambda d:local_pawn(d)['traversal']==2 and local_pawn(d)['motionDuration']==0))
    time.sleep(.6);pad(0,'a')
    check('spy climbs onto platform',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0 and local_pawn(d)['z']>270))
    action(0,'place_ledge');time.sleep(.5);action(0,'traverse');time.sleep(.7);action(0,'drop')
    check('spy drops from hanging',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0 and local_pawn(d)['z']<110))
    action(0,'place_vault');time.sleep(.5);action(0,'traverse')
    check('low vault completes',lambda:wait_for(lambda d:local_pawn(d)['x']>-250 and local_pawn(d)['traversal']==0))
    action(0,'place_open');time.sleep(.5);action(0,'traverse')
    check('unmarked space does not create traversal',lambda:wait_for(lambda d:local_pawn(d)['traversal']==0))
    stop();start(4)
    check('four networked worlds with 2v2',lambda:wait_for(lambda d:len(d['worlds'])==4 and all(w['spies']==2 and w['mercs']==2 and w['phase']==1 and not w['practice'] and len(w['pawns'])==4 and sum(p['local'] for p in w['pawns'])==1 for w in d['worlds']),25))
    check('correct local camera and HUD on all clients',lambda:wait_for(lambda d:all(all((p['actualCameraOffset']>200 if p['spy'] else p['actualCameraOffset']<100) and p.get('hudShown') and p.get('hudLastDraw',-1)>=0 for p in w['pawns'] if p['local']) for w in d['worlds'])))
    # Player 2 is the second spy and is owned by a remote client.
    pad(2,'y')
    check('remote controller goggles replicate',lambda:wait_for(lambda d:all(any(p['nightvision'] and abs(p['gogglePitch'])<3 for p in w['pawns']) for w in d['worlds'])))
    action(2,'place_ledge');time.sleep(1);pad(2,'a')
    check('remote spy hanging replicates',lambda:wait_for(lambda d:all(any(p['traversal']==2 and p['motionDuration']==0 for p in w['pawns']) for w in d['worlds'])))
    time.sleep(.6);pad(2,'a')
    check('remote climb completes on all clients',lambda:wait_for(lambda d:all(any(p['spy'] and p['z']>270 and p['traversal']==0 for p in w['pawns']) for w in d['worlds'])))
    action(0,'network_lag')
    check('100ms lag and 2 percent loss enabled',lambda:wait_for(lambda d:all(w.get('packetLag')==100 and w.get('packetLoss')==2 for w in d['worlds'])))
    action(2,'place_ledge');time.sleep(1);pad(2,'a')
    check('remote ledge catch under latency',lambda:wait_for(lambda d:synced(d,2,lambda p:p['traversal']==2 and p['motionDuration']==0),20))
    pad(2,'a')
    check('remote climb agrees under latency',lambda:wait_for(lambda d:synced(d,2,lambda p:p['traversal']==0 and p['z']>270) and aligned(d,2),20))
    action(2,'place_ledge');time.sleep(1);pad(2,'a')
    check('remote hangs before interrupted climb',lambda:wait_for(lambda d:synced(d,2,lambda p:p['traversal']==2 and p['motionDuration']==0),20))
    pad(2,'a')
    action(2,'damage')
    check('death cancels remote traversal',lambda:wait_for(lambda d:synced(d,2,lambda p:p['health']==0 and p['traversal']==0)))
    check('death and respawn restore remote player',lambda:wait_for(lambda d:all(len(w['pawns'])==4 and all(p['health']==100 for p in w['pawns']) for w in d['worlds']),12))
    action(0,'network_reset')
    check('network emulation restored',lambda:wait_for(lambda d:all(w.get('packetLag')==0 and w.get('packetLoss')==0 for w in d['worlds'])))
    action(0,'duel_blocked');time.sleep(1);pad(1,'rt');time.sleep(.4)
    check('cover blocks controller shooting',lambda:wait_for(lambda d:synced(d,2,lambda p:p['health']==100)))
    action(0,'duel_open');time.sleep(1);pad(1,'rt')
    check('controller RT damages enemy',lambda:wait_for(lambda d:synced(d,2,lambda p:p['health']==66)))
    time.sleep(.3);pad(1,'rt');time.sleep(.3);pad(1,'rt')
    check('three merc shots down spy',lambda:wait_for(lambda d:synced(d,2,lambda p:p['health']==0)))
    check('combat victim respawns',lambda:wait_for(lambda d:synced(d,2,lambda p:p['health']==100),12))
    action(0,'takedown_front');time.sleep(1);pad(2,'rt');time.sleep(.4)
    check('front takedown rejected',lambda:wait_for(lambda d:synced(d,1,lambda p:p['health']==100)))
    action(0,'takedown_rear');time.sleep(1);pad(2,'rt')
    check('rear controller takedown succeeds',lambda:wait_for(lambda d:synced(d,1,lambda p:p['health']==0)))
    check('merc respawns after takedown',lambda:wait_for(lambda d:synced(d,1,lambda p:p['health']==100),12))
    action(2,'place_terminal');time.sleep(1);action(2,'pad_x_down')
    check('remote hacking replicates',lambda:wait_for(lambda d:all(w['hack']>.02 for w in d['worlds'])))
    action(2,'pad_x_up');action(0,'expire')
    check('merc timer victory replicates',lambda:wait_for(lambda d:all(w['phase']==3 for w in d['worlds'])))
    check('round resets',lambda:wait_for(lambda d:all(w['phase']==1 and w['hack']==0 for w in d['worlds']),14))
    action(2,'place_terminal');time.sleep(.7);action(0,'near_complete');action(2,'hack')
    check('spy hack victory replicates',lambda:wait_for(lambda d:all(w['phase']==2 for w in d['worlds'])))
    stop();start(1);action(0,'automation_off')
    print(json.dumps({'passed':sum(c['passed'] for c in checks),'total':len(checks)}),flush=True)
