"""Make the existing original blast readable under warehouse exposure."""
import unreal
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),'Stop PIE first'
ML=unreal.MaterialEditingLibrary
def wired(result):
 if not result:raise RuntimeError('Smoke material graph connection failed')

m=unreal.load_asset('/Game/Characters/Grab/M_Blast');assert m
unreal.log('SPECIALTY_BLAST_READY '+m.get_path_name())
# Original cosmetic geometry from the user's merc model, with preserved UVs.
from pathlib import Path
import json
P=Path(unreal.Paths.project_dir()).resolve();src=P/'Art/Grab/Blast';dest='/Game/Characters/Grab/Blast'
tools=unreal.AssetToolsHelpers.get_asset_tools();EL=unreal.EditorAssetLibrary
body=unreal.load_asset('/Game/Characters/Meshy/Merc/M_Merc');assert body
cut=unreal.load_asset(dest+'/M_CutInterior');assert cut
task=unreal.AssetImportTask();task.filename=str(src/'T_BlastSmoke.png');task.destination_path=dest;task.destination_name='T_BlastSmoke';task.automated=True;task.replace_existing=True;task.save=True;tools.import_asset_tasks([task])
tex=unreal.load_asset(dest+'/T_BlastSmoke');assert tex
dust=unreal.load_asset(dest+'/M_BlastDustSoft') if EL.does_asset_exist(dest+'/M_BlastDustSoft') else None
if not dust:
 dust=tools.create_asset('M_BlastDustSoft',dest,unreal.Material,unreal.MaterialFactoryNew())
 dust.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);dust.set_editor_property('two_sided',True)
 col=ML.create_material_expression(dust,unreal.MaterialExpressionVectorParameter,-500,0);col.set_editor_property('parameter_name','DustColor');col.set_editor_property('default_value',unreal.LinearColor(.10,.085,.07,1))
 wired(ML.connect_material_property(col,'',unreal.MaterialProperty.MP_BASE_COLOR))
 sample=ML.create_material_expression(dust,unreal.MaterialExpressionTextureSample,-700,250);sample.set_editor_property('texture',tex)
 opacity=ML.create_material_expression(dust,unreal.MaterialExpressionScalarParameter,-700,150);opacity.set_editor_property('parameter_name','Density');opacity.set_editor_property('default_value',.28)
 multiply=ML.create_material_expression(dust,unreal.MaterialExpressionMultiply,-400,150)
 wired(ML.connect_material_expressions(sample,'A',multiply,'A'));wired(ML.connect_material_expressions(opacity,'',multiply,'B'))
 fade=ML.create_material_expression(dust,unreal.MaterialExpressionDepthFade,-200,150);fade.set_editor_property('fade_distance_default',35)
 wired(ML.connect_material_expressions(multiply,'',fade,ML.get_material_expression_input_names(fade)[0]));wired(ML.connect_material_property(fade,'',unreal.MaterialProperty.MP_OPACITY))
 ML.recompile_material(dust);EL.save_loaded_asset(dust)
# Reuse the soft particle graph; fire needs an emissive, exposure-independent
# version rather than an opaque sphere. Never delete an existing graph.
fire=unreal.load_asset(dest+'/M_BlastFireSoft')
if not fire:
 fire=EL.duplicate_asset(dest+'/M_BlastDustSoft',dest+'/M_BlastFireSoft')
 fire.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 color=ML.get_material_property_input_node(fire,unreal.MaterialProperty.MP_BASE_COLOR)
 inverse=ML.create_material_expression(fire,unreal.MaterialExpressionEyeAdaptationInverse)
 pins=ML.get_material_expression_input_names(inverse)
 wired(ML.connect_material_expressions(color,'',inverse,pins[0]))
 alpha=ML.create_material_expression(fire,unreal.MaterialExpressionConstant);alpha.set_editor_property('r',1.)
 wired(ML.connect_material_expressions(alpha,'',inverse,pins[1]))
 wired(ML.connect_material_property(inverse,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR))
 ML.recompile_material(fire)
 if not EL.save_loaded_asset(fire):raise RuntimeError('Fire material save failed')
task=unreal.AssetImportTask();task.filename=str(src/'T_BlastFire.png');task.destination_path=dest;task.destination_name='T_BlastFire';task.automated=True;task.replace_existing=True;task.save=True;tools.import_asset_tasks([task])
fire_tex=unreal.load_asset(dest+'/T_BlastFire')
if not fire_tex:raise RuntimeError('Fire texture import failed')
def walk(node):
 if not node:return []
 return [node]+[entry for child in ML.get_inputs_for_material_expression(fire,node) for entry in walk(child)]
nodes=walk(ML.get_material_property_input_node(fire,unreal.MaterialProperty.MP_OPACITY))
sample=next(n for n in nodes if isinstance(n,unreal.MaterialExpressionTextureSample));sample.set_editor_property('texture',fire_tex)
inverse=ML.get_material_property_input_node(fire,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
color=ML.get_inputs_for_material_expression(fire,inverse)[0]
if not isinstance(color,unreal.MaterialExpressionMultiply):
 tint=ML.create_material_expression(fire,unreal.MaterialExpressionMultiply)
 wired(ML.connect_material_expressions(color,'',tint,'A'));wired(ML.connect_material_expressions(sample,'RGB',tint,'B'))
 wired(ML.connect_material_expressions(tint,'',inverse,ML.get_material_expression_input_names(inverse)[0]))
ML.recompile_material(fire)
if not EL.save_loaded_asset(fire):raise RuntimeError('Fire graph save failed')
for f in sorted(src.glob('*.fbx')):
 opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
 opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=True
 task=unreal.AssetImportTask();task.filename=str(f);task.destination_path=dest;task.destination_name=f.stem;task.automated=True;task.replace_existing=True;task.save=True;task.options=opt;task.factory=unreal.FbxFactory();tools.import_asset_tasks([task])
 mesh=unreal.load_asset(dest+'/'+f.stem);assert mesh
 mesh.set_material(0,dust if f.stem=='SM_BlastCloud' else body)
 if f.stem!='SM_BlastCloud':mesh.set_material(1,cut)
 EL.save_loaded_asset(mesh)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal.log('MERC_BLAST_FRAGMENTS_IMPORTED')
# Save graph inputs for repeatable material QA without changing the graph.
info={'blend':str(dust.get_editor_property('blend_mode')),'opacity':str(ML.get_material_property_input_node(dust,unreal.MaterialProperty.MP_OPACITY))}
(P/'Saved/SpecialtyQA/smoke-material.json').write_text(json.dumps(info,indent=2))
def inspect_node(node):
 if not node:return None
 item={'type':node.get_class().get_name(),'path':node.get_path_name()}
 for key in ['default_value','parameter_name','texture','const_a','const_b','fade_distance_default']:
  try:item[key]=str(node.get_editor_property(key))
  except Exception:pass
 item['inputs']=[inspect_node(n) for n in ML.get_inputs_for_material_expression(dust,node)]
 return item
info['graph']=inspect_node(ML.get_material_property_input_node(dust,unreal.MaterialProperty.MP_OPACITY))
(P/'Saved/SpecialtyQA/smoke-material.json').write_text(json.dumps(info,indent=2))
