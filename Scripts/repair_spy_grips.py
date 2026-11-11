"""Fit the launcher draw to the rebuilt gloves without changing Y controls."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Equipment'
s=(P/'Scripts/prepare_grab_animations.py').read_text();exec(s[s.index('def ease('):s.index('def animate(')],globals())
cfg=json.loads((P/'Art/FittedCharacters/launcher-poses.json').read_text()) if (P/'Art/FittedCharacters/launcher-poses.json').exists() else {}
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/FittedCharacters/Spy_fitted.blend'));scene=bpy.context.scene;scene.render.fps=30;scene.unit_settings.scale_length=.01;scene.frame_start=1;scene.frame_end=22
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('SpyEquip')
for frame in range(1,23):
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();w=ease(.15,.7,(frame-1)/30)
 limb(rig,'upperarm_r','lowerarm_r','hand_r',lerp((-12,18,149),(-12,-26,133),w),(-60,-5,120))
 limb(rig,'upperarm_l','lowerarm_l','hand_l',lerp((25,-20,128),(-3.15,-50.75,132.65),w),(60,-5,120))
 for side in ['r','l']:
  angles={'default':(85,25,35) if side=='r' else (70,60,40),'index':(10,20,20) if side=='r' else (70,60,40)};angles.update(cfg.get(side,{}).get('angles',{}))
  hand_pose(rig,side,(0,-1,0) if side=='r' else (-1,0,0),(0,0,1) if side=='r' else (0,1,0),angles,(1,2.5,7) if side=='r' else (-4.6,1,2.8))
 for bone in rig.pose.bones:
  bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('scale',frame=frame)
scene.frame_set(22);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'SpyEquip.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SpyEquip.blend'));print('SPY_LAUNCHER_GRIPS_FITTED')
