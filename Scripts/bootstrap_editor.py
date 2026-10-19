"""Run INSIDE Unreal Editor after compiling the C++ module, not in system Python.

Creates only missing prototype assets; existing assets are preserved.
Gameplay and arena geometry are C++, not Python runtime dependencies.
"""
import unreal


def create_material(name, color):
    path = "/Game/Prototype/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, "/Game/Prototype", unreal.Material, unreal.MaterialFactoryNew()
    )
    if material is None:
        raise RuntimeError("Failed to create " + path)
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector
    )
    node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        node, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material):
        raise RuntimeError("Failed to save " + path)


create_material("M_Spy", (0.03, 0.18, 0.28))
create_material("M_Merc", (0.35, 0.15, 0.035))
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
map_path = "/Game/Maps/Prototype"
if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
    if not level.new_level(map_path):
        raise RuntimeError("Could not create prototype map")
    if not level.save_current_level():
        raise RuntimeError("Could not save prototype map")
unreal.log("Prototype map/materials ready. Open /Game/Maps/Prototype. Arena spawns on Play.")

# Original placeholder gear material with an exposed color parameter.
gear_path='/Game/Prototype/M_Gear'
if not unreal.EditorAssetLibrary.does_asset_exist(gear_path):
    gear=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Gear','/Game/Prototype',unreal.Material,unreal.MaterialFactoryNew())
    tint=unreal.MaterialEditingLibrary.create_material_expression(gear,unreal.MaterialExpressionVectorParameter)
    tint.set_editor_property('parameter_name','Tint')
    tint.set_editor_property('default_value',unreal.LinearColor(.015,.02,.025,1))
    unreal.MaterialEditingLibrary.connect_material_property(tint,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(gear)
    unreal.EditorAssetLibrary.save_loaded_asset(gear)

# Only a data/tuning child; gameplay remains in tested C++.
if not unreal.EditorAssetLibrary.does_asset_exist('/Game/Prototype/BP_Player'):
    factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.SPCharacter)
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_Player','/Game/Prototype',unreal.Blueprint,factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)

from pathlib import Path
for name in ['Step','Shot']:
    if unreal.EditorAssetLibrary.does_asset_exist('/Game/Prototype/Audio/'+name): continue
    task=unreal.AssetImportTask()
    task.filename=str(Path(unreal.Paths.project_dir())/'Art'/'Audio'/(name+'.wav'))
    task.destination_path='/Game/Prototype/Audio';task.destination_name=name
    task.automated=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths: raise RuntimeError('Audio import failed: '+name)
unreal.log('Prototype tuning Blueprint, gear and original placeholder audio ready')

for path in ['/Game/Prototype/M_Spy','/Game/Prototype/M_Merc']:
    material=unreal.load_asset(path)
    unreal.MaterialEditingLibrary.set_material_usage(material,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
for name in ['Idle','Walk','CrouchIdle','Crouch','Jump','Fall','Land','Vault']:
    anim=unreal.load_asset('/Game/Prototype/Mannequin/'+name)
    if anim:
        anim.set_editor_property('force_root_lock',True)
        unreal.EditorAssetLibrary.save_loaded_asset(anim)
