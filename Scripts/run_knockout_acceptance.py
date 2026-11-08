"""Real movement-collision knockouts under frame caps, recovery and network loss."""
import json,time,math
from pathlib import Path
from run_acceptance import *

OUT=Path('Saved/KnockoutQA');OUT.mkdir(parents=True,exist_ok=True)
checks=[];timings=[]
def passed(name,observed=True):
    checks.append({'name':name,'passed':True,'observed':observed})
    (OUT/'acceptance.json').write_text(json.dumps(checks,indent=2))
    print('PASS',name,flush=True)
def require(name,predicate,seconds=15):
    try:d=wait_for(predicate,seconds)
    except Exception as e:
        (OUT/'failure.txt').write_text(str(e));raise AssertionError(name+'; see Saved/KnockoutQA/failure.txt') from None
    passed(name);return d
def count(d,index=2):return player(d,index)['dropKnockouts']
def recovered():
    return require('merc recovers capsule, weapon and controls',lambda d:synced(d,1,lambda p:not p['knockedOut'] and not p['recoveryShield'] and p['health']==100 and p['capsuleHalfHeight']>80 and p['equipment']['weaponReady']),20)
def physical_drop(label,fixture='drop_attack',spy=2):
    before=count(report(),spy);result=action(0,fixture)
    if 'fixture started' not in result:
        (OUT/'failed-fixture.json').write_text(json.dumps({'result':result,'state':report()},indent=2));raise AssertionError(label+': '+result)
    samples=[];deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        d=report();s=player(d,spy);m=player(d,1)
        samples.append({'frameMs':d['frameMs'],'spy':{k:s[k] for k in ['x','y','z','verticalSpeed','falling','dropKnockouts']},'merc':{k:m[k] for k in ['health','knockedOut','capsuleHalfHeight']}})
        if synced(d,1,lambda p:p['knockedOut'] and p['health']==100):break
        time.sleep(.04)
    else:
        (OUT/'failed-trajectory.json').write_text(json.dumps(samples,indent=2));raise AssertionError(label+' missed physical landing')
    assert count(d,spy)==before+1,'Duplicate/missing impact award'
    passed(label,{'new_knockouts':count(d,spy)-before,'frame_ms':[min(p['frameMs'] for p in samples),max(p['frameMs'] for p in samples)]})
    timings.extend(p['frameMs'] for p in samples)
    (OUT/(label.replace(' ','-')+'.json')).write_text(json.dumps(samples,indent=2))
    require('knockout collision/body replicates above floor',lambda d:synced(d,1,lambda p:p['knockedOut'] and p['capsuleHalfHeight']<40 and p['headZ']>0 and p['pelvisZ']>0))
    time.sleep(.5);assert count(report(),spy)==before+1;passed('one collision awards exactly one knockout')
    recovered()

try:
    stop();call(project_tool,'open_map',map_name='Warehouse');start(4)
    require('four-client warehouse active',lambda d:len(d['worlds'])==4 and server(d)['phase']==1)
    for fps in [60,30,15,6]:
        if fps!=60:
            stop();start(4);require('fresh round for frame-cap group',lambda d:len(d['worlds'])==4 and server(d)['phase']==1)
        assert 'Temporary' in action(0,'drop_fps_'+str(fps));time.sleep(.5)
        before=count(report());action(0,'drop_miss');time.sleep(1.7)
        assert synced(report(),1,lambda p:not p['knockedOut'] and p['health']==100) and count(report())==before
        passed(f'{fps} cap near miss rejected')
        action(0,'drop_covered');time.sleep(1.7)
        assert synced(report(),1,lambda p:not p['knockedOut'] and p['health']==100) and count(report())==before
        passed(f'{fps} cap solid cover blocks knockout');action(0,'clear_drop_cover')
        require('cover fixture resets server and owner before next drop',lambda d:all(math.hypot(p['x']-player(d,1)['x'],p['y']-player(d,1)['y'])>400 for w in d['worlds'] for p in w['pawns'] if p['playerId']==player(d,2)['playerId'] and (p['local'] or w['netMode']!=3)))
        physical_drop(f'{fps} cap first drop')
        physical_drop(f'{fps} cap repeated drop after recovery')
        physical_drop(f'{fps} cap fast drop','drop_fast')
    action(0,'network_lag');physical_drop('6 cap lag loss drop')
    physical_drop('6 cap lag loss repeated drop')
    action(0,'network_reset');action(0,'drop_fps_30');physical_drop('host spy drop','drop_host',0)
    # Existing controller bindings must still be rejected while unconscious.
    action(0,'drop_attack');require('final remote drop for interruption',lambda d:synced(d,1,lambda p:p['knockedOut']))
    pad(1,'rt');pad(1,'gadget');pad(1,'a')
    require('unconscious controller cannot shoot throw or jump',lambda d:synced(d,1,lambda p:p['knockedOut'] and p['mercGrenades']==2 and p['capsuleHalfHeight']<40) and all(not w['grenades'] for w in d['worlds']))
    action(1,'damage');require('death clears knockout on every client',lambda d:synced(d,1,lambda p:p['health']==0 and not p['knockedOut']))
    require('respawn restores standing merc and supplies',lambda d:synced(d,1,lambda p:p['health']==100 and not p['knockedOut'] and p['capsuleHalfHeight']>80 and p['mercGrenades']==2),20)
    (OUT/'summary.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'observed_frame_ms':{'min':min(timings),'max':max(timings)},'requested_caps':[60,30,15,6],'note':'Caps are upper bounds; measured frame times are recorded. Local Mac PIE is not Xbox hardware validation.'},indent=2))
    print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
    action(0,'drop_fps_restore');action(0,'network_reset');stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
