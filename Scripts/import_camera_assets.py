"""Create original mono camera sounds and a lightweight gas material in Unreal.
Run in the editor through Tools > Execute Python Script, with PIE stopped.
"""
import math,random,struct,wave
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
audio=root/'Art'/'Camera';audio.mkdir(parents=True,exist_ok=True)
rate=22050
for name,duration in [('CameraLure',1.4),('CameraGas',1.2)]:
    rng=random.Random(831);samples=[];filtered=0.
    for index in range(int(rate*duration)):
        t=index/rate
        if name=='CameraLure':
            phase=t%0.45
            env=max(0.,min(1.,phase/.025,(.25-phase)/.04))
            value=.28*env*(math.sin(2*math.pi*1050*t)+.25*math.sin(2*math.pi*1575*t))
        else:
            filtered=.65*filtered+.35*rng.uniform(-1,1)
            env=min(1.,t/.06)*max(0.,1-t/duration)
            value=.7*env*filtered
        samples.append(int(max(-1,min(1,value))*32767))
    path=audio/(name+'.wav')
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    task=unreal.AssetImportTask();task.filename=str(path);task.destination_path='/Game/Prototype/Audio'
    task.automated=True;task.replace_existing=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
path='/Game/Prototype/M_CameraGas'
material=unreal.load_asset(path)
if material is None:
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_CameraGas','/Game/Prototype',unreal.Material,unreal.MaterialFactoryNew())
    material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided',True)
    color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant',unreal.LinearColor(.22,.42,.29,1))
    density=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionScalarParameter)
    density.set_editor_property('parameter_name','Density');density.set_editor_property('default_value',.12)
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(density,'',unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.recompile_material(material)
unreal.EditorAssetLibrary.save_asset(path)
for name in ['CameraLure','CameraGas']:
    asset=unreal.load_asset('/Game/Prototype/Audio/'+name)
    assert isinstance(asset,unreal.SoundWave),name
assert material is not None
unreal.log('CAMERA_ASSETS_READY: two original spatial mono sounds and translucent gas material')
