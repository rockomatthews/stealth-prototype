"""Capture neck hold through recovery/blast from actual four-client gameplay.
The clock, controller inputs and every raw viewport frame are recorded together.
"""
import argparse,json,time,shutil,subprocess
from pathlib import Path
from run_acceptance import *
parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['choke','grenade']);args=parser.parse_args()
OUT=Path('Saved/ContactQA')/(args.kind+'-hand-fit-v4');OUT.mkdir(parents=True,exist_ok=True)
DEST=Path('Art/Actions/Review');DEST.mkdir(parents=True,exist_ok=True)
stop();call(project_tool,'open_map',map_name='Warehouse')
call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},values=json.dumps({'PlayNumberOfClients':4,'RunUnderOneProcess':True,'PlayNetMode':'PIE_ListenServer','NewWindowWidth':960,'NewWindowHeight':540,'ClientWindowWidth':320,'ClientWindowHeight':180}))
call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InEditorFloating','warmupSeconds':2});action(0,'automation_on')
wait_for(lambda d:len(d['worlds'])==4 and len(server(d)['pawns'])==4,30)
action(0,'takedown_rear');action(1,'grenades_empty' if args.kind=='choke' else 'grenades_full');action(0,'specialty_review_camera');time.sleep(.6);pad(2,'x');wait_for(lambda d:player(d,2)['captor'],10)
camera={'refPath':'/Game/Maps/UEDPIE_0_Warehouse.Warehouse:PersistentLevel.CameraActor_0.CameraComponent'}
def framing(close):
 result=call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance=camera,values=json.dumps({'FieldOfView':38 if close else 60,'RelativeLocation':{'X':0,'Y':0,'Z':45 if close else 0}}))
 if not result:raise RuntimeError('Review camera framing failed')
framing(True)
action(0,'review_freeze');d=report();base=server(d)['serverTime'];samples=[]
action(0,'review_slow')
duration=8.4 if args.kind=='choke' else 7.0
try:
 for i in range(round(duration*20)):
  target=i/20
  d=wait_for(lambda d:server(d)['serverTime']-base>=target,20)
  if i==12:action(2,'pad_rt_down')
  if i==25:action(2,'pad_rt_up')
  if i==(26 if args.kind=='choke' else 74):framing(False)
  if args.kind=='choke':
   if i==36:action(1,'pad_move_down');action(1,'pad_lt_down')
   if i==48:action(1,'pad_move_up');pad(1,'rt');action(1,'pad_lt_up')
  elif i==81:action(2,'pad_back_down')
  elif i==94:action(2,'pad_back_up')
  if action(0,'specialty_capture')!='Specialty viewport captured':raise RuntimeError('Gameplay viewport capture failed')
  frame=OUT/f'frame-{i:03}.png';shutil.copyfile(Path('Saved/SpecialtyQA/capture.png'),frame)
  samples.append({'frame':i,'time':server(d)['serverTime']-base,'spy':player(d,2),'merc':player(d,1),'grenades':server(d)['grenades']})
  if i in [8,40,64,92,125,140]:shutil.copyfile(frame,DEST/(args.kind+f'-hand-fit-v4-{i:03}.png'))
  if i%20==0:print('FRAME',i,'TIME',samples[-1]['time'],flush=True)
finally:action(0,'review_normal')
video=DEST/('warehouse-'+args.kind+'-hand-fit-v4-2026-11-10.mp4')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','20','-i',str(OUT/'frame-%03d.png'),'-vf','scale=1280:-2:flags=lanczos','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
(DEST/(args.kind+'-hand-fit-v4-2026-11-10.json')).write_text(json.dumps({'source':'Unmodified actual Unreal Warehouse gameplay viewport; four local networked clients; slowed gameplay captured at sampled clock intervals','fps':20,'samples':samples},indent=2));print('RECORDED',video,flush=True)
