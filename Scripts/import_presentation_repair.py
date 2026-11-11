"""Scoped face repair; original Meshy inputs are preserved."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve()
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():raise RuntimeError('Stop PIE first')
source=(P/'Scripts/import_equipment.py').read_text();exec(source[:source.index("spy=imported(")],globals())
ML=unreal.MaterialEditingLibrary
def cloth_material(name,color,rough,noise=False):
 path=DEST+'/'+name
 if EL.does_asset_exist(path):return unreal.load_asset(path)
 m=tools.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew())
 c=ML.create_material_expression(m,unreal.MaterialExpressionVectorParameter,-400,0);c.set_editor_property('parameter_name','ClothColor');c.set_editor_property('default_value',unreal.LinearColor(*color,1))
 out=c
 if noise:
  n=ML.create_material_expression(m,unreal.MaterialExpressionNoise,-600,150);n.set_editor_property('scale',6.0);n.set_editor_property('quality',1);n.set_editor_property('output_min',.6);n.set_editor_property('output_max',1.)
  mul=ML.create_material_expression(m,unreal.MaterialExpressionMultiply,-150,0);ML.connect_material_expressions(c,'',mul,'A');ML.connect_material_expressions(n,'',mul,'B');out=mul
 ML.connect_material_property(out,'',unreal.MaterialProperty.MP_BASE_COLOR)
 r=ML.create_material_expression(m,unreal.MaterialExpressionConstant,-300,200);r.set_editor_property('r',rough);ML.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
 ML.set_material_usage(m,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);ML.recompile_material(m)
 if not EL.save_loaded_asset(m):raise RuntimeError('Presentation material did not save')
 return m
cloth_material('M_SpyFaceCloth',(.018,.020,.022),.98,True)
cloth_material('M_SpyEyeShadow',(.055,.045,.035),.55)
cloth_material('M_SpyEyeSkin',(.14,.09,.065),.85)
cloth_material('M_SpySclera',(.16,.13,.11),.7)
cloth_material('M_GoggleHousing',(.025,.03,.025),.65)
spy=imported('SpyEquipment','SK_SpyEquipment','skeletal',skeleton)
slots=list(spy.get_editor_property('materials'))
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name')).lower()
 path='/Game/Characters/Meshy/Spy/M_Spy'
 if 'fabricrepair' in name or 'gloverepair' in name:path=DEST+'/M_SpyFaceCloth'
 elif 'eyewhite' in name:path=DEST+'/M_SpySclera'
 elif 'eyeskin' in name:path=DEST+'/M_SpyEyeSkin'
 elif 'iris' in name:path='/Game/Characters/Equipment/M_Iris'
 slot.material_interface=unreal.load_asset(path);slots[i]=slot
spy.set_editor_property('materials',slots)
if not EL.save_loaded_asset(spy):raise RuntimeError('Spy repair save failed')
unreal.log('PRESENTATION_REPAIR_SAVED '+spy.get_path_name())
clip=imported('SpyEquip','SpyEquip','anim',skeleton)
if not EL.save_loaded_asset(clip):raise RuntimeError('Spy fitted grip save failed')
goggles=imported('Goggles','SM_Goggles','static')
for i in range(len(goggles.static_materials)):goggles.set_material(i,unreal.load_asset(DEST+'/M_GoggleHousing'))
if not EL.save_loaded_asset(goggles):raise RuntimeError('Goggle seam save failed')
lens=unreal.load_asset(DEST+'/M_GoggleLens')
node=ML.get_material_property_input_node(lens,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
if not isinstance(node,unreal.MaterialExpressionEyeAdaptationInverse):
 inverse=ML.create_material_expression(lens,unreal.MaterialExpressionEyeAdaptationInverse);pins=ML.get_material_expression_input_names(inverse)
 alpha=ML.create_material_expression(lens,unreal.MaterialExpressionConstant);alpha.set_editor_property('r',1.)
 if not ML.connect_material_expressions(node,'',inverse,pins[0]):raise RuntimeError('Lens color connection failed')
 if not ML.connect_material_expressions(alpha,'',inverse,pins[1]):raise RuntimeError('Lens exposure connection failed')
 if not ML.connect_material_property(inverse,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR):raise RuntimeError('Lens emission connection failed')
 ML.recompile_material(lens)
 if not EL.save_loaded_asset(lens):raise RuntimeError('Lens material save failed')

SOURCE=P/'Art/UtilityRifle';DEST='/Game/Characters/UtilityRifle'
weapon=unreal.load_asset(DEST+'/SK_MercUtility');weapon_skeleton=weapon.get_editor_property('skeleton');weapon=imported('MercUtility','SK_MercUtility','skeletal',weapon_skeleton)
slots=list(weapon.get_editor_property('materials'))
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name'));key=next((key for key in ['Shell','Metal','Rubber','Panel','Amber','Glass'] if key.lower() in name.lower()),None)
 if not key:raise RuntimeError('Unknown weapon material '+name)
 slot.material_interface=unreal.load_asset(DEST+'/M_'+key);slots[i]=slot
weapon.set_editor_property('materials',slots)
if not EL.save_loaded_asset(weapon):raise RuntimeError('Ergonomic rifle save failed')
for name in ['MercUtilityEquip','MercUtilityEquipView']:
 clip=imported(name,name,'anim',skeleton)
 if not EL.save_loaded_asset(clip):raise RuntimeError('Grip pose did not save')
arms=imported('MercUtilityArms','SK_MercUtilityArms','skeletal',skeleton)
slots=list(arms.get_editor_property('materials'))
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name')).lower()
 slot.material_interface=unreal.load_asset('/Game/Characters/UtilityRifle/M_Rubber' if 'gloverepair' in name else '/Game/Characters/Meshy/Merc/M_Merc');slots[i]=slot
arms.set_editor_property('materials',slots)
if not EL.save_loaded_asset(arms):raise RuntimeError('Textured arms save failed')
SOURCE=P/'Art/Actions';DEST='/Game/Characters/Actions'
clip=imported('MercThrowView','MercThrowView','anim',skeleton)
if not EL.save_loaded_asset(clip):raise RuntimeError('First-person throw save failed')
SOURCE=P/'Art/FittedCharacters';DEST='/Game/Characters/Meshy/Merc'
merc=imported('Merc_fitted','SK_Merc','skeletal',skeleton)
slots=list(merc.get_editor_property('materials'))
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name')).lower()
 slot.material_interface=unreal.load_asset('/Game/Characters/UtilityRifle/M_Rubber' if 'gloverepair' in name else DEST+'/M_Merc');slots[i]=slot
merc.set_editor_property('materials',slots)
if not EL.save_loaded_asset(merc):raise RuntimeError('Repaired merc mesh save failed')

# Morph-deformed cloth/gloves require their own material permutations.
for mesh in [spy,merc,arms]:
 for slot in mesh.get_editor_property('materials'):
  material=slot.material_interface
  if isinstance(material,unreal.Material):
   ML.set_material_usage(material,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
   ML.set_material_usage(material,unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS)
   ML.recompile_material(material)
   if not EL.save_loaded_asset(material):raise RuntimeError('Morph material save failed')
report={}
for label,mesh in [('Spy',spy),('Merc',merc),('View',arms)]:
 names=[m.get_name() for m in mesh.get_editor_property('morph_targets')]
 required=['ContactClothR','ContactClothL']+(['LauncherGripR','LauncherGripL'] if label=='Spy' else [])
 if not all(name in names for name in required):raise RuntimeError('Contact morph import missing for '+label+': '+str(names))
 report[label]={'asset':mesh.get_path_name(),'morphs':names}
(P/'Saved/HandContactQA/imported-correctives.json').write_text(json.dumps(report,indent=2))
unreal.log('FITTED_CONTACT_MESHES_SAVED '+json.dumps(report))
