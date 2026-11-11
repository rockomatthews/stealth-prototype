"""Stage actual networked warehouse takedowns for inspection and video capture."""
import argparse,base64,json,time,subprocess,shutil
from pathlib import Path
from run_acceptance import *
parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['choke','grenade']);parser.add_argument('--setup',action='store_true');parser.add_argument('--record',action='store_true');args=parser.parse_args()
OUT=Path('Saved/SpecialtyQA');DEST=Path('Art/Actions/Review');DEST.mkdir(parents=True,exist_ok=True)
def elapsed(d):
 p=player(d,2)
 if p['finisher']:return p['finishElapsed']
 if args.kind=='grenade':
  gs=server(d)['grenades']
  if gs:return max(g['age'] for g in gs)+1.05
 else:
  m=player(d,1)
  if m['knockedOut']:return 11.-m['knockoutRemaining']
 return 0.
def capture(name):
 assert action(0,'specialty_capture')=='Specialty viewport captured'
 shutil.copyfile(OUT/'capture.png',name)
if args.setup:
 stop();call(project_tool,'open_map',map_name='Warehouse')
 call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
 call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},values=json.dumps({'PlayNumberOfClients':4,'RunUnderOneProcess':True,'PlayNetMode':'PIE_ListenServer','ClientWindowWidth':640,'ClientWindowHeight':360}))
 call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2});action(0,'automation_on');wait_for(lambda d:len(d['worlds'])==4 and len(server(d)['pawns'])==4,30)
 action(0,'takedown_rear');action(1,'grenades_empty' if args.kind=='choke' else 'grenades_full');action(0,'specialty_review_camera');time.sleep(.6);pad(2,'x');wait_for(lambda d:player(d,2)['captor'],10)
 action(2,'pad_rt_down');wait_for(lambda d:player(d,2)['finisher']>0,5);action(0,'review_freeze');action(2,'pad_rt_up');capture(OUT/(args.kind+'-start.png'));print('STAGED',args.kind,flush=True)
if args.record:
 frames=OUT/(args.kind+'-frames');frames.mkdir(parents=True,exist_ok=True);samples=[]
 action(0,'review_slow')
 duration=5.8 if args.kind=='choke' else 4.8
 count=round(duration*20)
 for i in range(count):
  target=max(.05,i/20)
  d=wait_for(lambda d:elapsed(d)>=target,15)
  capture(frames/f'frame-{i:03}.png');samples.append({'frame':i,'gameplayTime':elapsed(d),'spy':player(d,2),'merc':player(d,1),'grenades':server(d)['grenades']})
  if args.kind=='choke':
   if i==24:action(1,'pad_move_down');action(1,'pad_lt_down')
   if i==36:action(1,'pad_move_up');pad(1,'rt');action(1,'pad_lt_up')
  if i in [20,40,60,80]:shutil.copyfile(frames/f'frame-{i:03}.png',DEST/(args.kind+f'-phase-{i/20:.0f}.png'))
  if i%20==0:print('FRAME',i,'TIME',elapsed(d),flush=True)
 action(0,'review_normal')
 video=DEST/('warehouse-'+args.kind+'-preview.mp4')
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','20','-i',str(frames/'frame-%03d.png'),'-vf','scale=1280:-2:flags=lanczos','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
 (DEST/(args.kind+'-preview.json')).write_text(json.dumps({'source':'Actual Unreal warehouse gameplay, four networked PIE participants; unmodified gameplay viewport pixels','fps':20,'samples':samples},indent=2));print('RECORDED',video,flush=True)
