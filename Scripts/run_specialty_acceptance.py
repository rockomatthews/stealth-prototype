"""Actual four-client controller-input checks for specialty takedowns.
No direct success-state mutations: fixtures only place players/set test stock.
"""
import json,time,math
from pathlib import Path
from run_acceptance import *
OUT=Path('Saved/SpecialtyQA');OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def test(name,predicate,seconds=12):
 try:
  d=wait_for(predicate,seconds);checks.append({'name':name,'passed':True,'observed':d});print('PASS',name,flush=True)
 except Exception as e:
  checks.append({'name':name,'passed':False,'error':str(e)});raise
 finally:(OUT/'acceptance.json').write_text(json.dumps(checks,indent=2))
 return d
def paired(d):return synced(d,2,lambda p:p['captor']) and synced(d,1,lambda p:p['restrained'])
def clear(d):return synced(d,2,lambda p:not p['restrained']) and synced(d,1,lambda p:not p['restrained'])
def alive(d):return all(synced(d,i,lambda p:p['health']==100) for i in [1,2])
def owned(d,i):
 id=player(d,i)['playerId'];return next(p for w in d['worlds'] for p in w['pawns'] if p['local'] and p['playerId']==id)
def live(w):return [g for g in w['grenades'] if not g['exploded']]
def ready():
 test('participants alive with no stale hold/knockout/protection',lambda d:alive(d) and clear(d) and synced(d,1,lambda p:not p['knockedOut'] and not p['recoveryShield'] and not p['panicking']),25)
def grab(empty=False):
 action(0,'takedown_rear');action(1,'grenades_empty' if empty else 'grenades_full');time.sleep(.6);pad(2,'x');test('X rear grab established on all clients',paired)
def hold():action(2,'pad_rt_down');time.sleep(.65);action(2,'pad_rt_up')
try:
 stop();call(project_tool,'open_map',map_name='Warehouse');start(4)
 test('all four clients load the new paired clips',lambda d:len(d['worlds'])==4 and all(len(w['pawns'])==4 and all(p['grabClipCount']==8 for p in w['pawns']) for w in d['worlds']),30)
 grab();test('merc rifle stays drawn and uses the reduced body scale during neck hold',lambda d:synced(d,1,lambda p:p['equipment']['weapon']==3 and p['equipment']['equipAlpha']>.95 and abs(p['equipment']['rifleScale']-.75)<.01),3);pad(2,'rt');test('tap RT still selects quick neck snap',lambda d:synced(d,2,lambda p:p['finisher']==1),3)
 test('quick snap kills and closes automatic pair voice',lambda d:clear(d) and synced(d,1,lambda p:p['health']==0) and owned(d,1)['voice']['pairToken']==0)
 ready();grab(True);hold()
 test('held RT with no grenades mounts the five-second back choke',lambda d:paired(d) and synced(d,1,lambda p:p['chokeVictim'] and p['health']==100) and synced(d,2,lambda p:p['finisher']==2),3)
 before=player(report(),1);action(1,'pad_move_down');action(1,'pad_look_down');time.sleep(.65);action(1,'pad_move_up');action(1,'pad_look_up')
 test('merc walks and turns while carrying the spy',lambda d:paired(d) and math.dist([player(d,1)[k] for k in ['x','y']],[before[k] for k in ['x','y']])>30 and abs(player(d,1)['yaw']-before['yaw'])>15 and aligned(d,1) and aligned(d,2),3)
 action(1,'pad_lt_down');test('merc can aim his first-person carbine during choke',lambda d:owned(d,1)['aiming'] and owned(d,1)['equipment']['firstPersonWeapon'],2)
 before=player(report(),1)['lastAttackAt'];pad(1,'rt');action(1,'pad_lt_up')
 test('merc RT fires a real server-approved shot during choke',lambda d:paired(d) and player(d,1)['lastAttackAt']>before and synced(d,2,lambda p:p['health']==100),2)
 test('automatic private grab voice stays open during back choke',lambda d:paired(d) and all(owned(d,i)['voice']['desiredChannel']=='Grab' for i in [1,2]),2)
 test('five-second strangulation kills merc and retains a visible collapse',lambda d:clear(d) and synced(d,1,lambda p:p['health']==0 and p['chokeCorpse']) and owned(d,1)['voice']['pairToken']==0,8)
 test('choke ends with forward merc collapse and spy disengage clip',lambda d:synced(d,1,lambda p:p['chokeCorpse'] and p['forwardCollapse']) and synced(d,2,lambda p:p['chokeExit'] and 'SpyChokeExit' in p['animationAsset']),2)
 ready();grab(True);hold();test('second choke starts',lambda d:player(d,1)['chokeVictim'],3)
 # Refill only to exercise RB during a choke whose selection was already empty.
 action(1,'grenades_full');pad(1,'gadget')
 test('choked merc can RB throw using the same finite supply',lambda d:paired(d) and synced(d,1,lambda p:p['mercGrenades']==1) and all(any(g['thrown'] for g in live(w)) for w in d['worlds']),3)
 action(2,'wound');test('damage to rider interrupts choke and closes pair voice',lambda d:clear(d) and synced(d,2,lambda p:p['health']==90) and synced(d,1,lambda p:p['health']==100) and owned(d,2)['voice']['pairToken']==0)
 time.sleep(5.2);test('interrupted choke has no delayed knockout',lambda d:not player(d,1)['knockedOut'])
 action(2,'damage');ready();grab();hold()
 test('held RT with shared grenade stock selects waistband plant',lambda d:paired(d) and synced(d,2,lambda p:p['finisher']==3),3)
 test('steal spends exactly one shared merc grenade',lambda d:synced(d,1,lambda p:p['mercGrenades']==1) and all(len(live(w))==1 for w in d['worlds']),3)
 test('grenade is concealed at waist after pin pull',lambda d:all(any(g['planted'] and .85<=g['age']<2.9 for g in live(w)) for w in d['worlds']),3)
 d=test('shove releases spy while merc panics with a live grenade',lambda d:clear(d) and synced(d,1,lambda p:p['panicking'] and p['health']==100) and all(any(g['planted'] and g['age']<g['fuse'] for g in live(w)) for w in d['worlds']),3)
 before=player(d,2);action(2,'pad_back_down');time.sleep(.35);action(2,'pad_back_up')
 test('spy has movement restored before detonation',lambda d:synced(d,2,lambda p:p['maxSpeed']>100 and not p['equipment']['stunned']) and player(d,2)['x']<before['x']-15,2)
 test('planted grenade explodes at waist and inevitably kills merc',lambda d:synced(d,1,lambda p:p['health']==0) and all(not live(w) for w in d['worlds']),6)
 test('planted blast renders textured merc body fragments on every client',lambda d:all(any(g['exploded'] and g['bodyFragments']>=10 and g['clouds']==36 and g['fireSprites']==14 and g['bloodDrops']==64 for g in w['grenades']) for w in d['worlds']),3)
 test('spy survives outside blast radius after shove',lambda d:synced(d,2,lambda p:p['health']==100))
 ready();grab();hold();test('next grenade has its pin pulled',lambda d:any(g['age']>.1 for g in live(server(d))),3)
 action(2,'wound');test('interrupt after pin pull closes the hold',clear)
 test('live grenade survives interruption and finishes its fuse',lambda d:all(not live(w) for w in d['worlds']),8)
 ready();grab();hold();test('grenade is planted before captor-death case',lambda d:all(any(g['planted'] for g in live(w)) for w in d['worlds']),4)
 action(2,'damage');test('captor death releases hold but leaves merc panicking',lambda d:clear(d) and synced(d,2,lambda p:p['health']==0) and synced(d,1,lambda p:p['health']==100 and p['panicking']),3)
 test('planted grenade still kills merc after captor dies',lambda d:synced(d,1,lambda p:p['health']==0) and all(not live(w) for w in d['worlds']),6)
 # Each network group starts a fresh competitive round, avoiding timer exhaustion.
 stop();start(4);test('fresh warehouse round for network stress',lambda d:len(d['worlds'])==4 and all(w['phase']==1 for w in d['worlds']),30)
 action(0,'network_lag');grab(True);hold()
 test('back choke is replicated under 100ms lag and 2 percent loss',lambda d:synced(d,1,lambda p:p['chokeVictim']) and synced(d,2,lambda p:p['finisher']==2),4)
 test('five-second lethal strangulation converges under lag/loss',lambda d:clear(d) and synced(d,1,lambda p:p['chokeCorpse'] and p['health']==0),10)
 action(0,'network_reset');ready();grab();hold();test('final planted grenade exists before round cancellation',lambda d:any(g['planted'] for g in live(server(d))),4);action(0,'expire')
 test('round reset clears explosives, panic and all hold voice',lambda d:all(w['phase']==1 and not live(w) for w in d['worlds']) and clear(d) and synced(d,1,lambda p:p['health']==100 and not p['panicking'] and p['mercGrenades']==2) and all(owned(d,i)['voice']['pairToken']==0 for i in [1,2]),20)
 print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
 try:action(0,'network_reset');action(0,'review_normal')
 finally:stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
