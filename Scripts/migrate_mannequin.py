"""Export installed example art to FBX, import independent project-owned assets.
No Mover gameplay component or animation blueprint is migrated.
"""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_saved_dir())/'ArtMigration'
root.mkdir(parents=True,exist_ok=True)
source='/MoverExamples/Characters/Mannequins'
target='/Game/Prototype/Mannequin'
mesh_path=target+'/SK_Prototype'
assets=unreal.AssetToolsHelpers.get_asset_tools()

def export(obj,filename,exporter):
    task=unreal.AssetExportTask();task.object=obj;task.filename=str(filename)
    task.automated=True;task.prompt=False;task.replace_identical=True
    task.exporter=exporter
    task.options=unreal.FbxExportOption()
    if not unreal.Exporter.run_asset_export_task(task): raise RuntimeError('FBX export failed: '+str(filename))

def import_fbx(filename,name,options):
    task=unreal.AssetImportTask();task.filename=str(filename);task.destination_path=target
    task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=False
    task.options=options
    task.factory=unreal.FbxFactory()
    assets.import_asset_tasks([task])
    if not task.imported_object_paths: raise RuntimeError('FBX import failed: '+name)
    return task.imported_object_paths

if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
    mesh=unreal.load_asset(source+'/Meshes/SKM_Manny_Simple')
    if not mesh: raise RuntimeError('Installed mannequin unavailable')
    filename=root/'Prototype.fbx';export(mesh,filename,unreal.SkeletalMeshExporterFBX())
    opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.import_mesh=True;opt.import_materials=False
    opt.import_textures=False;opt.import_animations=False
    opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
    opt.automated_import_should_detect_type=False
    import_fbx(filename,'SK_Prototype',opt)
mesh=unreal.load_asset(mesh_path)
skeleton=mesh.get_editor_property('skeleton')
clips={'Idle':'MM_Idle','Walk':'MM_Walk_Fwd','Crouch':'MM_Unarmed_Crouch_Walk_Fwd',
       'CrouchIdle':'MM_Unarmed_Crouch_Idle','Jump':'MM_Jump','Fall':'MM_Fall_Loop','Land':'MM_Land','Vault':'VaultOver'}
for name,source_name in clips.items():
    if unreal.EditorAssetLibrary.does_asset_exist(target+'/'+name): continue
    anim=unreal.load_asset(source+'/Animations/Manny/'+source_name)
    if not anim: raise RuntimeError('Animation unavailable: '+source_name)
    filename=root/(name+'.fbx');export(anim,filename,unreal.AnimSequenceExporterFBX())
    opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.import_mesh=False
    opt.import_materials=False;opt.import_textures=False;opt.import_animations=True;opt.skeleton=skeleton
    opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
    opt.automated_import_should_detect_type=False
    import_fbx(filename,name,opt)
unreal.EditorAssetLibrary.save_directory(target,recursive=True)
unreal.log('Independent mannequin art migration completed')
