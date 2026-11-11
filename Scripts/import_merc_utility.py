"""Import the original utility-rifle assets without touching the supplied carbine."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),'Stop PIE first'
# Use the project's tested scoped FBX importer, without running its full import.
source=(P/'Scripts/import_equipment.py').read_text();exec(source[:source.index("spy=imported(")],globals())
SOURCE=P/'Art/UtilityRifle';DEST='/Game/Characters/UtilityRifle';report={}
mesh=imported('MercUtility','SK_MercUtility','skeletal')
arms=imported('MercUtilityArms','SK_MercUtilityArms','skeletal',skeleton)
arm_slots=list(arms.get_editor_property('materials'))
for i,slot in enumerate(arm_slots):
 name=str(slot.get_editor_property('imported_material_slot_name')).lower()
 slot.material_interface=unreal.load_asset('/Game/Characters/Equipment/M_FPSleeve' if 'fpsleeve' in name else '/Game/Characters/Meshy/Merc/M_Merc');arm_slots[i]=slot
arms.set_editor_property('materials',arm_slots);assert EL.save_loaded_asset(arms)
colors={'Shell':(.009,.011,.014),'Metal':(.035,.04,.045),'Rubber':(.011,.014,.016),'Panel':(.004,.006,.007),'Amber':(1.,.38,.025),'Glass':(.014,.03,.04)}
for name,color in colors.items():
 path=DEST+'/M_'+name;m=unreal.load_asset(path) or tools.create_asset('M_'+name,DEST,unreal.Material,unreal.MaterialFactoryNew());ML.delete_all_material_expressions(m)
 c=ML.create_material_expression(m,unreal.MaterialExpressionVectorParameter);c.set_editor_property('parameter_name','Tint');c.set_editor_property('default_value',unreal.LinearColor(*color,1))
 if name=='Amber':
  m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);inv=ML.create_material_expression(m,unreal.MaterialExpressionEyeAdaptationInverse);pins=ML.get_material_expression_input_names(inv);alpha=ML.create_material_expression(m,unreal.MaterialExpressionConstant);alpha.set_editor_property('r',1.);ML.connect_material_expressions(c,'',inv,pins[0]);ML.connect_material_expressions(alpha,'',inv,pins[1]);ML.connect_material_property(inv,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 else:
  ML.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
  for key,val,prop in [('Metallic',.75 if name=='Metal' else .1,unreal.MaterialProperty.MP_METALLIC),('Roughness',.75 if name=='Rubber' else .4,unreal.MaterialProperty.MP_ROUGHNESS)]:
   n=ML.create_material_expression(m,unreal.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',key);n.set_editor_property('default_value',val);ML.connect_material_property(n,'',prop)
 ML.set_material_usage(m,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);ML.recompile_material(m);assert EL.save_loaded_asset(m)
slots=list(mesh.get_editor_property('materials'))
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name'));key=next((k for k in colors if k.lower() in name.lower()),None);assert key,name;slot.material_interface=unreal.load_asset(DEST+'/M_'+key);slots[i]=slot
mesh.set_editor_property('materials',slots);assert EL.save_loaded_asset(mesh)
for source,name,skel,duration in [('MercUtility','MercUtilityFire',mesh.get_editor_property('skeleton'),.2),('MercUtilityEquip','MercUtilityEquip',skeleton,.7),('MercUtilityEquipView','MercUtilityEquipView',skeleton,.7)]:
 asset=imported(source,name,'anim',skel);assert abs(asset.get_play_length()-duration)<.05;(report.setdefault('clips',{}))[name]=asset.get_play_length();EL.save_loaded_asset(asset)
report['mesh']=mesh.get_path_name();report['materials']=[str(s.get_editor_property('imported_material_slot_name')) for s in slots];report['bounds']=str(mesh.get_bounds());report['skeleton']=mesh.get_editor_property('skeleton').get_path_name()
(P/'Saved/UtilityRifleQA/import.json').write_text(json.dumps(report,indent=2));unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True);unreal.log('UTILITY_IMPORTED '+json.dumps(report))
