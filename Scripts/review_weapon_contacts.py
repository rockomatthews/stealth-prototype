"""Record actual first/third-person weapon contacts with injected controller input."""
import json,time,shutil,subprocess,math
from pathlib import Path
from run_acceptance import *
OUT=Path('Saved/ContactQA/weapon-hand-fit-v4');OUT.mkdir(parents=True,exist_ok=True)
DEST=Path('Art/Actions/Review');DEST.mkdir(parents=True,exist_ok=True)
stop();call(project_tool,'open_map',map_name='Warehouse');start(1);pad(0,'role');action(0,'place_open');time.sleep(1)
wait_for(lambda d:local_pawn(d)['equipment']['weaponReady'])
action(0,'review_freeze');base=server(report())['serverTime'];samples=[];action(0,'review_slow')
try:
 for i in range(105):
  d=wait_for(lambda d:server(d)['serverTime']-base>=i/20,20)
  if i==10:action(0,'pad_lt_down')
  if i==35:action(0,'pad_lt_up')
  if i==40:action(0,'pad_rt_down')
  if i==45:action(0,'pad_rt_up')
  if i==55:
   pad(0,'inspect');action(0,'grip_review_camera')
  if i==80:
   # A second angle exposes the thumb and finger wrap hidden in the side view.
   yaw=math.atan2(-220,-40);pitch=math.atan2(-25,math.hypot(40,220))
   basis=[(math.cos(pitch)*math.cos(yaw),math.cos(pitch)*math.sin(yaw),math.sin(pitch)),(-math.sin(yaw),math.cos(yaw),0),(-math.sin(pitch)*math.cos(yaw),-math.sin(pitch)*math.sin(yaw),math.cos(pitch))]
   dot=lambda a,b:sum(x*y for x,y in zip(a,b))
   offset=[dot((140,-60,0),axis) for axis in basis];forward=[dot((-150,-160,-20),axis) for axis in basis]
   values={'RelativeLocation':dict(zip(['X','Y','Z'],offset)),'RelativeRotation':{'Pitch':math.degrees(math.atan2(forward[2],math.hypot(*forward[:2]))),'Yaw':math.degrees(math.atan2(forward[1],forward[0])),'Roll':0}}
   call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Game/Maps/UEDPIE_0_Warehouse.Warehouse:PersistentLevel.CameraActor_0.CameraComponent'},values=json.dumps(values))
  if action(0,'specialty_capture')!='Specialty viewport captured':raise RuntimeError('Gameplay capture failed')
  shutil.copyfile('Saved/SpecialtyQA/capture.png',OUT/f'frame-{i:03}.png');samples.append({'frame':i,'state':d})
  if i%25==0:print('WEAPON_FRAME',i,flush=True)
finally:action(0,'review_normal')
video=DEST/'weapon-hand-fit-v4-2026-11-10.mp4'
subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','20','-i',str(OUT/'frame-%03d.png'),'-vf','scale=1280:-2:flags=lanczos','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
(DEST/'weapon-hand-fit-v4-2026-11-10.json').write_text(json.dumps({'source':'Actual Unreal Warehouse viewport, injected controller actions, slowed game clock sampled at 20 fps; silent','samples':samples},indent=2))
print('RECORDED',video,flush=True)
