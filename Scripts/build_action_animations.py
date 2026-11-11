"""Original merc overhand toss and spy rope climbing on existing runtime rigs."""
import bpy,math,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Actions';OUT.mkdir(parents=True,exist_ok=True)
# Reuse the source-controlled limb solver without running the grab exports.
source=(P/'Scripts/prepare_grab_animations.py').read_text();ns={};exec(source[source.index('def ease('):source.index('def animate(')],globals())
report={}
for name,spy,duration in [('MercEquipView',False,.7),('MercThrowView',False,.9666667),('MercThrow',False,.9666667),('SpyRope',True,.8),('MercKnockout',False,.8)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters'/('Spy_rigged.blend' if spy else 'Merc_rigged.blend')))
 scene=bpy.context.scene;scene.render.fps=60;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 scene.frame_start=1;scene.frame_end=round(duration*60)+1
 for frame in range(1,scene.frame_end+1):
  t=(frame-1)/60
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  if name=='MercEquipView':
   w=ease(.2,.7,t);right=lerp((-14,-18,113),(-12,-26,133),w);left=lerp((18,-22,114),(-10,-43,133),w)
  elif name in ['MercThrow','MercThrowView']:
   # Pin-pull near chest -> right shoulder windup -> overhand release -> ready.
   keys=[(0,(-12,-26,133),(-10,-43,133)),(.12,(-12,-24,133),(5,-26,133)),(.27,(-29,7,158),(15,-30,130)),(.42,(-14,-65,154),(18,-20,123)),(.58,(-8,-52,126),(18,-22,120)),(.76,(-12,-30,125),(-10,-40,130)),(.9666667,(-12,-26,133),(-10,-43,133))]
   for i in range(len(keys)-1):
    if keys[i][0]<=t<=keys[i+1][0]+.0001:
     a,r,l=keys[i];b,rr,ll=keys[i+1];w=ease(a,b,t);right=lerp(r,rr,w);left=lerp(l,ll,w);break
   rot(rig,'spine_01',0,0,-8*math.sin(math.pi*min(1,t/.76)))
   rot(rig,'spine_03',4*math.sin(math.pi*min(1,t/.6)))
  elif name=='SpyRope':
   def stance(phase):
    phase%=1
    return 80-55*phase/.65 if phase<.65 else 25+55*ease(.65,1,phase)
   phase=t/.8;right=(-3,-40,stance(phase)+80);left=(3,-40,stance(phase+.5)+80)
   limb(rig,'thigh_r','calf_r','foot_r',(-6,-28,stance(phase+.5)),(-32,-40,90))
   limb(rig,'thigh_l','calf_l','foot_l',(6,-28,stance(phase)),(32,-40,90))
  else:
   w=ease(0,.6,t);m=rig.pose.bones['pelvis'].matrix.copy();m.translation+=Vector((0,15*w,-72*w));rig.pose.bones['pelvis'].matrix=m
   rot(rig,'spine_01',-45*w);rot(rig,'spine_02',-35*w);rot(rig,'spine_03',-10*w)
   right=lerp((-12,-26,133),(-35,40,14),w);left=lerp((-10,-43,133),(35,40,14),w)
   limb(rig,'thigh_r','calf_r','foot_r',(-22,-30,8),(-35,-45,40));limb(rig,'thigh_l','calf_l','foot_l',(22,-18,8),(35,-40,40))
  view=name in ['MercEquipView','MercThrowView']
  limb(rig,'upperarm_r','lowerarm_r','hand_r',right,(-30,0,55) if view else (-60,-2,135));limb(rig,'upperarm_l','lowerarm_l','hand_l',left,(30,0,55) if view else (60,-5,125))
  if name in ['MercEquipView','MercThrowView']:
   for side in ['r','l']:
    hand=rig.pose.bones['hand_'+side];rest=rig.data.bones[hand.name];q=(rest.tail_local-rest.head_local).rotation_difference(Vector((0,-1,0)))
    hand.matrix=Matrix.Translation(hand.head)@q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4();bpy.context.view_layer.update()
  if name in ['SpyRope','MercKnockout']:
   for side in ['r','l']:
    foot=rig.pose.bones['foot_'+side];where=foot.head.copy();rest=rig.data.bones[foot.name].matrix_local.to_quaternion().to_matrix().to_4x4()
    angle=math.radians(10 if side=='r' else -10) if name=='SpyRope' else 0
    foot.matrix=Matrix.Translation(where)@Matrix.Rotation(angle,4,'Z')@rest;bpy.context.view_layer.update()
  # Small finger curl keeps the hand around the grenade / rope instead of a flat palm.
  for bone in rig.pose.bones:
   if bone.name.startswith(('index_','middle_','ring_','pinky_')):bone.rotation_mode='XYZ';bone.rotation_euler.x=math.radians(28)
   bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('scale',frame=frame)
 scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 report[name]={'seconds':(scene.frame_end-1)/60,'frames':scene.frame_end,'release_seconds':.42 if name in ['MercThrow','MercThrowView'] else None}
(OUT/'action-build.json').write_text(json.dumps(report,indent=2));print('ACTION_ANIMATIONS_BUILT',json.dumps(report))

# Original short body-impact sound, synthesized rather than downloaded.
import wave,struct,random
rng=random.Random(19);rate=24000;samples=[];last=0
for i in range(int(rate*.24)):
 t=i/rate;last=last*.7+rng.uniform(-1,1)*.3;v=(math.sin(t*2*math.pi*78)*.55+last*.45)*math.exp(-21*t);samples.append(struct.pack('<h',int(max(-1,min(1,v))*27000)))
with wave.open(str(OUT/'DropImpact.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(samples))

# Mantle and vent locomotion are authored together to preserve their handoff.
throw_script=P/'Scripts/repair_throw_view.py'
exec(compile(throw_script.read_text(),str(throw_script),'exec'),{'__file__':str(throw_script),'__name__':'__main__'})
vent_script=P/'Scripts/build_vent_entry.py'
exec(compile(vent_script.read_text(),str(vent_script),'exec'),{'__file__':str(vent_script),'__name__':'__main__'})
