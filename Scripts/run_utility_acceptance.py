"""Focused controller/replication checks for the replacement merc rifle."""
import time,json,shutil
from pathlib import Path
from run_acceptance import *
OUT=Path('Saved/UtilityRifleQA');OUT.mkdir(parents=True,exist_ok=True);checks=[]
def test(name,predicate,seconds=12):
 try:d=wait_for(predicate,seconds);checks.append({'name':name,'passed':True,'observed':d});print('PASS',name,flush=True)
 except Exception as e:checks.append({'name':name,'passed':False,'error':str(e)});raise
 finally:(OUT/'acceptance.json').write_text(json.dumps(checks,indent=2))
 return d
def capture(name,index=0):
 assert action(index,'specialty_capture')=='Specialty viewport captured';shutil.copyfile('Saved/SpecialtyQA/capture.png',OUT/(name+'.png'))
try:
 stop();call(project_tool,'open_map',map_name='Warehouse');start(1);pad(0,'role')
 test('solo merc loads original utility rifle and first-person arms',lambda d:not local_pawn(d)['spy'] and '/SK_MercUtility.' in local_pawn(d)['equipment']['weaponMesh'] and local_pawn(d)['equipment']['firstPersonArms'])
 test('both ready-pose hands align with the actual weapon grip sockets',lambda d:local_pawn(d)['equipment']['weaponReady'] and local_pawn(d)['equipment']['gripDistance']<2 and local_pawn(d)['equipment'].get('worldSupportDistance',999)<5 and local_pawn(d)['equipment'].get('viewSupportDistance',999)<5)
 capture('first-person');pad(0,'equipment');test('D-pad Up still controls replicated flashlight',lambda d:local_pawn(d)['flashlight']);pad(0,'equipment')
 action(0,'pad_lt_down');test('LT aims with support grip still aligned',lambda d:local_pawn(d)['aiming'] and local_pawn(d)['cameraFOV']<67 and local_pawn(d)['equipment']['viewSupportDistance']<5)
 capture('aiming');action(0,'pad_lt_up');pad(0,'y');test('Y holsters rifle and hides reticle',lambda d:local_pawn(d)['equipment']['weapon']==0 and not local_pawn(d)['equipment']['reticle'])
 time.sleep(.8);pad(0,'y');test('Y restores rifle and new reticle without toggling light',lambda d:local_pawn(d)['equipment']['weaponReady'] and local_pawn(d)['equipment']['reticle'] and not local_pawn(d)['flashlight'])
 pad(0,'gadget');test('RB grenade animation still spends shared stock',lambda d:local_pawn(d)['mercGrenades']==1 and any(g['thrown'] and not g['exploded'] for g in server(d)['grenades']))
 test('new ready grip recovers after grenade throw',lambda d:local_pawn(d)['equipment']['weaponReady'] and not local_pawn(d)['throwing'] and local_pawn(d)['equipment']['viewSupportDistance']<5)
 stop();start(4);test('four network worlds use the same rifle asset on both mercs',lambda d:len(d['worlds'])==4 and all(len(w['pawns'])==4 and all('/SK_MercUtility.' in p['equipment']['weaponMesh'] for p in w['pawns'] if not p['spy']) for w in d['worlds']),30)
 action(0,'takedown_rear');time.sleep(.8);action(0,'utility_review_camera');capture('third-person-grip')
 d=report();before=player(d,1)['lastAttackAt'];pad(1,'rt');test('remote merc fires an actual server-accepted shot with replacement rifle',lambda d:player(d,1)['lastAttackAt']>before)
 pad(1,'y');test('remote Y holster replicates to every client',lambda d:synced(d,1,lambda p:p['equipment']['weapon']==0 and not p['equipment']['reticle']))
 time.sleep(.8);pad(1,'y');test('remote re-equip restores grip on every client',lambda d:synced(d,1,lambda p:p['equipment']['weaponReady'] and p['equipment']['worldSupportDistance']<5))
 action(0,'network_lag');pad(1,'equipment');test('weapon light state converges with lag and loss',lambda d:synced(d,1,lambda p:p['flashlight']))
 action(0,'network_reset');print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
 action(0,'network_reset');stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
