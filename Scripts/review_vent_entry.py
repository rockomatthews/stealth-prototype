"""Freeze the actual solo mantle at a chosen time for close visual inspection."""
import argparse,json,time,base64
from pathlib import Path
from run_acceptance import *
parser=argparse.ArgumentParser();parser.add_argument('--start',action='store_true');parser.add_argument('--phase',type=float,default=.45);parser.add_argument('--finish',action='store_true');args=parser.parse_args();out=Path('Saved/VentEntryQA');out.mkdir(parents=True,exist_ok=True)
try:
 if args.start:
  stop();call(project_tool,'open_map',map_name='Warehouse')
  call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'},values=json.dumps({'PlayNumberOfClients':1,'RunUnderOneProcess':True,'PlayNetMode':'PIE_Standalone'}))
  call('editor_toolset.toolsets.object.ObjectTools','set_properties',instance={'refPath':'/Script/UnrealEd.Default__EditorPerformanceSettings'},values=json.dumps({'bThrottleCPUWhenNotForeground':False}))
  call(app_tool,'StartPIE',options={'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2});action(0,'automation_on');action(0,'warehouse_rope');time.sleep(.3);action(0,'vent_review_camera');pad(0,'a');action(0,'pad_move_down');wait_for(lambda d:local_pawn(d)['z']>630,15)
 if args.finish:
  action(0,'review_normal');d=wait_for(lambda d:local_pawn(d)['inVent'] and not local_pawn(d)['ventEntry'],12);time.sleep(.3);d=report();name='crawl-handoff'
 else:
  assert 0<args.phase<3.2;action(0,'review_slow');d=wait_for(lambda d:local_pawn(d)['ventEntry'] and local_pawn(d)['ventEntryTime']>=args.phase,20);action(0,'review_freeze');action(0,'pad_move_up');time.sleep(.05);d=report();name=f'phase-{args.phase:.2f}'
  assert local_pawn(d)['crouched'] and local_pawn(d)['capsuleHalfHeight']<43,'Mantle crouch was lost'
 r=call(app_tool,'CaptureEditorImage');(out/(name+'.png')).write_bytes(base64.b64decode(r['data']));(out/(name+'.json')).write_text(json.dumps(d,indent=2));p=local_pawn(d);print(name,{k:p[k] for k in ['ventEntryTime','crouched','z','bodyPelvisZ','rightPalm','leftPalm','rightKnee','animationAsset']},flush=True)
except Exception:
 action(0,'review_normal');raise
