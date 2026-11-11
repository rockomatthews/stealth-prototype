"""Quiet movement and directional detection: real controller inputs, four clients."""
import time,json,math
from pathlib import Path
from run_acceptance import *
checks=[];OUT=Path('Saved/UtilityRifleQA')
def merc_cues(d):return [p['noiseAge'] for w in d['worlds'] for p in w['pawns'] if p['local'] and not p['spy']]
def quiet(d,age):return len(merc_cues(d))==2 and all(a>age for a in merc_cues(d))
def test(name,predicate,seconds=12):
 try:d=wait_for(predicate,seconds);checks.append({'name':name,'passed':True});print('PASS',name,flush=True)
 except Exception as e:checks.append({'name':name,'passed':False,'error':str(e)});raise
 finally:(OUT/'quiet-movement.json').write_text(json.dumps(checks,indent=2))
 return d
try:
 stop();call(project_tool,'open_map',map_name='Warehouse');start(4);test('four-player warehouse round active',lambda d:len(d['worlds'])==4 and server(d)['phase']==1,30)
 action(0,'warehouse_noise');time.sleep(.8);pad(2,'b');test('spy is crouched for silent movement',lambda d:player(d,2)['crouched'])
 old=player(report(),2).copy();action(2,'pad_move_down');time.sleep(1.2);action(2,'pad_move_up')
 test('moving crouched spy creates no merc movement cue',lambda d:math.hypot(player(d,2)['x']-old['x'],player(d,2)['y']-old['y'])>20 and quiet(d,5))
 pad(2,'b');test('spy stands for analog sneak test',lambda d:not player(d,2)['crouched'])
 old=player(report(),2).copy();action(2,'pad_sneak_down');time.sleep(1.4);action(2,'pad_sneak_up')
 test('low analog-stick movement is silent but really moves',lambda d:math.hypot(player(d,2)['x']-old['x'],player(d,2)['y']-old['y'])>10 and quiet(d,5))
 action(2,'pad_back_down');test('fast spy movement creates an actual merc directional cue',lambda d:any(a<.7 for a in merc_cues(d)),4);action(2,'pad_back_up')
 test('movement cue expires after spy stops',lambda d:quiet(d,1.))
 action(0,'network_lag');pad(2,'b');test('crouch converges under lag',lambda d:synced(d,2,lambda p:p['crouched']))
 old=min(merc_cues(report()));action(2,'pad_move_down');time.sleep(.8);action(2,'pad_move_up')
 test('quiet crouching does not renew detector under lag/loss',lambda d:quiet(d,old+.4))
 print(json.dumps({'passed':len(checks),'total':len(checks)}),flush=True)
finally:
 action(2,'pad_move_up');action(2,'pad_back_up');action(2,'pad_sneak_up');action(0,'network_reset');stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'automation_off')
