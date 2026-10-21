"""Unreal Editor script: import the optimized, mannequin-compatible Meshy rigs."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve()
tools=unreal.AssetToolsHelpers.get_asset_tools()
template=unreal.load_asset('/Game/Prototype/Mannequin/SK_Prototype')
if not template:raise RuntimeError('Prototype animation skeleton unavailable')
skeleton=template.get_editor_property('skeleton')
report=[]
for label in ['Spy','Merc']:
    folder='/Game/Characters/Meshy/'+label
    material_path=folder+'/M_'+label
    if not unreal.EditorAssetLibrary.does_asset_exist(material_path):
        material=unreal.EditorAssetLibrary.duplicate_asset('/Game/Meshy/Imported_20261020/'+label+'/M_'+label,material_path)
    else:material=unreal.load_asset(material_path)
    unreal.MaterialEditingLibrary.set_material_usage(material,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    unreal.MaterialEditingLibrary.recompile_material(material)
    target=folder+'/SK_'+label
    # Rebuild only these derived meshes; preserve the static originals.
    opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False
    opt.import_as_skeletal=True;opt.import_mesh=True;opt.import_animations=False
    opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
    opt.skeleton=skeleton;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
    opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False)
    opt.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose',False)
    opt.skeletal_mesh_import_data.set_editor_property('import_mesh_lo_ds',False)
    task=unreal.AssetImportTask();task.filename=str(P/'Art/RiggedCharacters'/(label+'_rigged.fbx'))
    task.destination_path=folder;task.destination_name='SK_'+label
    task.automated=True;task.save=True;task.replace_existing=True;task.options=opt;task.factory=unreal.FbxFactory()
    tools.import_asset_tasks([task])
    mesh=unreal.load_asset(target)
    if not mesh or not isinstance(mesh,unreal.SkeletalMesh):raise RuntimeError('Rigged mesh import failed '+label)
    if mesh.get_editor_property('skeleton')!=skeleton:raise RuntimeError('Animation skeleton differs '+label)
    height=mesh.get_bounds().box_extent.z*2
    if not 160<height<210:raise RuntimeError('Unexpected character height '+str(height))
    # Unreal array indexing returns struct values; write each updated slot back.
    entries=list(mesh.get_editor_property('materials'))
    for i,entry in enumerate(entries):
        entry.set_editor_property('material_interface',material)
        entries[i]=entry
    mesh.set_editor_property('materials',entries)
    if not entries or any(e.material_interface!=material for e in mesh.get_editor_property('materials')):
        raise RuntimeError('Material assignment failed '+label)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    info={'label':label,'mesh':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),
          'material':material.get_path_name(),'bounds':str(mesh.get_bounds())}
    report.append(info);unreal.log('RIG_IMPORTED '+json.dumps(info))
(P/'Saved/RiggingQA/unreal_rig_import.json').write_text(json.dumps(report,indent=2))
unreal.log('RIG_IMPORT_COMPLETE')
