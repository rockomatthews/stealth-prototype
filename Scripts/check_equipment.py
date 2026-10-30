"""Focused post-import checks; preserves the full acceptance suite's report."""
import json,time
from pathlib import Path
from run_acceptance import start,stop,pad,action,report,local_pawn,wait_for,synced
P=Path(__file__).resolve().parents[1];results=[]
def verify(name,predicate,seconds=12):
 try:
  state=wait_for(predicate,seconds);results.append({'name':name,'passed':True,'observed':state});print('PASS',name,flush=True)
 except Exception as error:
  results.append({'name':name,'passed':False,'error':str(error)});print('FAIL',name,str(error),flush=True)
 (P/'Saved/EquipmentQA/focused.json').write_text(json.dumps(results,indent=2))
stop();start(1)
verify('raised goggle housing is above its lowered position',lambda d:local_pawn(d)['equipment']['goggleCenterHeight']>4 and not local_pawn(d)['equipment']['goggleLights'])
pad(0,'equipment')
verify('lowered goggles show both green lenses',lambda d:local_pawn(d)['equipment']['goggleLights'] and abs(local_pawn(d)['gogglePitch'])<3)
pad(0,'equipment');pad(0,'y')
verify('launcher draw produces reticle and a human-scale animated pose',lambda d:local_pawn(d)['equipment']['weaponReady'] and local_pawn(d)['equipment']['reticle'] and local_pawn(d)['headBoneScale']<1.1)
pad(0,'role');time.sleep(.9)
verify('merc first-person arms and carbine share the grip',lambda d:local_pawn(d)['equipment']['firstPersonArms'] and local_pawn(d)['equipment']['firstPersonWeapon'] and local_pawn(d)['equipment']['gripDistance']<2)
action(0,'place_open');time.sleep(.6);pad(0,'a')
verify('merc jumps',lambda d:local_pawn(d)['z']>110 and local_pawn(d)['traversal']==0)
verify('merc lands',lambda d:local_pawn(d)['z']<100)
action(0,'place_ledge');time.sleep(.6);action(0,'traverse');time.sleep(.4)
verify('merc cannot grapple',lambda d:local_pawn(d)['z']<100 and local_pawn(d)['traversal']==0)
stop();start(4)
verify('four worlds start',lambda d:len(d['worlds'])==4 and all(len(w['pawns'])==4 and w['phase']==1 for w in d['worlds']),25)
pad(2,'y')
verify('remote launcher ready',lambda d:synced(d,2,lambda p:p['equipment']['weapon']==1 and p['equipment']['weaponReady']))
action(0,'duel_blocked');time.sleep(1);pad(2,'rt');time.sleep(.4)
verify('cover blocks the revised launcher muzzle trace',lambda d:synced(d,1,lambda p:not p['equipment']['stunned']))
action(0,'duel_open');time.sleep(1);pad(2,'rt')
verify('revised launcher pose tases merc',lambda d:synced(d,1,lambda p:p['equipment']['stunned'] and p['health']==100))
verify('merc recovers',lambda d:synced(d,1,lambda p:not p['equipment']['stunned']),8)
pad(1,'rt')
verify('revised carbine pose shoots correctly',lambda d:synced(d,2,lambda p:p['health']==66))
stop();start(1);action(0,'automation_off')
print(json.dumps({'passed':sum(r['passed'] for r in results),'total':len(results)}),flush=True)
raise SystemExit(0 if all(r['passed'] for r in results) else 1)
