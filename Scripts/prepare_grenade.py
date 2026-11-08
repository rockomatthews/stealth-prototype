"""Original simple grenade and removable safety pin; centimeters."""
import bpy,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Grab';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
parts=[]
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1);o=bpy.context.object;o.scale=(2.6,2.6,3.3);parts.append(o)
for loc,scale in [((0,0,3.5),(2,2,1.2)),((0,-.5,4.6),(.7,3.2,.45)),((0,-1.9,3.2),(.7,.45,2.8))]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale;parts.append(o)
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='SM_Grenade'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
def export(o,name):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},bake_anim=False,axis_forward='-Y',axis_up='Z')
export(body,'SM_Grenade')
bpy.ops.mesh.primitive_torus_add(major_radius=1.1,minor_radius=.16,major_segments=20,minor_segments=6,rotation=(math.pi/2,0,0));pin=bpy.context.object;pin.name='SM_GrenadePin';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);export(pin,'SM_GrenadePin')
print('GRENADE_MESHES_BUILT')
