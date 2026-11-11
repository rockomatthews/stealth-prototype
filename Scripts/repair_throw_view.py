"""Camera-only toss using the same reachable shoulder frame as rifle ready."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Actions'
s=(P/'Scripts/prepare_grab_animations.py').read_text();exec(s[s.index('def ease('):s.index('def animate(')],globals())
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/FittedCharacters/Merc_fitted.blend'))
scene=bpy.context.scene;scene.unit_settings.scale_length=.01;scene.render.fps=60;scene.frame_start=1;scene.frame_end=59
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('MercThrowView')
keys=[(0,(-12,-26,133),(-3.7,-50.1,132.8)),(.12,(-12,-24,133),(5,-26,133)),(.27,(-29,5,150),(15,-30,130)),(.42,(-14,-43,148),(18,-20,123)),(.58,(-8,-42,126),(18,-22,120)),(.76,(-12,-30,125),(-4,-40,130)),(58/60,(-12,-26,133),(-3.7,-50.1,132.8))]
for frame in range(1,60):
 t=(frame-1)/60
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
 for side in ['r','l']:
  bone=rig.pose.bones['clavicle_'+side];m=bone.matrix.copy();m.translation+=Vector((0,-10,-26));bone.matrix=m
 bpy.context.view_layer.update()
 for (a,r,l),(b,rr,ll) in zip(keys,keys[1:]):
  if a<=t<=b+1e-5:
   w=ease(a,b,t);right=lerp(r,rr,w);left=lerp(l,ll,w);break
 limb(rig,'upperarm_r','lowerarm_r','hand_r',right,(-35,-5,90));limb(rig,'upperarm_l','lowerarm_l','hand_l',left,(35,-5,90))
 gun_hand(rig,'r');gun_hand(rig,'l')
 if .04<t<.8:
  w=ease(.04,.12,t);angles=tuple(a+(b-a)*w for a,b in zip(GRIP_POSES['r']['angles']['middle'],(85,35,35)))
  if t>.42:angles=tuple(a+(b-a)*ease(.42,.57,t) for a,b in zip(angles,(0,10,10)))
  hand_pose(rig,'r',(0,-1,0),(0,0,1),{'default':angles},(1,2.5,8))
 for bone in rig.pose.bones:
  bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('scale',frame=frame)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'MercThrowView.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
print('REACHABLE_THROW_VIEW_BUILT')
