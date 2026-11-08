"""Observe supported mantle geometry and interruption in solo and networked PIE."""
import json,time,math
from pathlib import Path
from run_acceptance import *
OUT=Path('Saved/VentEntryQA');OUT.mkdir(parents=True,exist_ok=True);results=[]
def passed(name,data):
 results.append({'name':name,'passed':True,'observed':data});(OUT/'acceptance.json').write_text(json.dumps(results,indent=2));print('PASS',name,flush=True)
def expect(name,predicate,seconds=12):
 try:d=wait_for(predicate,seconds)
 except Exception as e:(OUT/'failure.txt').write_text(str(e));raise AssertionError(name+'; see Saved/VentEntryQA/failure.txt') from None
 passed(name,d);return d
def run_entry(index,network=False):
 action(index,'warehouse_rope');time.sleep(.6);pad(index,'a');expect('remote rope mount' if network else 'solo rope mount',lambda d:synced(d,index,lambda p:p['onRope']) if network else local_pawn(d)['onRope'])
 if network:action(0,'network_lag')
 action(index,'pad_move_down');expect('mantle starts from below the vent floor',lambda d:player(d,index)['ventEntry'] if network else local_pawn(d)['ventEntry'],25);action(index,'pad_move_up')
 samples=[];end=time.monotonic()+15
 while time.monotonic()<end:
  d=report();p=player(d,index) if network else local_pawn(d)
  if not p['ventEntry']:break
  samples.append(d);time.sleep(.035)
 (OUT/('remote-samples.json' if network else 'solo-samples.json')).write_text(json.dumps(samples,indent=2))
 assert len(samples)>15,'Insufficient animation observations';return samples

def validate(samples,index,network):
 pawn=lambda d:player(d,index) if network else local_pawn(d)
 observed=[pawn(d) for d in samples]
 assert max(p['ventEntryTime'] for p in observed)>3.,'Mantle skipped its authored phases'
 passed('full reach/pull/knee/trailing-leg timeline observed',{'samples':len(samples),'last_phase':max(p['ventEntryTime'] for p in observed)})
 assert all(p['crouched'] and p['capsuleHalfHeight']<43 for p in observed);passed('capsule stays crouched throughout mantle',True)
 assert min(p['bodyPelvisZ'] for p in observed if p['ventEntryTime']<.6)>710;passed('collision crouch never drops the rendered body',True)
 # Contact quality is assessed on the actual owning client's rendered mesh.
 # The server can receive a movement packet between its animation refreshes.
 if network:
  identity=observed[0]['playerId']
  observed=[next(p for w in d['worlds'] for p in w['pawns'] if p['playerId']==identity and p['local']) for d in samples]
 errors=[]
 for p in observed:
  t=p['animationTime']
  for field,a,b,y,x in [('rightPalm',.65,1.65,-1400,-2118),('leftPalm',.65,1.3,-1400,-2082),('leftPalm',1.85,2.1,-1345,-2082),('rightPalm',2.3,3.1,-1295,-2118)]:
   if a<=t<=b:
    q=p[field];errors.append(math.sqrt((q['x']-x)**2+(q['y']-y)**2+(q['z']-790)**2))
 assert errors and max(errors)<10,('Authoritative palms drift from support',max(errors));passed('planted palms remain on their physical supports',{'max_error_cm':max(errors)})
 knees=[p['rightKnee'] for p in observed if 1.45<p['animationTime']<2.05];assert knees and all(abs(k['z']-790)<8 and abs(k['y']+1392)<8 for k in knees);passed('right knee bears weight on lip before trailing leg enters',knees)
 velocities=[]
 for a,b in zip(observed,observed[1:]):
  dt=b['animationTime']-a['animationTime']
  if dt>.01:velocities.append(abs(b['bodyPelvisZ']-a['bodyPelvisZ'])/dt)
 assert max(velocities)<350,('Pelvis pose snapped',max(velocities));passed('rendered pelvis moves continuously instead of snapping prone',{'max_vertical_speed_cm_s':max(velocities)})
 if network:
  for d in samples:
   identity=player(d,index)['playerId']
   assert all(p['crouched'] and p['capsuleHalfHeight']<43 for w in d['worlds'] for p in w['pawns'] if p['playerId']==identity and p['ventEntry'] and p['ventEntryTime']>.2)
  passed('all clients preserve mantle crouch under latency and loss',True)

try:
 stop();call(project_tool,'open_map',map_name='Warehouse');start(1);s=run_entry(0);validate(s,0,False)
 expect('solo settles into dedicated crawl idle',lambda d:local_pawn(d)['inVent'] and 'SpyVentIdle' in local_pawn(d)['animationAsset'] and local_pawn(d)['crouched'])
 a=local_pawn(report());time.sleep(.6);b=local_pawn(report());assert math.hypot(a['x']-b['x'],a['y']-b['y'])<3;passed('neutral stick does not inherit mantle exit velocity',{'movement_cm':math.hypot(a['x']-b['x'],a['y']-b['y'])})
 stop();start(4);s=run_entry(2,True);validate(s,2,True)
 expect('remote crawl handoff converges on every client',lambda d:synced(d,2,lambda p:p['inVent'] and not p['onRope'] and p['crouched'] and 'SpyVentIdle' in p['animationAsset']) and aligned(d,2),15);action(0,'network_reset')
 action(2,'warehouse_rope');time.sleep(.6);pad(2,'a');action(2,'pad_move_down');wait_for(lambda d:player(d,2)['ventEntryTime']>.8,20);action(2,'pad_move_up');pad(2,'b')
 expect('B interrupts mantle and clears replicated traversal',lambda d:synced(d,2,lambda p:not p['ventEntry'] and not p['onRope']))
 expect('interrupted spy lands safely and remains alive',lambda d:synced(d,2,lambda p:p['z']<100 and p['health']==100),10)
 action(2,'warehouse_rope');time.sleep(.6);pad(2,'a');action(2,'pad_move_down');wait_for(lambda d:player(d,2)['ventEntryTime']>1.5,20);action(2,'pad_move_up');action(2,'damage')
 expect('death during knee plant clears mantle on all clients',lambda d:synced(d,2,lambda p:p['health']==0 and not p['ventEntry'] and not p['onRope']))
 expect('spy respawns with normal movement after mantle death',lambda d:synced(d,2,lambda p:p['health']==100 and p['traversal']==0 and not p['crouched']),15)
 print(json.dumps({'passed':len(results),'total':len(results)}),flush=True)
finally:
 action(0,'review_normal');stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
