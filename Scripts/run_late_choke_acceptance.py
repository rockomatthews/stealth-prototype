"""Rescue in the last 40 ms must not produce a death or ghost dismount."""
import time,json
from pathlib import Path
from run_acceptance import *
checks=[]
def verify(name,predicate,seconds=10):
 d=wait_for(predicate,seconds);checks.append({'name':name,'passed':True,'observed':d});print('PASS',name,flush=True);return d
def pair_voice_closed(d):
 for index in [1,2]:
  identity=player(d,index)['playerId']
  owned=next(p for w in d['worlds'] for p in w['pawns'] if p['local'] and p['playerId']==identity)
  if owned['voice']['pairToken']!=0:return False
 return True
try:
 stop();call(project_tool,'open_map',map_name='Warehouse');start(4)
 action(0,'takedown_rear');action(1,'grenades_empty');time.sleep(.6);pad(2,'x');wait_for(lambda d:player(d,2)['captor']);action(2,'pad_rt_down');time.sleep(.65);action(2,'pad_rt_up')
 wait_for(lambda d:player(d,2)['finishElapsed']>=4.05,7);action(0,'review_slow')
 end=time.monotonic()+12
 while time.monotonic()<end:
  d=report()
  if player(d,2)['finishElapsed']>=4.96:break
  time.sleep(.05)
 action(0,'review_freeze');d=report();elapsed=player(d,2)['finishElapsed']
 if not 4.95<=elapsed<5:raise RuntimeError('Late-interrupt fixture missed its timing: '+str(elapsed))
 print('INTERRUPT_TIME',elapsed,flush=True);action(2,'wound')
 verify('last-moment rescue clears both grab states and voice',lambda d:synced(d,2,lambda p:not p['restrained'] and p['health']==90) and synced(d,1,lambda p:not p['restrained'] and p['health']==100) and pair_voice_closed(d))
 action(0,'review_normal');time.sleep(1.1)
 verify('rescued merc remains alive beyond the original five-second finish',lambda d:synced(d,1,lambda p:p['health']==100 and not p['chokeCorpse']))
 verify('interrupted spy never plays the successful choke dismount',lambda d:synced(d,2,lambda p:not p['chokeExit'] and not p['equipment']['stunned']))
 Path('Saved/SpecialtyQA/late-interrupt.json').write_text(json.dumps({'elapsed':elapsed,'checks':checks},indent=2));print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
 try:action(0,'review_normal')
 finally:stop();start(1);action(0,'automation_off')
