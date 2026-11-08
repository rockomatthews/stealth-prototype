"""Capture saved original warehouse geometry with Epic's native viewport tool."""
import base64,json,time,math
from pathlib import Path
from run_acceptance import call,stop,app_tool,project_tool
OUT=Path('Art/Warehouse/Review');OUT.mkdir(parents=True,exist_ok=True)
stop();call(project_tool,'open_map',map_name='Warehouse')
for name,location,target in [('overview',(2700,-1800,1010),(0,350,340)),('floor',(150,-2050,170),(0,800,250))]:
 d=[b-a for a,b in zip(location,target)]
 transform={'location':dict(zip('xyz',location)),'rotation':{'pitch':math.degrees(math.atan2(d[2],math.hypot(*d[:2]))),'yaw':math.degrees(math.atan2(d[1],d[0])),'roll':0},'scale':dict.fromkeys('xyz',1)}
 call(app_tool,'SetCameraTransform',transform=transform);time.sleep(.5)
 result=call(app_tool,'CaptureViewport',captureTransform=transform,annotations={'gridSpacing':0,'gridExtent':0,'gridHeight':0,'maxLabelDistance':0,'classFilter':{'refPath':'/Script/Engine.Actor'},'maxLabels':0},bShowUI=False)
 data=result.pop('image');assert data['data'],'Empty capture';(OUT/(name+'.png')).write_bytes(base64.b64decode(data['data']));(OUT/(name+'.json')).write_text(json.dumps(result,indent=2));print(name,'saved',flush=True)
call(project_tool,'save_project')
