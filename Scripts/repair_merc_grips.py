"""Re-author only merc equipment poses, with actual thumb/finger closures."""
import bpy,math,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/UtilityRifle'
s=(P/'Scripts/prepare_grab_animations.py').read_text();exec(s[s.index('def ease('):s.index('def animate(')],globals())
for name,view in [('MercUtilityEquip',False),('MercUtilityEquipView',True)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters/Merc_rigged.blend'));scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01;scene.render.fps=30;scene.frame_start=1;scene.frame_end=22
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 for f in range(1,23):
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update();w=ease(.15,.7,(f-1)/30)
  # Shared shoulder protraction gives both views a reachable support grip.
  # Camera-only shoulder frame: keep both sleeve ends below/behind the
  # viewport while the hands retain the same physical weapon contacts.
  for side in ['r','l']:
   bone=rig.pose.bones['clavicle_'+side];m=bone.matrix.copy();m.translation+=Vector((0,-10,-26 if view else 0))*w;bone.matrix=m
  bpy.context.view_layer.update()
  limb(rig,'upperarm_r','lowerarm_r','hand_r',lerp((-14,-18,113),(-12,-26,133),w),(-30,0,55) if view else (-60,-2,125));limb(rig,'upperarm_l','lowerarm_l','hand_l',lerp((18,-22,114),(-3.7,-50.1,132.8),w),(30,0,55) if view else (60,-5,125))
  gun_hand(rig,'r');gun_hand(rig,'l')
  for b in rig.pose.bones:b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('scale',frame=f)
 scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
print('MERC_GRIPS_REPAIRED')
