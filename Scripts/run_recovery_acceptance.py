"""Merc get-up shield: visible arcs, real blocked contacts, control and expiry."""
import json,time,math,base64
from pathlib import Path
from run_acceptance import *

OUT=Path('Saved/RecoveryQA');OUT.mkdir(parents=True,exist_ok=True);checks=[]
def check(name,predicate,seconds=15):
    try:d=wait_for(predicate,seconds)
    except Exception as e:
        (OUT/'failure.txt').write_text(str(e));raise AssertionError(name+'; see Saved/RecoveryQA/failure.txt') from None
    checks.append({'name':name,'passed':True});(OUT/'acceptance.json').write_text(json.dumps(checks,indent=2));print('PASS',name,flush=True);return d
def merc(d):return player(d,1)
def fresh(fps=30,lag=False,viewport=False):
    stop();call(project_tool,'open_map',map_name='Warehouse')
    if viewport:
        call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
        call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},values=json.dumps({'PlayNumberOfClients':4,'RunUnderOneProcess':True,'PlayNetMode':'PIE_ListenServer','ClientWindowWidth':640,'ClientWindowHeight':360}))
        call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2});action(0,'automation_on')
    else:start(4)
    action(0,'drop_fps_'+str(fps))
    if lag:action(0,'network_lag')
    check('fresh round has no stale protection',lambda d:len(d['worlds'])==4 and server(d)['phase']==1 and all(not p['recoveryShield'] for w in d['worlds'] for p in w['pawns']))
def knock():
    assert 'fixture started' in action(0,'drop_attack')
    check('physical drop knocks merc out',lambda d:synced(d,1,lambda p:p['knockedOut'] and p['health']==100))
def ready():return check('merc regains weapon while shield is active',lambda d:synced(d,1,lambda p:p['recoveryShield'] and not p['gettingUp'] and not p['knockedOut'] and p['equipment']['weaponReady']))
def expired():return check('protection and visible current expire on every client',lambda d:synced(d,1,lambda p:not p['recoveryShield'] and not p['shieldFXVisible'] and not p['gettingUp']))

try:
    fresh(viewport=True);knock();action(0,'recovery_observer');action(0,'recovery_camp')
    check('electrical wake-up cue starts before control returns',lambda d:merc(d)['knockedOut'] and synced(d,1,lambda p:p['recoveryShield'] and p['shieldFXVisible'] and p['shieldArcCount']==48 and p['shieldGlow']>0))
    check('camping spy is pushed clear for get-up',lambda d:math.hypot(player(d,2)['x']-merc(d)['x'],player(d,2)['y']-merc(d)['y'])>100,5)
    check('get-up transition is protected',lambda d:merc(d)['gettingUp'] and merc(d)['recoveryShield'] and not merc(d)['knockedOut'])
    action(0,'review_freeze');time.sleep(.1)
    r=call(app_tool,'CaptureEditorImage');(OUT/'get-up-shield.png').write_bytes(base64.b64decode(r['data']));(OUT/'get-up-shield.json').write_text(json.dumps(report(),indent=2));action(0,'review_normal')
    d=ready();assert merc(d)['shieldRemaining']>1
    old=merc(d);action(1,'pad_move_down');time.sleep(.3);action(1,'pad_move_up')
    check('protected merc can reposition',lambda d:merc(d)['recoveryShield'] and math.hypot(merc(d)['x']-old['x'],merc(d)['y']-old['y'])>20,3)
    pad(1,'rt');check('protected merc can fire the carbine',lambda d:merc(d)['recoveryShotsFired']>0)
    action(1,'wound');check('shield preserves ordinary damage counterplay',lambda d:merc(d)['health']==90 and merc(d)['recoveryShield'],3)
    action(1,'damage');check('death removes current and protection',lambda d:synced(d,1,lambda p:p['health']==0 and not p['recoveryShield'] and not p['shieldFXVisible']))
    check('respawn does not inherit shield',lambda d:synced(d,1,lambda p:p['health']==100 and not p['recoveryShield'] and not p['gettingUp']),15)

    fresh(lag=True);knock();ready();action(0,'takedown_rear');time.sleep(.3);pad(2,'x')
    check('rear X grab rejected by server shield rule under latency',lambda d:merc(d)['recoveryGrabBlocks']>0 and merc(d)['recoveryShield'] and synced(d,1,lambda p:p['grabToken']==0) and synced(d,2,lambda p:p['grabToken']==0),4)
    check('rejected grab does not open pair voice',lambda d:merc(d)['voice']['pairToken']==0 and player(d,2)['voice']['pairToken']==0)
    expired();pad(2,'x');check('same rear grab succeeds after shield expires',lambda d:synced(d,1,lambda p:p['grabToken']>0) and synced(d,2,lambda p:p['grabToken']>0))
    pad(2,'b');check('normal grab release still works',lambda d:synced(d,1,lambda p:p['grabToken']==0));action(0,'network_reset')

    fresh(fps=6,lag=True);knock();ready();before=player(report(),2)['dropKnockouts'];assert 'fixture started' in action(0,'drop_fast')
    check('six-FPS protected head landing is blocked under lag and loss',lambda d:merc(d)['recoveryDropBlocks']>0 and not merc(d)['knockedOut'] and player(d,2)['dropKnockouts']==before,5)
    check('blocked landing pushes spy away',lambda d:math.hypot(player(d,2)['x']-merc(d)['x'],player(d,2)['y']-merc(d)['y'])>80,5)
    expired();assert 'fixture started' in action(0,'drop_attack')
    check('fresh landing works after protection expires',lambda d:synced(d,1,lambda p:p['knockedOut']) and player(d,2)['dropKnockouts']==before+1)
    action(0,'network_reset');action(0,'drop_fps_30')
    check('shield activates for next recovery',lambda d:synced(d,1,lambda p:p['recoveryShield']))
    action(0,'expire');check('round result clears active visual protection',lambda d:server(d)['phase']!=1 and synced(d,1,lambda p:not p['recoveryShield'] and not p['shieldFXVisible']))
    check('round reset spawns clean players',lambda d:server(d)['phase']==1 and all(not p['recoveryShield'] and not p['gettingUp'] for w in d['worlds'] for p in w['pawns']),20)
    (OUT/'summary.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'shield_seconds':3,'getup_seconds':.8,'network':'Four local PIE worlds, including 6 FPS cap with 100 ms lag and 2% loss','visual':'Actual in-editor capture: get-up-shield.png','limits':'Mac PIE; physical controller and Xbox hardware remain unverified'},indent=2))
    print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
    action(0,'review_normal');action(0,'drop_fps_restore');action(0,'network_reset');stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
