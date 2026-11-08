"""Import only the corrected spy traversal clips; preserve materials and rigs."""
import unreal,json,hashlib
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();EL=unreal.EditorAssetLibrary
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),'Stop PIE first'
tools=unreal.AssetToolsHelpers.get_asset_tools();skel=unreal.load_asset('/Game/Prototype/Mannequin/SK_Prototype_Skeleton');assert skel
report={}
for name,seconds in [('SpyVentEntry',3.2),('SpyVentCrawl',1.),('SpyVentIdle',.2)]:
 file=P/'Art/Actions'/(name+'.fbx');digest=hashlib.sha256(file.read_bytes()).hexdigest();path='/Game/Characters/Actions/'+name;asset=unreal.load_asset(path)
 if not asset or EL.get_metadata_tag(asset,'BuildSourceSHA')!=digest:
  opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=skel;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.override_animation_name=name
  opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME);opt.anim_sequence_import_data.set_editor_property('remove_redundant_keys',False)
  task=unreal.AssetImportTask();task.filename=str(file);task.destination_path='/Game/Characters/Actions';task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.options=opt;task.factory=unreal.FbxFactory();tools.import_asset_tasks([task]);objects=[o for o in task.get_objects() if isinstance(o,unreal.AnimSequence)]
  asset=unreal.load_asset(path)
  if not asset:
   assert len(objects)==1,(name,objects);assert EL.rename_asset(objects[0].get_path_name(),path);asset=unreal.load_asset(path)
  assert asset in objects,(name,'Importer did not update target',objects);EL.set_metadata_tag(asset,'BuildSourceSHA',digest)
 assert abs(asset.get_play_length()-seconds)<.025,(name,asset.get_play_length());EL.save_loaded_asset(asset);report[name]={'seconds':asset.get_play_length(),'asset':asset.get_path_name()}
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert level.load_level('/Game/Maps/Warehouse')
warehouse_class=unreal.load_class(None,'/Script/StealthPrototype.SPWarehouse');warehouses=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class()==warehouse_class];assert len(warehouses)==1
warehouses[0].rebuild_warehouse();assert level.save_current_level();unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(P/'Saved/VentEntryQA/import.json').write_text(json.dumps(report,indent=2));unreal.log('VENT_ENTRY_IMPORTED '+json.dumps(report))
