"""Actual solo gameplay inspection before returning to multiplayer review."""
from pathlib import Path
import json,time,shutil
from run_acceptance import *
D=Path('Art/Actions/Review');D.mkdir(exist_ok=True,parents=True)
def capture(name):
 result=action(0,'specialty_capture')
 if result!='Specialty viewport captured':raise RuntimeError(result)
 shutil.copyfile('Saved/SpecialtyQA/capture.png',D/name)
 (D/(name+'.json')).write_text(json.dumps(report(),indent=2))
stop();call(project_tool,'open_map',map_name='Warehouse');start(1);action(0,'place_open');action(0,'face_review_camera');time.sleep(1)
capture('spy-face-repaired.png');pad(0,'equipment');time.sleep(.5);capture('spy-goggles-down-repaired.png');pad(0,'equipment')
pad(0,'role');time.sleep(.7);pad(0,'inspect');wait_for(lambda d:local_pawn(d)['appearanceView'],3);action(0,'grip_review_camera');time.sleep(1);capture('merc-grip-repaired.png')
pad(0,'inspect');wait_for(lambda d:not local_pawn(d)['appearanceView'],3);action(0,'review_player_view');time.sleep(.7);capture('merc-first-person-repaired.png')
(D/'presentation-repaired.json').write_text(json.dumps(report(),indent=2));print('SOLO_PRESENTATION_CAPTURED',flush=True)
