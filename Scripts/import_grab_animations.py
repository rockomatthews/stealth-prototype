"""Import original paired prototype clips without changing the shared bind pose."""
import unreal,json,math,random,wave,struct
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();SRC=P/'Art/Grab';DEST='/Game/Characters/Grab'
EL=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();ML=unreal.MaterialEditingLibrary
skel=unreal.load_asset('/Game/Prototype/Mannequin/SK_Prototype_Skeleton');assert skel
report={}
specialty=globals().get('SPECIALTY_ONLY',False)
for role in ['Spy','Merc']:
 for move,duration in [('Hold',.1),('Snap',.85)]+[('BackChoke',5.),('Grenade',2.8)]+([('Panic',1.),('ChokeFall',.8)] if role=='Merc' else [('ChokeExit',1.6)]):
  name=role+move;opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=skel;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
  opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME);opt.anim_sequence_import_data.set_editor_property('remove_redundant_keys',False)
  task=unreal.AssetImportTask();task.filename=str(SRC/(name+'.fbx'));task.destination_path=DEST;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.options=opt;task.factory=unreal.FbxFactory();tools.import_asset_tasks([task])
  asset=unreal.load_asset(DEST+'/'+name)
  if not asset:
   found=[a for a in task.get_objects() if isinstance(a,unreal.AnimSequence)];assert len(found)==1,str(task.get_objects());EL.rename_asset(found[0].get_path_name(),DEST+'/'+name);asset=unreal.load_asset(DEST+'/'+name)
  assert asset and asset.get_editor_property('skeleton')==skel and abs(asset.get_play_length()-duration)<.05,name
  EL.save_loaded_asset(asset);report[name]={'seconds':asset.get_play_length(),'asset':asset.get_path_name()}
if not specialty:
 for name in ['SM_Grenade','SM_GrenadePin']:
  opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False
  task=unreal.AssetImportTask();task.filename=str(SRC/(name+'.fbx'));task.destination_path=DEST;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.options=opt;task.factory=unreal.FbxFactory();tools.import_asset_tasks([task]);assert unreal.load_asset(DEST+'/'+name)
 # Original synthesized short blast; no external sound or licensed asset.
 rng=random.Random(72);rate=24000;last=0;samples=[]
 for i in range(int(rate*.65)):
  t=i/rate;last=.65*last+.35*rng.uniform(-1,1);v=(last*.9+math.sin(2*math.pi*65*t)*.28)*math.exp(-8*t);samples.append(struct.pack('<h',int(max(-1,min(1,v))*26000)))
 with wave.open(str(SRC/'GrenadeBlast.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(samples))
 task=unreal.AssetImportTask();task.filename=str(SRC/'GrenadeBlast.wav');task.destination_path=DEST;task.destination_name='GrenadeBlast';task.automated=True;task.save=True;task.replace_existing=True;tools.import_asset_tasks([task]);assert unreal.load_asset(DEST+'/GrenadeBlast')
 for name,color,unlit in [('M_Blast',(8,3,.3),True),('M_Grenade',(.04,.065,.025),False)]:
  m=unreal.load_asset(DEST+'/'+name) or tools.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew());ML.delete_all_material_expressions(m)
  if unlit:m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
  n=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-200,0);n.constant=unreal.LinearColor(*color,1);ML.connect_material_property(n,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR if unlit else unreal.MaterialProperty.MP_BASE_COLOR);ML.recompile_material(m);EL.save_loaded_asset(m)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);(P/'Saved/EquipmentQA/grab-animation-import.json').write_text(json.dumps(report,indent=2));unreal.log('GRAB_IMPORT_COMPLETE '+json.dumps(report))
