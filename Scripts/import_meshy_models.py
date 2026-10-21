"""Run in a full Unreal Editor session. Adds assets and resumes partial imports."""
import json
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = PROJECT / 'Art/MeshySource/2026-10-20'
DEST = '/Game/Meshy/Imported_20261020'
REPORT = PROJECT / 'Saved/MeshyImportReport.json'
ITEMS = [
    ('Night_Vision_Operativ', 'Spy'),
    ('Midnight_Sentinel', 'Merc'),
    ('Tactical_Frontline_Si', 'MercCarbine'),
]
tools = unreal.AssetToolsHelpers.get_asset_tools()
materials = unreal.MaterialEditingLibrary
report = {'project':str(PROJECT), 'destination':DEST, 'models':[], 'success':False}

def import_file(filename, folder, name, options=None, factory=None):
    if unreal.EditorAssetLibrary.does_asset_exist(folder+'/'+name):
        return [unreal.load_asset(folder+'/'+name)]
    task = unreal.AssetImportTask()
    task.filename = str(filename)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = False
    task.save = True
    if options is not None: task.options = options
    if factory is not None: task.factory = factory
    tools.import_asset_tasks([task])
    result = list(task.get_objects())
    if not result: raise RuntimeError('No assets imported from '+str(filename))
    return result

try:
    for token, label in ITEMS:
        files = list(SOURCE.rglob('*'+token+'*.fbx'))
        if len(files) != 1: raise RuntimeError('Expected one FBX for '+label)
        fbx = files[0]
        folder = DEST+'/'+label
        options = unreal.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.import_mesh = True
        options.import_as_skeletal = False
        options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        options.import_materials = False
        options.import_textures = False
        options.import_animations = False
        options.static_mesh_import_data.combine_meshes = True
        options.static_mesh_import_data.auto_generate_collision = False
        options.static_mesh_import_data.generate_lightmap_u_vs = False
        options.static_mesh_import_data.convert_scene = True
        options.static_mesh_import_data.convert_scene_unit = True
        imported = import_file(fbx, folder, 'SM_'+label, options, unreal.FbxFactory())
        meshes = [a for a in imported if isinstance(a,unreal.StaticMesh)]
        if len(meshes)!=1: raise RuntimeError('Expected one combined static mesh for '+label)
        mesh = meshes[0]
        textures = {}
        stem = fbx.stem
        for suffix, key in [('', 'BaseColor'),('_normal','Normal'),('_roughness','Roughness'),('_metallic','Metallic')]:
            tex = import_file(fbx.with_name(stem+suffix+'.png'),folder+'/Textures','T_'+label+'_'+key)[0]
            tex.set_editor_property('srgb',key=='BaseColor')
            if key=='Normal': tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            elif key!='BaseColor': tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
            unreal.EditorAssetLibrary.save_loaded_asset(tex)
            textures[key] = tex
        material = unreal.load_asset(folder+'/M_'+label) if unreal.EditorAssetLibrary.does_asset_exist(folder+'/M_'+label) else None
        create_material = material is None
        if create_material:
            material = tools.create_asset('M_'+label,folder,unreal.Material,unreal.MaterialFactoryNew())
        if not material: raise RuntimeError('Material creation failed for '+label)
        properties = {'BaseColor':unreal.MaterialProperty.MP_BASE_COLOR,'Normal':unreal.MaterialProperty.MP_NORMAL,
                      'Roughness':unreal.MaterialProperty.MP_ROUGHNESS,'Metallic':unreal.MaterialProperty.MP_METALLIC}
        for i,(key,tex) in enumerate(textures.items()):
            if not create_material: continue
            node = materials.create_material_expression(material,unreal.MaterialExpressionTextureSample,-450,i*240)
            node.texture = tex
            node.sampler_type = (unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if key=='Normal' else
                                 unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if key=='BaseColor' else
                                 unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            if not materials.connect_material_property(node,'RGB' if key in ('BaseColor','Normal') else 'R',properties[key]):
                raise RuntimeError('Failed material connection '+key)
        materials.recompile_material(material)
        slots = mesh.get_editor_property('static_materials')
        for i in range(max(1,len(slots))): mesh.set_material(i,material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        bounds = mesh.get_bounding_box()
        entry = {'label':label,'source':str(fbx),'mesh':mesh.get_path_name(),'type':mesh.get_class().get_name(),
                 'material':material.get_path_name(),'textures':{k:v.get_path_name() for k,v in textures.items()},
                 'bounds_cm':{'min':str(bounds.min),'max':str(bounds.max)},'rigged':False,
                 'lod0_triangles':mesh.get_num_triangles(0)}
        report['models'].append(entry)
        REPORT.write_text(json.dumps(report,indent=2))
        unreal.log('MESHY_IMPORTED '+json.dumps(entry))
    report['success'] = True
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    REPORT.write_text(json.dumps(report,indent=2))
unreal.log('MESHY_IMPORT_COMPLETE '+str(REPORT))
