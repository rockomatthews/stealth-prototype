"""Validate the retail manual's dual-use Spy Bullet behavior through network inputs."""
import json,time
from pathlib import Path
from run_acceptance import *
results=[]
def test(name,predicate,seconds=12):
    observed=wait_for(predicate,seconds);results.append({'name':name,'passed':True,'observed':observed})
    Path('Saved/EquipmentQA/spy-bullet.json').write_text(json.dumps(results,indent=2));print('PASS',name,flush=True)
try:
    stop();start(4)
    test('network match ready',lambda d:len(d['worlds'])==4 and all(w['phase']==1 and len(w['pawns'])==4 for w in d['worlds']),25)
    test('unmarked merc does not appear on radar',lambda d:synced(d,1,lambda p:not p['equipment']['onSpyRadar']))
    pad(2,'select_gadget');pad(2,'y');test('remote spy equips Spy Bullet payload',lambda d:synced(d,2,lambda p:p['equipment']['weaponReady'] and p['equipment']['selectedGadget']=='TrackingDart'))
    action(0,'network_lag');action(0,'duel_blocked');time.sleep(1);pad(2,'gadget')
    test('wall hit places replicated proximity sensor and spends one bullet',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==1 and p['equipment']['trackingAmmo']==3),20)
    test('wall sensor detects nearby merc without attaching tag or dealing damage',lambda d:synced(d,1,lambda p:p['equipment']['onSpyRadar'] and p['equipment']['trackingSeconds']==0 and p['health']==100),20)
    test('sensor contact shared with spies only',lambda d:all(all(len(p['equipment']['trackingContacts'])==(1 if p['spy'] else 0) for p in w['pawns']) for w in d['worlds'])),
    action(0,'sensor_exit');test('merc leaving sensor range disappears',lambda d:synced(d,1,lambda p:not p['equipment']['onSpyRadar']),20)
    action(0,'sensor_return');test('merc reentering range reappears',lambda d:synced(d,1,lambda p:p['equipment']['onSpyRadar']),20)
    action(0,'expire_sensors');test('expired sensor removes its contact',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==0) and synced(d,1,lambda p:not p['equipment']['onSpyRadar']),20)
    action(0,'network_reset');action(0,'duel_open');time.sleep(1);pad(2,'gadget')
    test('direct hit marks merc on radar with no damage or stun',lambda d:synced(d,1,lambda p:p['equipment']['trackingSeconds']>7 and p['equipment']['onSpyRadar'] and p['health']==100 and not p['equipment']['stunned']))
    test('attached bullet creates no wall sensor',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==0 and p['equipment']['trackingAmmo']==2))
    test('attached tag expires off radar',lambda d:synced(d,1,lambda p:p['equipment']['trackingSeconds']==0 and not p['equipment']['onSpyRadar']),18)
    action(0,'duel_blocked');time.sleep(1);pad(2,'gadget');test('second sensor placed for cleanup',lambda d:synced(d,2,lambda p:p['equipment']['sensorCount']==1))
    action(2,'damage');test('owner death removes sensors from all clients',lambda d:synced(d,2,lambda p:p['health']==0 and p['equipment']['sensorCount']==0))
    test('respawn restores Spy Bullet supplies',lambda d:synced(d,2,lambda p:p['health']==100 and p['equipment']['trackingAmmo']==4),12)
    print(json.dumps({'passed':len(results),'total':len(results)}),flush=True)
finally:
    stop();start(1);action(0,'automation_off')
