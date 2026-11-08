"""Controller-driven sticky camera tests across four real PIE network worlds."""
import json,time
from pathlib import Path
from run_acceptance import *
results=[]
def owned(data,index=2):
    identity=player(data,index)['playerId']
    return next(p for w in data['worlds'] for p in w['pawns'] if p['playerId']==identity and p['local'])
def equipment(data):return owned(data)['equipment']
def test(name,predicate,seconds=12):
    observed=wait_for(predicate,seconds);results.append({'name':name,'passed':True,'observed':observed})
    Path('Saved/EquipmentQA/camera-controls.json').write_text(json.dumps(results,indent=2));print('PASS',name,flush=True)

def hold(key,seconds):
    action(2,'pad_'+key+'_down');time.sleep(seconds);action(2,'pad_'+key+'_up')
def deploy():
    action(2,'place_camera_wall');time.sleep(1);pad(2,'gadget')
    test('remote camera placed with original audio ready',lambda d:synced(d,2,lambda p:p['equipment']['cameraDeployed'] and p['equipment']['cameraAudioReady']))
    action(2,'place_open');time.sleep(.4)
try:
    stop();call(project_tool,'open_map',map_name='Prototype');start(4)
    test('network round ready',lambda d:len(d['worlds'])==4 and all(w['phase']==1 and len(w['pawns'])==4 for w in d['worlds']),25)
    pad(2,'y');test('launcher drawn',lambda d:synced(d,2,lambda p:p['equipment']['weaponReady']))
    deploy()
    action(2,'camera_noise_rpc');action(2,'camera_gas_rpc');time.sleep(.5)
    test('server rejects camera actions outside camera viewing',lambda d:synced(d,2,lambda p:p['equipment']['noiseCues']==0 and p['equipment']['gasAvailable']))
    action(1,'foreign_camera_rpc');time.sleep(.5)
    test('merc cannot view or gas from another players camera',lambda d:synced(d,2,lambda p:p['equipment']['gasAvailable'] and p['equipment']['gasCues']==0) and not player(d,1)['equipment']['serverViewingCamera'])
    pad(2,'camera')
    test('LB opens feed and server records owned camera view',lambda d:equipment(d)['cameraView'] and player(d,2)['equipment']['serverViewingCamera'])
    baseline=owned(report());hold('look',.4)
    test('right stick pans camera without turning body',lambda d:equipment(d)['stickyYaw']>20 and abs(owned(d)['viewYaw']-baseline['viewYaw'])<1)
    hold('look',1.1);test('camera pan clamps at mount limit',lambda d:abs(equipment(d)['stickyYaw']-85)<.1)
    hold('look_pitch',1.2);test('camera tilt clamps at mount limit',lambda d:abs(equipment(d)['stickyPitch']+60)<.1)
    hold('lt',1.7);test('LT zooms to narrow field of view',lambda d:abs(equipment(d)['stickyFOV']-30)<.2 and not owned(d)['aiming'])
    hold('rt',1.7);test('RT zooms out without firing or spending ammo',lambda d:abs(equipment(d)['stickyFOV']-85)<.2 and equipment(d)['cameraAmmo']==2 and equipment(d)['trackingAmmo']==4)
    hold('move',.5);test('camera view blocks character movement',lambda d:abs(owned(d)['x']-baseline['x'])<2 and abs(owned(d)['y']-baseline['y'])<2)
    pad(2,'equipment');test('Up toggles camera NV without lowering body goggles',lambda d:equipment(d)['stickyNV'] and not owned(d)['nightvision'])
    pad(2,'equipment');test('camera NV toggles off',lambda d:not equipment(d)['stickyNV'])
    pad(2,'x');test('X emits camera distraction cue on all clients',lambda d:synced(d,2,lambda p:p['equipment']['noiseCues']==1 and p['equipment']['lastNoiseAt']>=0))
    noise_time=equipment(report())['lastNoiseAt'];pad(2,'x');time.sleep(.3)
    test('speaker cooldown rejects repeated noise',lambda d:synced(d,2,lambda p:p['equipment']['noiseCues']==1 and p['equipment']['lastNoiseAt']==noise_time))
    test('camera noise does not hack terminal or spend gadget rounds',lambda d:all(w['hack']==0 for w in d['worlds']) and equipment(d)['cameraAmmo']==2 and equipment(d)['trackingAmmo']==4)
    action(0,'camera_behind');time.sleep(.5);pad(2,'b')
    test('B releases replicated visible single-use gas',lambda d:synced(d,2,lambda p:not p['equipment']['gasAvailable'] and p['equipment']['gasCues']==1 and p['equipment']['gasVisible']))
    test('solid cover protects nearby merc from gas',lambda d:synced(d,1,lambda p:not p['equipment']['stunned'] and p['health']==100))
    test('gas does not harm spies near the camera',lambda d:synced(d,0,lambda p:not p['equipment']['stunned'] and p['health']==100))
    pad(2,'b');time.sleep(.3);test('empty gas cannot fire twice',lambda d:synced(d,2,lambda p:p['equipment']['gasCues']==1 and p['equipment']['cameraAmmo']==2))
    pad(2,'camera');test('LB returns to player and clears server view state',lambda d:not equipment(d)['cameraView'] and not player(d,2)['equipment']['serverViewingCamera'])
    time.sleep(.9);deploy();test('replacement camera has fresh one-shot gas',lambda d:synced(d,2,lambda p:p['equipment']['cameraAmmo']==1 and p['equipment']['gasAvailable']))
    action(0,'camera_front');time.sleep(.5);action(0,'network_lag');pad(2,'camera');pad(2,'x')
    test('noise replicates under latency and packet loss',lambda d:synced(d,2,lambda p:p['equipment']['noiseCues']==1),20)
    pad(2,'b');test('camera gas stuns exposed merc under latency without damage',lambda d:synced(d,1,lambda p:p['equipment']['stunned'] and p['health']==100),20)
    test('gas state agrees on all clients under latency',lambda d:synced(d,2,lambda p:not p['equipment']['gasAvailable'] and p['equipment']['gasCues']==1),20)
    pad(1,'rt');pad(1,'a');time.sleep(.3)
    test('gassed merc cannot shoot or jump',lambda d:synced(d,1,lambda p:p['z']<105) and synced(d,2,lambda p:p['health']==100))
    test('merc recovers from camera gas',lambda d:synced(d,1,lambda p:not p['equipment']['stunned']),10)
    action(0,'network_reset');pad(2,'y')
    test('Y only holsters launcher and exits camera feed',lambda d:synced(d,2,lambda p:p['equipment']['weapon']==0 and p['equipment']['cameraAmmo']==1) and not equipment(d)['cameraView'])
    time.sleep(.8);pad(2,'y');test('Y redraws launcher',lambda d:synced(d,2,lambda p:p['equipment']['weaponReady']))
    pad(2,'camera');test('camera feed can reopen',lambda d:equipment(d)['cameraView'])
    action(2,'expire_camera');test('camera expiry safely exits view',lambda d:not equipment(d)['cameraView'] and synced(d,2,lambda p:not p['equipment']['cameraDeployed']))
    time.sleep(.9);deploy();pad(2,'camera');test('last camera can be viewed before death',lambda d:equipment(d)['cameraView'])
    action(2,'damage');test('death exits camera and destroys owned equipment',lambda d:synced(d,2,lambda p:p['health']==0 and not p['equipment']['cameraDeployed']) and not equipment(d)['cameraView'])
    test('respawn restores camera supplies after view cleanup',lambda d:synced(d,2,lambda p:p['health']==100 and p['equipment']['cameraAmmo']==3 and not p['equipment']['cameraDeployed']),12)
    print(json.dumps({'passed':len(results),'total':len(results)}),flush=True)
finally:
    stop();start(1);action(0,'automation_off')
