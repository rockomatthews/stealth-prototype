"""Gadget inventory checks using real controller inputs and replicated PIE state.
Run with the project open. Restores ordinary-input solo practice in finally.
"""
import json,time
from pathlib import Path
from run_acceptance import (report,action,pad,start,stop,wait_for,server,local_pawn,player,synced)

results=[]
def check(name,predicate,seconds=12):
    data=wait_for(predicate,seconds)
    results.append({'name':name,'passed':True,'observed':data})
    Path('Saved/EquipmentQA/gadget-inventory.json').write_text(json.dumps(results,indent=2))
    print('PASS',name,flush=True)
    return data

def eq(data):return local_pawn(data)['equipment']
def wait_shot(index):
    time.sleep(.9);pad(index,'gadget')

try:
    stop();call(project_tool,'open_map',map_name='Prototype');start(1)
    check('new spy has three cameras and four darts',lambda d:eq(d)['cameraAmmo']==3 and eq(d)['trackingAmmo']==4 and eq(d)['selectedGadget']=='StickyCamera')
    check('HUD shows both supplies and selection hint',lambda d:'Cameras 3 / Bullets 4' in eq(d)['gadgetHUD'] and 'D-pad Down' in eq(d)['gadgetHUD'])
    check('selector has keyboard and Xbox bindings',lambda d:all(k in local_pawn(d)['inputKeys'] for k in ['R','Gamepad_DPad_Down']))
    pad(0,'select_gadget')
    check('Down selects dart while leaving hands empty',lambda d:eq(d)['selectedGadget']=='TrackingDart' and eq(d)['weapon']==0 and eq(d)['trackingAmmo']==4)
    pad(0,'gadget');time.sleep(.3)
    check('holstered gadget attempt spends nothing',lambda d:eq(d)['trackingAmmo']==4 and eq(d)['weapon']==0)
    time.sleep(.3);pad(0,'select_gadget');pad(0,'y')
    check('Y draws launcher without changing camera selection',lambda d:eq(d)['selectedGadget']=='StickyCamera' and eq(d)['weaponReady'])
    action(0,'place_vault');time.sleep(.7);pad(0,'gadget')
    check('successful camera deployment spends one camera only',lambda d:eq(d)['cameraDeployed'] and eq(d)['cameraAmmo']==2 and eq(d)['trackingAmmo']==4)
    first_camera=eq(report())['cameraActor']
    pad(0,'gadget');time.sleep(.3)
    check('rapid repeated RB does not spend a second camera',lambda d:eq(d)['cameraAmmo']==2 and eq(d)['cameraActor']==first_camera)
    pad(0,'camera');check('deployed camera view enters',lambda d:eq(d)['cameraView'])
    pad(0,'select_gadget');pad(0,'gadget');time.sleep(.3)
    check('camera viewing blocks selector and gadget fire',lambda d:eq(d)['cameraAmmo']==2 and eq(d)['selectedGadget']=='StickyCamera' and eq(d)['cameraView'])
    pad(0,'camera')
    wait_shot(0);check('replacement camera spends one charge',lambda d:eq(d)['cameraAmmo']==1 and eq(d)['cameraActor']!=first_camera)
    wait_shot(0);check('last camera charge reaches zero',lambda d:eq(d)['cameraAmmo']==0 and eq(d)['cameraDeployed'])
    last_camera=eq(report())['cameraActor']
    wait_shot(0);time.sleep(.4)
    check('empty camera cannot spawn or replace and HUD says empty',lambda d:eq(d)['cameraAmmo']==0 and eq(d)['cameraActor']==last_camera and 'EMPTY' in eq(d)['gadgetHUD'])
    pad(0,'y');check('Y holsters without refilling inventory',lambda d:eq(d)['weapon']==0 and eq(d)['cameraAmmo']==0)
    time.sleep(.8);pad(0,'y');check('Y draws without refilling inventory',lambda d:eq(d)['weaponReady'] and eq(d)['cameraAmmo']==0)
    pad(0,'select_gadget');check('Down selects available dart without changing weapon',lambda d:eq(d)['selectedGadget']=='TrackingDart' and eq(d)['weapon']==1 and eq(d)['gadgetAmmo']==4)
    for remaining in [3,2,1,0]:
        wait_shot(0)
        check('dart shot spends one round including misses: '+str(remaining),lambda d,r=remaining:eq(d)['trackingAmmo']==r and eq(d)['cameraAmmo']==0)
    wait_shot(0);time.sleep(.3)
    check('empty darts stay at zero',lambda d:eq(d)['trackingAmmo']==0 and not eq(d)['trackingContacts'] and 'EMPTY' in eq(d)['gadgetHUD'])
    pad(0,'role');check('practice switches to merc',lambda d:not local_pawn(d)['spy'])
    pad(0,'select_gadget');pad(0,'gadget');time.sleep(.4)
    check('merc cannot change or fire spy inventory',lambda d:eq(d)['selectedGadget']=='TrackingDart' and eq(d)['trackingAmmo']==0 and eq(d)['cameraAmmo']==0)
    pad(0,'role');check('practice switching does not refill spy supplies',lambda d:local_pawn(d)['spy'] and eq(d)['cameraAmmo']==0 and eq(d)['trackingAmmo']==0)
    action(0,'damage');check('spy death accepted',lambda d:local_pawn(d)['health']==0)
    check('respawn restores supplies and default selection',lambda d:local_pawn(d)['health']==100 and eq(d)['cameraAmmo']==3 and eq(d)['trackingAmmo']==4 and eq(d)['selectedGadget']=='StickyCamera',12)
    stop();start(4)
    check('network round is active',lambda d:len(d['worlds'])==4 and all(w['phase']==1 and len(w['pawns'])==4 for w in d['worlds']),25)
    pad(2,'select_gadget');pad(2,'y')
    check('remote selector and ammo replicate with weapon still drawn',lambda d:synced(d,2,lambda p:p['equipment']['selectedGadget']=='TrackingDart' and p['equipment']['weaponReady'] and p['equipment']['trackingAmmo']==4))
    action(0,'duel_blocked');time.sleep(1);pad(2,'gadget');time.sleep(.5)
    check('cover blocks tracking but fired round is spent',lambda d:synced(d,2,lambda p:p['equipment']['trackingAmmo']==3) and synced(d,1,lambda p:p['equipment']['trackingSeconds']==0 and p['health']==100))
    check('blocked Spy Bullet becomes a wall radar sensor',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==1))
    action(0,'expire_sensors')
    check('expired area sensor clears before direct-tag test',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==0))
    action(0,'duel_open');time.sleep(1);pad(2,'gadget')
    check('tracking hit replicates without damage or stun',lambda d:synced(d,2,lambda p:p['equipment']['trackingAmmo']==2) and synced(d,1,lambda p:p['equipment']['trackingSeconds']>8 and p['health']==100 and not p['equipment']['stunned']))
    check('both spies get contact readouts and mercs do not',lambda d:all(all(len(p['equipment']['trackingContacts'])==(1 if p['spy'] else 0) for p in w['pawns']) for w in d['worlds']))
    check('tracking expires and all contact readouts clear',lambda d:synced(d,1,lambda p:p['equipment']['trackingSeconds']==0) and all(all(not p['equipment']['trackingContacts'] for p in w['pawns']) for w in d['worlds']),18)
    pad(2,'rt')
    check('RT remains taser and does not spend gadget rounds',lambda d:synced(d,1,lambda p:p['equipment']['stunned']) and synced(d,2,lambda p:p['equipment']['trackingAmmo']==2))
    check('stun wears off',lambda d:synced(d,1,lambda p:not p['equipment']['stunned']),8)
    action(0,'network_lag');pad(2,'select_gadget')
    check('camera selection replicates under lag and packet loss',lambda d:synced(d,2,lambda p:p['equipment']['selectedGadget']=='StickyCamera' and p['equipment']['weapon']==1),20)
    action(2,'place_vault');time.sleep(1);pad(2,'gadget')
    check('remote camera charge and placement agree under lag',lambda d:synced(d,2,lambda p:p['equipment']['cameraAmmo']==2 and p['equipment']['cameraDeployed'] and p['equipment']['trackingAmmo']==2),20)
    action(0,'network_reset')
    # Live enemy is an invalid surface for camera placement: no ammo is spent.
    action(0,'duel_open');time.sleep(1);pad(2,'gadget');time.sleep(.5)
    check('camera cannot attach to player or consume ammo for invalid surface',lambda d:synced(d,2,lambda p:p['equipment']['cameraAmmo']==2) and synced(d,1,lambda p:not p['equipment']['stunned'] and p['health']==100))
    pad(2,'select_gadget');wait_shot(2)
    check('dart marks target before death cleanup',lambda d:synced(d,1,lambda p:p['equipment']['trackingSeconds']>5))
    action(1,'damage');check('dead merc stops exposing tracking contact',lambda d:synced(d,1,lambda p:p['health']==0 and p['equipment']['trackingSeconds']==0) and all(all(not p['equipment']['trackingContacts'] for p in w['pawns']) for w in d['worlds']))
    action(2,'damage')
    check('remote respawn restores ammo and clears deployed camera',lambda d:synced(d,2,lambda p:p['health']==100 and p['equipment']['cameraAmmo']==3 and p['equipment']['trackingAmmo']==4 and p['equipment']['selectedGadget']=='StickyCamera' and not p['equipment']['cameraDeployed']),12)
    # Spend a camera, then verify that a round restart also restores it.
    time.sleep(.8);pad(2,'y')
    check('respawned launcher finishes drawing',lambda d:synced(d,2,lambda p:p['equipment']['weaponReady']))
    action(2,'place_vault');time.sleep(.6);pad(2,'gadget')
    check('camera spent before round reset',lambda d:synced(d,2,lambda p:p['equipment']['cameraAmmo']==2))
    action(0,'expire');check('round reaches results',lambda d:all(w['phase']==3 for w in d['worlds']))
    check('round restart replenishes every spy',lambda d:all(w['phase']==1 and all(p['equipment']['cameraAmmo']==3 and p['equipment']['trackingAmmo']==4 and p['equipment']['selectedGadget']=='StickyCamera' for p in w['pawns'] if p['spy']) for w in d['worlds']),15)
    print(json.dumps({'passed':len(results),'total':len(results)}),flush=True)
except Exception as error:
    results.append({'name':'gadget inventory acceptance failure','passed':False,'error':str(error)})
    Path('Saved/EquipmentQA/gadget-inventory.json').write_text(json.dumps(results,indent=2))
    print('FAIL',str(error),flush=True)
    raise
finally:
    stop();start(1);action(0,'automation_off')
