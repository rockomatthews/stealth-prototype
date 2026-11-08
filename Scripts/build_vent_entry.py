"""Contact-authored rope mantle and matching all-fours vent locomotion (cm)."""
import bpy,math,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Actions';OUT.mkdir(parents=True,exist_ok=True)
source=(P/'Scripts/prepare_grab_animations.py').read_text();exec(source[source.index('def ease('):source.index('def animate(')],globals())
DURATION=3.2;FLOOR=780.;START_Z=674.;MESH_Z=-42.;LIP=60.;KNEE=68.
ROOT=[(0,0,0),(.5,0,0),(1.4,25,120),(1.65,25,150),(2.3,100,150),(3.2,140,150)]
def root_at(t):
 for a,b in zip(ROOT,ROOT[1:]):
  if t<=b[0]:
   s=max(0,min(1,(t-a[0])/(b[0]-a[0])));return a[1]+(b[1]-a[1])*s,START_Z+a[2]+(b[2]-a[2])*s
 return 140.,824.
def keys(t,values):
 for a,b in zip(values,values[1:]):
  if t<=b[0]:return a[1]+(b[1]-a[1])*ease(a[0],b[0],t)
 return values[-1][1]
def flat_foot(rig,side):
 b=rig.pose.bones['foot_'+side];b.matrix=Matrix.Translation(b.head)@rig.data.bones[b.name].matrix_local.to_quaternion().to_matrix().to_4x4();bpy.context.view_layer.update()
def flat_hand(rig,side,w):
 b=rig.pose.bones['hand_'+side];rest=rig.data.bones[b.name];q=(rest.tail_local-rest.head_local).rotation_difference(Vector((0,-1,0)))
 desired=(q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()).to_quaternion();b.matrix=Matrix.Translation(b.head)@b.matrix.to_quaternion().slerp(desired,w).to_matrix().to_4x4();bpy.context.view_layer.update()
def rope_stance(phase):
 phase%=1
 return 80-55*phase/.65 if phase<.65 else 25+55*ease(.65,1,phase)
phase=(720-90)/84.61538
START_R=(-6,-28,rope_stance(phase+.5));START_L=(6,-28,rope_stance(phase));START_HAND_R=(-3,-40,rope_stance(phase)+80);START_HAND_L=(3,-40,rope_stance(phase+.5)+80)
def crawl_targets(t):
 # Opposite hands/knees recover together. The end of the mantle is this pose.
 result={}
 for side,offset in [('r',.5),('l',0.)]:
  p=(t+offset)%1;stance=p<.5;s=p*2 if stance else (p-.5)*2
  forward=75-50*s if stance else 25+50*ease(0,1,s)
  lift=0 if stance else 10*math.sin(s*math.pi)
  result['hand_'+side]=((-18 if side=='r' else 18),-forward,8+lift)
  result['foot_'+side]=((-16 if side=='r' else 16),-6+3*math.sin((p+.5)*2*math.pi),8+(0 if not stance else 4*math.sin(s*math.pi)))
 return result
report={};contact_samples=[];end_pose=None;handoff={}
for name,duration in [('SpyVentEntry',DURATION),('SpyVentCrawl',1.),('SpyVentIdle',.2)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters/Spy_rigged.blend'))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01;scene.render.fps=60
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 scene.frame_start=1;scene.frame_end=round(duration*60)+1
 rest_pelvis=rig.data.bones['pelvis'].head_local.copy();hip_delta=rig.data.bones['thigh_r'].head_local-rest_pelvis
 l1=(rig.data.bones['calf_r'].head_local-rig.data.bones['thigh_r'].head_local).length;l2=(rig.data.bones['foot_r'].head_local-rig.data.bones['calf_r'].head_local).length
 def knee_pelvis(fwd,rz):
  dz=FLOOR+10-(rz+MESH_Z);dy=(-KNEE+fwd)-(-10+hip_delta.y);dx=-16-hip_delta.x
  return dz+math.sqrt(max(1,l1*l1-dx*dx-dy*dy))-hip_delta.z
 for frame in range(1,scene.frame_end+1):
  t=(frame-1)/60
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  entry=name=='SpyVentEntry';fwd,rz=root_at(t) if entry else (140.,824.);visual_z=rz+MESH_Z
  if entry:
   if t<1.4:pelvis=keys(t,[(0,rest_pelvis.z),(.5,rest_pelvis.z),(1.4,knee_pelvis(*root_at(1.4)))])
   elif t<=2.15:pelvis=knee_pelvis(fwd,rz)
   else:pelvis=keys(t,[(2.15,knee_pelvis(*root_at(2.15))),(3.2,30.)])
   lean=keys(t,[(0,0),(.5,18),(1.4,102),(2.4,102),(3.2,85)])
   py=keys(t,[(0,rest_pelvis.y),(.5,-4),(1.4,-10),(3.2,-10)])
  else:pelvis=30.;lean=85.;py=-10.
  m=rig.pose.bones['pelvis'].matrix.copy();m.translation+=Vector((0,py-rest_pelvis.y,pelvis-rest_pelvis.z));rig.pose.bones['pelvis'].matrix=m
  rot(rig,'spine_01',lean*.45);rot(rig,'spine_02',lean*.35);rot(rig,'spine_03',lean*.2);rot(rig,'neck_01',-lean*.15);rot(rig,'head',-lean*.75)
  crawl=crawl_targets(0 if entry or name=='SpyVentIdle' else t)
  if entry:
   # Palms are world-anchored on the lip while the body rises beneath them.
   rforward=LIP if t<1.75 else LIP+(165-LIP)*ease(1.75,2.15,t)
   lforward=LIP+(115-LIP)*ease(1.4,1.75,t) if t<2.2 else 115+(215-115)*ease(2.2,3.2,t)
   rlift=16*math.sin(math.pi*max(0,min(1,(t-1.75)/.4))) if 1.75<t<2.15 else 0
   llift=16*math.sin(math.pi*max(0,min(1,(t-1.4)/.35))) if 1.4<t<1.75 else 10*math.sin(math.pi*max(0,min(1,(t-2.2)/1.0))) if t>2.2 else 0
   right=lerp(START_HAND_R,(-18,-(rforward-fwd),FLOOR+10+rlift-visual_z),ease(.05,.4,t));left=lerp(START_HAND_L,(18,-(lforward-fwd),FLOOR+10+llift-visual_z),ease(.2,.5,t))
   if t<=2.15:
    rfoot_world=(26.,FLOOR+10);w=ease(.65,1.4,t);rf=(-16,-(rfoot_world[0]-fwd),rfoot_world[1]-visual_z+16*math.sin(math.pi*w))
    right_foot=lerp((START_R[0],-(28-fwd),START_Z+MESH_Z+START_R[2]-visual_z),rf,w)
   else:
    w=ease(2.15,2.8,t);right_foot=(-16,-(26+(134-26)*w-fwd),FLOOR+10-visual_z+14*math.sin(math.pi*w))
   if t<1.4:lfwd=28.;lz=START_Z+MESH_Z+START_L[2]+(740-(START_Z+MESH_Z+START_L[2]))*ease(.5,1.4,t)
   elif t<2.05:
    w=ease(1.4,2.05,t);lfwd=28+(83-28)*w;lz=740+(790-740)*w+16*math.sin(math.pi*w)
   else:
    w=ease(2.75,3.2,t);lfwd=83+(134-83)*w;lz=790+10*math.sin(math.pi*w)
   left_foot=(16,-(lfwd-fwd),lz-visual_z)
   if t>2.8:
    right_foot=lerp(right_foot,crawl['foot_r'],ease(2.8,3.2,t));left_foot=lerp(left_foot,crawl['foot_l'],ease(2.8,3.2,t))
   limb(rig,'thigh_r','calf_r','foot_r',right_foot,lerp((-16,-(KNEE-fwd),FLOOR+10-visual_z),(-20,-40,8),ease(2.15,2.8,t)));limb(rig,'thigh_l','calf_l','foot_l',left_foot,(20,-40,8))
  else:
   right=crawl['hand_r'];left=crawl['hand_l'];limb(rig,'thigh_r','calf_r','foot_r',crawl['foot_r'],(-20,-40,8));limb(rig,'thigh_l','calf_l','foot_l',crawl['foot_l'],(20,-40,8))
  limb(rig,'upperarm_r','lowerarm_r','hand_r',right,(-45,-20,80));limb(rig,'upperarm_l','lowerarm_l','hand_l',left,(45,-20,80))
  for side in ['r','l']:flat_foot(rig,side);flat_hand(rig,side,ease(.2,.5,t) if entry else 1)
  for bone in rig.pose.bones:
   if bone.name.startswith(('index_','middle_','ring_','pinky_')):bone.rotation_mode='XYZ';bone.rotation_euler.x=math.radians(28*(1-ease(.15,.5,t))) if entry else 0
   bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('scale',frame=frame)
  if entry and frame%3==1:
   sample={'time':t,'root_forward':fwd,'root_z':rz}
   for bone in ['pelvis','head','hand_r','hand_l','calf_r','foot_l','upperarm_r','upperarm_l','lowerarm_r']:
    p=rig.pose.bones[bone].head;sample[bone]={'x':p.x,'forward':fwd-p.y,'z':visual_z+p.z}
   contact_samples.append(sample)
 if name=='SpyVentEntry':end_pose={b.name:b.matrix.copy() for b in rig.pose.bones}
 if name=='SpyVentCrawl':
  scene.frame_set(1);bpy.context.view_layer.update();handoff={'max_position_cm':max((b.matrix.translation-end_pose[b.name].translation).length for b in rig.pose.bones),'max_rotation_degrees':max(math.degrees(b.matrix.to_quaternion().rotation_difference(end_pose[b.name].to_quaternion()).angle) for b in rig.pose.bones)}
 scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 report[name]={'seconds':duration,'frames':scene.frame_end,'release_seconds':None}
existing=json.loads((OUT/'action-build.json').read_text()) if (OUT/'action-build.json').exists() else {};existing.update(report);(OUT/'action-build.json').write_text(json.dumps(existing,indent=2));(OUT/'vent-entry-contacts.json').write_text(json.dumps(contact_samples,indent=2))
(OUT/'vent-entry-profile.json').write_text(json.dumps({'duration':DURATION,'floor_z':FLOOR,'rope_body_to_lip':LIP,'root_keys':ROOT,'support':['reach lip','pull chest up','right knee on lip','shift weight inside','bring trailing leg through']},indent=2))
(OUT/'vent-entry-handoff.json').write_text(json.dumps(handoff,indent=2));print('VENT_ANIMATIONS_BUILT',json.dumps(report),json.dumps(handoff))
