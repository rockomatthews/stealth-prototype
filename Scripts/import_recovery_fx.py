"""Create the original lightweight unlit recovery-electricity material."""
import unreal
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),'Stop PIE first'
path='/Game/Prototype/FX/M_RecoveryArc'
m=unreal.load_asset(path)
if not m:
    m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_RecoveryArc','/Game/Prototype/FX',unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    color=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant',unreal.LinearColor(.02,.12,.2,1.))
    power=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionScalarParameter)
    power.set_editor_property('parameter_name','Power');power.set_editor_property('default_value',16.)
    multiply=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionMultiply)
    unreal.MaterialEditingLibrary.connect_material_expressions(color,'',multiply,'A')
    unreal.MaterialEditingLibrary.connect_material_expressions(power,'',multiply,'B')
    unreal.MaterialEditingLibrary.connect_material_property(multiply,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
node=unreal.MaterialEditingLibrary.get_material_property_input_node(m,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
assert node,'Recovery material requires an emissive input'
if not isinstance(node,unreal.MaterialExpressionEyeAdaptationInverse):
    inverse=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionEyeAdaptationInverse)
    pins=unreal.MaterialEditingLibrary.get_material_expression_input_names(inverse)
    assert unreal.MaterialEditingLibrary.connect_material_expressions(node,'',inverse,pins[0])
    alpha=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant)
    alpha.set_editor_property('r',1.)
    assert unreal.MaterialEditingLibrary.connect_material_expressions(alpha,'',inverse,pins[1])
    assert unreal.MaterialEditingLibrary.connect_material_property(inverse,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    for entry in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(m,node):
        if isinstance(entry,unreal.MaterialExpressionConstant3Vector):entry.set_editor_property('constant',unreal.LinearColor(.02,.12,.2,1.))
unreal.MaterialEditingLibrary.set_material_usage(m,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
unreal.MaterialEditingLibrary.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m)
unreal.log('RECOVERY_FX_READY '+m.get_path_name())
