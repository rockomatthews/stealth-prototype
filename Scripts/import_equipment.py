"""Full-editor import of fixed derived equipment assets; originals are preserved."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();SOURCE=P/'Art/Equipment';DEST='/Game/Characters/Equipment'
tools=unreal.AssetToolsHelpers.get_asset_tools();EL=unreal.EditorAssetLibrary;ML=unreal.MaterialEditingLibrary
skeleton=unreal.load_asset('/Game/Prototype/Mannequin/SK_Prototype_Skeleton')
if not skeleton:raise RuntimeError('Migrate the licensed mannequin first')
report={}
def imported(stem,name,kind,skel=None):
 opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False
 opt.import_mesh=kind!='anim';opt.import_as_skeletal=kind!='static';opt.import_animations=kind=='anim'
 opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
 opt.mesh_type_to_import={'anim':unreal.FBXImportType.FBXIT_ANIMATION,'skeletal':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'static':unreal.FBXImportType.FBXIT_STATIC_MESH}[kind]
 if skel:opt.skeleton=skel
 if kind=='skeletal':
  opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False);opt.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose',False)
 if kind=='static':
  opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False
  opt.static_mesh_import_data.generate_lightmap_u_vs=False
 if kind=='anim':
  opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
  opt.anim_sequence_import_data.set_editor_property('remove_redundant_keys',False)
 task=unreal.AssetImportTask();task.filename=str(SOURCE/(stem+'.fbx'));task.destination_path=DEST;task.destination_name=name
 task.automated=True;task.save=True;task.replace_existing=True;task.options=opt;task.factory=unreal.FbxFactory()
 tools.import_asset_tasks([task]);objects=list(task.get_objects())
 obj=unreal.load_asset(DEST+'/'+name)
 if not obj:
  cls=unreal.AnimSequence if kind=='anim' else unreal.SkeletalMesh if kind=='skeletal' else unreal.StaticMesh
  candidates=[o for o in objects if isinstance(o,cls)]
  if len(candidates)==1:
   obj=candidates[0]
   if obj.get_name()!=name:
    EL.rename_asset(obj.get_path_name(),DEST+'/'+name);obj=unreal.load_asset(DEST+'/'+name)
 if not obj:raise RuntimeError('Import failed '+name+': '+str(objects))
 return obj
spy=imported('SpyEquipment','SK_SpyEquipment','skeletal',skeleton)
goggles=imported('Goggles','SM_Goggles','static')
arms=imported('MercArms','SK_MercArms','skeletal',skeleton)
carbine=imported('Carbine','SK_Carbine','skeletal')
launcher=imported('Launcher','SK_Launcher','skeletal')
def material(path,color,metallic=.1,roughness=.6):
 m=unreal.load_asset(path)
 if m:return m
 folder,name=path.rsplit('/',1);m=tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
 c=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-300,0);c.constant=unreal.LinearColor(*color,1)
 ML.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
 for value,prop,y in [(metallic,unreal.MaterialProperty.MP_METALLIC,130),(roughness,unreal.MaterialProperty.MP_ROUGHNESS,240)]:
  n=ML.create_material_expression(m,unreal.MaterialExpressionConstant,-300,y);n.r=value;ML.connect_material_property(n,'',prop)
 ML.set_material_usage(m,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);ML.recompile_material(m);return m
launcher_mat=material(DEST+'/M_Launcher',(.035,.045,.05),.55,.4)
spy_mat=unreal.load_asset('/Game/Characters/Meshy/Spy/M_Spy')
carbine_mat=unreal.load_asset('/Game/Meshy/Imported_20261020/MercCarbine/M_MercCarbine')
eye_white=material(DEST+'/M_EyeWhite',(.55,.52,.45),0,.55)
iris=material(DEST+'/M_Iris',(.012,.018,.012),0,.4)
for mesh,mat in [(spy,spy_mat),(carbine,carbine_mat),(launcher,launcher_mat),(arms,unreal.load_asset('/Game/Characters/Meshy/Merc/M_Merc'))]:
 ML.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);ML.recompile_material(mat)
 slots=list(mesh.get_editor_property('materials'))
 for i,slot in enumerate(slots):
  name=str(slot.get_editor_property('imported_material_slot_name')).lower()
  selected=mat
  if mesh==spy:
   if 'fabricrepair' in name:selected=unreal.load_asset('/Game/Prototype/M_Gear')
   elif 'eyewhite' in name:selected=eye_white
   elif 'iris' in name:selected=iris
  slot.material_interface=selected;slots[i]=slot
 mesh.set_editor_property('materials',slots)
 assert all(s.material_interface is not None for s in mesh.get_editor_property('materials'))
 EL.save_loaded_asset(mat);EL.save_loaded_asset(mesh)
optic_mat=material(DEST+'/M_OpticGlass',(.005,.008,.006),.35,.18)
for i in range(len(goggles.static_materials)):goggles.set_material(i,spy_mat if i==0 else optic_mat)
EL.save_loaded_asset(goggles)
lens=unreal.load_asset(DEST+'/M_GoggleLens')
if not lens:lens=tools.create_asset('M_GoggleLens',DEST,unreal.Material,unreal.MaterialFactoryNew())
if lens:
 ML.delete_all_material_expressions(lens)
 lens.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 color=ML.create_material_expression(lens,unreal.MaterialExpressionConstant3Vector,-400,0);color.constant=unreal.LinearColor(.01,5,.03,1)
 enabled=ML.create_material_expression(lens,unreal.MaterialExpressionScalarParameter,-400,150);enabled.set_editor_property('parameter_name','Enabled');enabled.set_editor_property('default_value',0)
 multiply=ML.create_material_expression(lens,unreal.MaterialExpressionMultiply,-100,0)
 ML.connect_material_expressions(color,'',multiply,'A');ML.connect_material_expressions(enabled,'',multiply,'B')
 ML.connect_material_property(multiply,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 ML.recompile_material(lens);EL.save_loaded_asset(lens)
for source,name,skel in [('SpyEquip','SpyEquip',skeleton),('MercEquip','MercEquip',skeleton),('Carbine','CarbineFire',carbine.get_editor_property('skeleton')),('Launcher','LauncherFire',launcher.get_editor_property('skeleton'))]:
 anim=imported(source,name,'anim',skel);EL.save_loaded_asset(anim)
 report[name]={'asset':anim.get_path_name(),'seconds':anim.get_play_length(),'skeleton':anim.get_editor_property('skeleton').get_path_name()}
for label,mesh in [('spy',spy),('carbine',carbine),('launcher',launcher),('arms',arms)]:
 report[label]={'asset':mesh.get_path_name(),'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'bounds':str(mesh.get_bounds()),'materials':[(str(s.get_editor_property('imported_material_slot_name')),s.material_interface.get_path_name()) for s in mesh.get_editor_property('materials')]}
 if label=='spy' and not 160<mesh.get_bounds().box_extent.z*2<210:raise RuntimeError('Spy scale invalid')
report['goggles']={'asset':goggles.get_path_name(),'bounds':str(goggles.get_bounding_box())}
(P/'Saved/EquipmentQA/import.json').write_text(json.dumps(report,indent=2))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal.log('EQUIPMENT_IMPORT_COMPLETE '+json.dumps(report))
