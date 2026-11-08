"""Import original modular art/actions and create the reference-led playable map."""
import unreal,json,hashlib
from pathlib import Path
P=Path(unreal.Paths.project_dir()).resolve();SRC=P/'Art/Warehouse';ROOT='/Game/Warehouse';EL=unreal.EditorAssetLibrary;ML=unreal.MaterialEditingLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();report={}
assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),'Stop PIE before importing'
def task(file,dest,name,options=None):
 digest=hashlib.sha256(Path(file).read_bytes()).hexdigest();existing=unreal.load_asset(dest+'/'+name)
 if existing and EL.get_metadata_tag(existing,'BuildSourceSHA')==digest:return existing
 t=unreal.AssetImportTask();t.filename=str(file);t.destination_path=dest;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
 if options:t.options=options;t.factory=unreal.FbxFactory()
 tools.import_asset_tasks([t]);a=unreal.load_asset(dest+'/'+name)
 if not a:
  objs=list(t.get_objects());assert len(objs)==1,(name,objs);EL.rename_asset(objs[0].get_path_name(),dest+'/'+name);a=unreal.load_asset(dest+'/'+name)
 assert a,name
 assert any(o==a for o in t.get_objects()),(name,'Importer did not update the requested asset')
 EL.set_metadata_tag(a,'BuildSourceSHA',digest);EL.save_loaded_asset(a)
 return a
textures={}
for f in sorted(SRC.glob('*.png')):
 a=unreal.load_asset(ROOT+'/Textures/'+f.stem) or task(f,ROOT+'/Textures',f.stem)
 if f.stem.endswith('_N'):a.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);a.set_editor_property('srgb',False)
 if f.stem.endswith('_R'):a.set_editor_property('srgb',False);a.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
 EL.save_loaded_asset(a);textures[f.stem]=a
for name in ['Wood','Steel','Concrete','ConcreteFloor','Duct','Canvas','Roof','Yellow','Black','Key','Glass','LampLens']:
 path=ROOT+'/Materials/M_'+name;m=unreal.load_asset(path) or tools.create_asset('M_'+name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew());ML.delete_all_material_expressions(m)
 if name=='Glass':
  m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('two_sided',True)
  for value,prop in [(.12,unreal.MaterialProperty.MP_OPACITY),(.08,unreal.MaterialProperty.MP_ROUGHNESS)]:
   c=ML.create_material_expression(m,unreal.MaterialExpressionConstant);c.r=value;ML.connect_material_property(c,'',prop)
  c=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(.65,.76,.84,1);ML.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
 elif name=='LampLens':
  c=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(6,4.6,2.6,1);ML.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 elif name in ['Yellow','Black','Key']:
  colors={'Yellow':(.63,.40,.07),'Black':(.015,.02,.022),'Key':(.7,.72,.66)};c=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(*colors[name],1);ML.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
 else:
  source='Concrete' if name=='ConcreteFloor' else 'Steel' if name=='Roof' else name
  uv=ML.create_material_expression(m,unreal.MaterialExpressionTextureCoordinate,-600,0);uv.u_tiling=4 if source=='Wood' else 24 if name=='Concrete' else 2;uv.v_tiling=uv.u_tiling
  out_uv=uv
  if name=='ConcreteFloor':
   world=ML.create_material_expression(m,unreal.MaterialExpressionWorldPosition,-900,0);mask=ML.create_material_expression(m,unreal.MaterialExpressionComponentMask,-700,0);mask.set_editor_property('r',True);mask.set_editor_property('g',True);mask.set_editor_property('b',False);mask.set_editor_property('a',False)
   ML.connect_material_expressions(world,'',mask,'Input');scale=ML.create_material_expression(m,unreal.MaterialExpressionMultiply,-500,0);scale.set_editor_property('const_b',1/240);ML.connect_material_expressions(mask,'',scale,'A');out_uv=scale
  for suffix,prop,y in [('',unreal.MaterialProperty.MP_BASE_COLOR,0),('_N',unreal.MaterialProperty.MP_NORMAL,200),('_R',unreal.MaterialProperty.MP_ROUGHNESS,400)]:
   sample=ML.create_material_expression(m,unreal.MaterialExpressionTextureSample,-250,y);sample.texture=textures['T_'+source+suffix]
   if suffix=='_N':sample.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
   elif suffix=='_R':sample.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
   ML.connect_material_expressions(out_uv,'',sample,'Coordinates')
   if name=='ConcreteFloor' and suffix=='':
    pigment=ML.create_material_expression(m,unreal.MaterialExpressionMultiply,-50,y);pigment.set_editor_property('const_b',.4);ML.connect_material_expressions(sample,'RGB',pigment,'A');ML.connect_material_property(pigment,'',prop)
   else:ML.connect_material_property(sample,'R' if suffix=='_R' else 'RGB',prop)
  metallic=ML.create_material_expression(m,unreal.MaterialExpressionConstant,-250,550);metallic.r=.72 if source in ['Steel','Duct'] else 0;ML.connect_material_property(metallic,'',unreal.MaterialProperty.MP_METALLIC)
 ML.recompile_material(m);EL.save_loaded_asset(m)
for f in sorted(SRC.glob('SM_*.fbx')):
 opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
 opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=True
 mesh=task(f,ROOT+'/Meshes',f.stem,opt)
 slots=list(mesh.static_materials)
 for i,slot in enumerate(slots):
  label=str(slot.get_editor_property('material_slot_name'));label='LampLens' if f.stem=='SM_Lamp' and label=='Yellow' else label;mat=unreal.load_asset(ROOT+'/Materials/M_'+label)
  assert mat,(f.stem,label);mesh.set_material(i,mat)
 EL.save_loaded_asset(mesh);bounds=mesh.get_bounding_box();report[f.stem]={'asset':mesh.get_path_name(),'min':str(bounds.min),'max':str(bounds.max)}
# Author animations share the existing skeleton; never replace its reference pose.
skel=unreal.load_asset('/Game/Prototype/Mannequin/SK_Prototype_Skeleton');assert skel
# Camera-only forearms retain the separate full-body world mesh.
opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.skeleton=skel;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False);opt.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose',False)
arms=task(P/'Art/Equipment/MercArms.fbx','/Game/Characters/Equipment','SK_MercArms',opt)
slots=list(arms.get_editor_property('materials'))
fp_mat=unreal.load_asset('/Game/Characters/Equipment/M_MercFP') or tools.duplicate_asset('M_MercFP','/Game/Characters/Equipment',unreal.load_asset('/Game/Characters/Meshy/Merc/M_Merc'))
fp_mat.set_editor_property('two_sided',True);ML.recompile_material(fp_mat);EL.save_loaded_asset(fp_mat)
sleeve_mat=unreal.load_asset('/Game/Characters/Equipment/M_FPSleeve') or tools.create_asset('M_FPSleeve','/Game/Characters/Equipment',unreal.Material,unreal.MaterialFactoryNew())
ML.delete_all_material_expressions(sleeve_mat);c=ML.create_material_expression(sleeve_mat,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(.018,.028,.05,1);ML.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR);rough=ML.create_material_expression(sleeve_mat,unreal.MaterialExpressionConstant);rough.r=.9;ML.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);ML.set_material_usage(sleeve_mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);ML.recompile_material(sleeve_mat);EL.save_loaded_asset(sleeve_mat)
for slot in slots:slot.material_interface=sleeve_mat if 'fpsleeve' in str(slot.get_editor_property('imported_material_slot_name')).lower() else fp_mat
arms.set_editor_property('materials',slots);EL.save_loaded_asset(arms)
for name,seconds in [('MercEquipView',.7),('MercThrowView',.966667),('MercThrow',.966667),('SpyRope',.8),('SpyVentEntry',3.2),('SpyVentCrawl',1.),('SpyVentIdle',.2),('MercKnockout',.8)]:
 opt=unreal.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=skel;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
 opt.anim_sequence_import_data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME);opt.anim_sequence_import_data.set_editor_property('remove_redundant_keys',False)
 anim=task(P/'Art/Actions'/(name+'.fbx'),'/Game/Characters/Actions',name,opt);assert abs(anim.get_play_length()-seconds)<.04,(name,anim.get_play_length());EL.save_loaded_asset(anim)
 report[name]={'seconds':anim.get_play_length(),'skeleton':anim.get_editor_property('skeleton').get_path_name()}
task(P/'Art/Actions/DropImpact.wav','/Game/Characters/Actions','DropImpact')
# Existing maps stay intact. The new map becomes the ordinary entry point.
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);map_path='/Game/Maps/Warehouse'
if EL.does_asset_exist(map_path):assert level.load_level(map_path)
else:assert level.new_level(map_path)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);existing=list(actors.get_all_level_actors())
def ensure(label,cls,loc=unreal.Vector(),rot=unreal.Rotator()):
 a=next((a for a in existing if a.get_actor_label()==label),None)
 if not a:a=actors.spawn_actor_from_class(cls,loc,rot);a.set_actor_label(label)
 return a
warehouse=ensure('Warehouse',unreal.load_class(None,'/Script/StealthPrototype.SPWarehouse'))
warehouse.rebuild_warehouse()
sun=ensure('Warehouse Sun',unreal.DirectionalLight,unreal.Vector(0,0,1600),unreal.Rotator(-52,-35,0));light=sun.get_component_by_class(unreal.DirectionalLightComponent);light.set_editor_property('intensity',12000.);light.set_editor_property('atmosphere_sun_light',True);light.set_editor_property('light_source_angle',1.2);light.set_mobility(unreal.ComponentMobility.MOVABLE)
ensure('Warehouse Atmosphere',unreal.SkyAtmosphere)
sky=ensure('Warehouse Sky',unreal.SkyLight);sky_light=sky.get_component_by_class(unreal.SkyLightComponent);sky_light.set_mobility(unreal.ComponentMobility.MOVABLE);sky_light.set_editor_property('intensity',4.0);sky_light.set_light_color(unreal.LinearColor(1,.9,.78,1));sky_light.set_editor_property('real_time_capture',True)
# Bright, slightly warm interiors; night vision is only useful inside opaque ducts.
post=ensure('Warehouse Exposure',unreal.PostProcessVolume);post.set_editor_property('unbound',True);settings=post.settings
settings.override_auto_exposure_min_brightness=True;settings.override_auto_exposure_max_brightness=True;settings.auto_exposure_min_brightness=9.;settings.auto_exposure_max_brightness=9.;settings.override_auto_exposure_bias=True;settings.auto_exposure_bias=.2;settings.override_bloom_intensity=True;settings.bloom_intensity=.15;post.settings=settings
level.editor_set_game_view(True)
assert level.save_current_level();unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(P/'Saved/WarehouseQA/import.json').write_text(json.dumps(report,indent=2));unreal.log('WAREHOUSE_IMPORT_COMPLETE '+json.dumps(report))
