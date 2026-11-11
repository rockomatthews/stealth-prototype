"""Original paired prototype animation; preserve the source character rigs."""
import bpy,math,json,sys
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Grab';OUT.mkdir(parents=True,exist_ok=True)
report={}
def ease(a,b,t):
 x=max(0,min(1,(t-a)/(b-a)));return x*x*(3-2*x)
def limb(rig,upper,lower,end,target,pole):
 bpy.context.view_layer.update();u,l,e=[rig.pose.bones[n] for n in (upper,lower,end)]
 a,b,c=u.head.copy(),l.head.copy(),e.head.copy();um,lm=u.matrix.copy(),l.matrix.copy()
 n1=(b-a).length;n2=(c-b).length;target=Vector(target);direction=(target-a).normalized();distance=max(abs(n1-n2)+.05,min((target-a).length,n1+n2-.05));target=a+direction*distance
 along=(n1*n1-n2*n2+distance*distance)/(2*distance);normal=Vector(pole)-a;normal=normal-direction*normal.dot(direction)
 if normal.length<.00001:normal=direction.cross(Vector((1,0,0)) if abs(direction.x)<.8 else Vector((0,1,0)))
 normal.normalize();elbow=a+direction*along+normal*math.sqrt(max(0,n1*n1-along*along))
 for bone,mat,oldstart,oldend,newstart,newend in [(u,um,a,b,a,elbow),(l,lm,b,c,elbow,target)]:
  q=(oldend-oldstart).rotation_difference(newend-newstart).to_matrix().to_4x4();bone.matrix=Matrix.Translation(newstart)@q@Matrix.Translation(-oldstart)@mat;bpy.context.view_layer.update()
def rot(rig,name,x=0,y=0,z=0):
 bpy.context.view_layer.update();b=rig.pose.bones[name];m=b.matrix.copy();origin=b.head.copy()
 b.matrix=Matrix.Translation(origin)@Matrix.Rotation(math.radians(z),4,'Z')@Matrix.Rotation(math.radians(y),4,'Y')@Matrix.Rotation(math.radians(x),4,'X')@Matrix.Translation(-origin)@m
 bpy.context.view_layer.update()
def lerp(a,b,t):return tuple(Vector(a).lerp(Vector(b),t))
def orient_digit(rig,name,direction,old_direction=None):
 bpy.context.view_layer.update();bone=rig.pose.bones[name];rest=rig.data.bones[name]
 if old_direction is None:
  finger,joint,side=name.split('_');joint=int(joint)
  if joint<3:old_direction=rig.pose.bones[f'{finger}_{joint+1:02}_{side}'].head-bone.head
  else:
   rest_axis=rest.head_local-rig.data.bones[f'{finger}_02_{side}'].head_local
   old_direction=(bone.matrix@rest.matrix_local.inverted()).to_3x3()@rest_axis
 q=Vector(old_direction).rotation_difference(Vector(direction));origin=bone.head.copy()
 bone.matrix=Matrix.Translation(origin)@q.to_matrix().to_4x4()@Matrix.Translation(-origin)@bone.matrix;bpy.context.view_layer.update()
def hand_pose(rig,side,forward,across,angles,thumb_target=None):
 for bone in rig.pose.bones:
  if bone.name.endswith('_'+side) and bone.name.startswith(('index_','middle_','ring_','pinky_','thumb_')):bone.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();hand=rig.pose.bones['hand_'+side];wrist=hand.head.copy();rest=rig.data.bones
 f=(rest['middle_01_'+side].head_local-rest[hand.name].head_local).normalized();a=rest['index_01_'+side].head_local-rest['pinky_01_'+side].head_local;a=(a-f*a.dot(f)).normalized()
 src=Matrix((a,f,a.cross(f))).transposed();df=Vector(forward).normalized();da=Vector(across);da=(da-df*da.dot(df)).normalized();normal=da.cross(df)
 dst=Matrix((da,df,normal)).transposed();hand.matrix=Matrix.Translation(wrist)@(dst@src.inverted()).to_4x4()@rest[hand.name].matrix_local.to_quaternion().to_matrix().to_4x4();bpy.context.view_layer.update()
 for finger in ['index','middle','ring','pinky']:
  total=0
  for joint,angle in enumerate(angles.get(finger,angles['default']),1):
   total+=angle;direction=Matrix.Rotation(math.radians(total),3,da)@df
   orient_digit(rig,f'{finger}_{joint:02}_{side}',direction)
 palm=(rig.pose.bones['middle_01_'+side].head+wrist)*.5
 tip=palm+normal*6.2+df+da*2.5 if thumb_target is None else palm+df*thumb_target[0]+da*thumb_target[1]+normal*thumb_target[2]
 length=rest['thumb_03_'+side].length;direction=df if side=='r' else normal
 limb(rig,'thumb_01_'+side,'thumb_02_'+side,'thumb_03_'+side,tip-direction*length,wrist+da*8+normal*4)
 orient_digit(rig,'thumb_03_'+side,tip-rig.pose.bones['thumb_03_'+side].head)
 # Distribute pronation through the forearm instead of twisting only the wrist
 # seam. The hand frame and all finger contact points remain fixed in space.
 lower=rig.pose.bones['lowerarm_'+side];saved=hand.matrix.copy();elbow=lower.head.copy();axis=(hand.head-elbow).normalized()
 current=(lower.matrix@rest[lower.name].matrix_local.inverted()).to_3x3()@a.cross(f)
 current=current-axis*current.dot(axis);target=normal-axis*normal.dot(axis)
 if current.length>.0001 and target.length>.0001:
  current.normalize();target.normalize();angle=math.atan2(axis.dot(current.cross(target)),current.dot(target));angle=max(-math.pi*.55,min(math.pi*.55,angle*.85))
  lower.matrix=Matrix.Translation(elbow)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-elbow)@lower.matrix;bpy.context.view_layer.update();hand.matrix=saved;bpy.context.view_layer.update()
 return palm,normal
GRIP_POSES=json.loads((P/'Art/FittedCharacters/grip-poses.json').read_text()) if (P/'Art/FittedCharacters/grip-poses.json').exists() else {}
def gun_hand(rig,side):
 # Absolute phalanx directions, not another curl added to a curled bind pose.
 # Index-to-pinky runs vertically on the pistol grip; support fingers run across
 # the handguard with the thumb on the opposite side.
 angles={'default':(85,60,25)} if side=='r' else {'default':(90,10,50)}
 angles.update(GRIP_POSES.get(side,{}).get('angles',{}))
 if side=='r':return hand_pose(rig,side,(0,-1,0),(0,0,1),angles,GRIP_POSES.get(side,{}).get('thumb_target'))
 return hand_pose(rig,side,(-1,0,0),(0,1,0),angles,GRIP_POSES.get(side,{}).get('thumb_target',(-4.6,1,2.8)))
def blend_hand_axes(f0,a0,f1,a1,w):
 f0=Vector(f0);a0=Vector(a0);f1=Vector(f1);a1=Vector(a1)
 q0=Matrix((a0,f0,a0.cross(f0))).transposed().to_quaternion();q1=Matrix((a1,f1,a1.cross(f1))).transposed().to_quaternion();q=q0.slerp(q1,w)
 return q@Vector((0,1,0)),q@Vector((1,0,0))
def neck_hand(rig,side,hook=False,release=0):
 if side=='r':return hand_pose(rig,side,(1,0,0),(0,0,1),{'default':(85*(1-release),65*(1-release),25*(1-release))},(2,2,3))
 if hook:return hand_pose(rig,side,(0,-1,0),(0,0,1),{'default':(60*(1-release),35*(1-release),20*(1-release))},(2,2,3))
 return hand_pose(rig,side,(-1,0,0),(0,0,1),{'default':(75*(1-release),50*(1-release),25*(1-release))},(2,2,3))
NECK_FIT=json.loads((P/'Art/FittedCharacters/neck-contact.json').read_text()) if (P/'Art/FittedCharacters/neck-contact.json').exists() else {'offset':[0,0,0],'pole_angles':[0,0]}
def animate(name,spy,kind,duration):
 label='Spy' if spy else 'Merc';source=P/'Art/FittedCharacters'/f'{label}_fitted.blend'
 if not source.exists():source=P/'Art/RiggedCharacters'/f'{label}_rigged.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01;scene.render.fps=30
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 mesh=next(o for o in scene.objects if o.type=='MESH')
 foot_groups={g.index for g in mesh.vertex_groups if g.name.startswith(('foot_','ball_'))}
 sole_vertices=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in foot_groups)>.5]
 scene.frame_start=1;scene.frame_end=round(duration*30)+1
 for frame in range(1,scene.frame_end+1):
  t=(frame-1)/30
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  # Shared 40 cm root spacing: right forearm across throat, left hand locks
  # the right upper arm. Every entry and specialty starts from this exact pose.
  right=(-7,-57,151) if spy else (-12,-26,133)
  left=(6,-55.5,154) if spy else (-3.7,-50.1,132.8)
  if spy:
   hold=1-ease(.55,1.6,t) if kind=='ChokeExit' else 1
   rot(rig,'spine_01',20)
   for side in ['r','l']:
    bone=rig.pose.bones['clavicle_'+side];m=bone.matrix.copy();m.translation+=Vector((0,-8,0))*hold;bone.matrix=m
   bone=rig.pose.bones['neck_01'];m=bone.matrix.copy();m.translation+=Vector((0,4,0))*hold;bone.matrix=m
   bpy.context.view_layer.update()
  if not spy and kind!='Panic':
   for side in ['r','l']:
    bone=rig.pose.bones['clavicle_'+side];m=bone.matrix.copy();m.translation+=Vector((0,-10,0));bone.matrix=m
   bpy.context.view_layer.update()
  if kind=='Snap':
   w=ease(.18,.5,t);rot(rig,'spine_03',0,0,(-12 if spy else 12)*w)
   if spy:right=(-7,-57,151+2*w);left=(6,-55.5,154+2*w)
   else:rot(rig,'head',0,20*w,38*w);rot(rig,'neck_01',0,0,12*w)
  elif kind in ['BackChoke','ChokeExit','ChokeFall']:
   # Five seconds of live merc control, followed by a paired forward collapse.
   exit_only=kind=='ChokeExit';fall_only=kind=='ChokeFall'
   clock=t+5 if exit_only or fall_only else t
   mount=ease(0,.55,clock);fall=ease(5,5.8,clock);release=ease(5.1,5.5,clock);rise=ease(5.55,6.6,clock)
   if spy:
    pelvis=rig.pose.bones['pelvis'];m=pelvis.matrix.copy()
    m.translation+=Vector((45*release*(1-rise),-3*mount-23*fall*(1-rise),12*mount-72*fall*(1-rise)-12*rise));pelvis.matrix=m
    rot(rig,'pelvis',58*fall*(1-rise));rot(rig,'spine_01',-20*rise+6*mount+12*fall*(1-rise))
    # Opposed hooks: knees either side of his hips; ankles cross in front.
    rfoot=lerp((-14,1,8),(7,-58,84),mount);lfoot=lerp((14,1,8),(-7,-55,88),mount)
    if exit_only:
     rfoot=lerp(rfoot,(-45,-8,75),ease(5.1,5.45,clock))
     rfoot=lerp(rfoot,(35,-7,8),ease(5.45,5.85,clock))
    else:rfoot=lerp(rfoot,(35,-7,8),release)
    lfoot=lerp(lfoot,(68,-24,8),release)
    rfoot=lerp(rfoot,(-14,1,8),rise);lfoot=lerp(lfoot,(14,1,8),rise)
    limb(rig,'thigh_r','calf_r','foot_r',rfoot,lerp((-45,-30,104),(15,-35,55),release))
    limb(rig,'thigh_l','calf_l','foot_l',lfoot,lerp((45,-30,104),(75,-35,55),release))
    right=lerp(right,(38,-65,12),release);left=lerp(left,(74,-32,12),release)
    right=lerp(right,(-47,-15,104),rise);left=lerp(left,(47,-15,104),rise)
   else:
    # Preserve the anatomical hip/knee/ankle chain while pitching prone. The old
    # world-space foot targets folded the knees backwards under a rotated pelvis.
    # Knees buckle first, then unfold into the prone landing. Compute hip
    # height from the actual segment lengths so the early fall keeps the boots
    # at floor level instead of pitching a rigid, straight-legged plank.
    thigh_angle=90*fall-60*math.sin(math.pi*fall)
    knee_bend=85*math.sin(math.pi*fall)
    bones=rig.data.bones
    upper=(bones['calf_r'].head_local-bones['thigh_r'].head_local).length
    lower=(bones['foot_r'].head_local-bones['calf_r'].head_local).length
    hip_z=8+upper*math.cos(math.radians(thigh_angle))+lower*math.cos(math.radians(thigh_angle+knee_bend))+8*fall
    pelvis=rig.pose.bones['pelvis'];m=pelvis.matrix.copy();m.translation+=Vector((0,-23*fall,hip_z-(8+upper+lower)));pelvis.matrix=m
    rot(rig,'pelvis',88*fall);rot(rig,'head',-18*fall)
    for side in ['r','l']:
     rot(rig,'thigh_'+side,thigh_angle-88*fall);rot(rig,'calf_'+side,knee_bend)
    right=lerp(right,(-30,-78,25),fall);left=lerp(left,(30,-72,25),fall)
  elif kind=='Panic':
   tug=(.5-.5*math.cos(t*math.pi*4));rot(rig,'spine_01',12+5*tug);rot(rig,'spine_03',0,0,4*math.sin(t*math.pi*2));rot(rig,'head',20,-8*math.sin(t*math.pi*4),0)
   right=(-9,-23,100+8*tug);left=(11,-22,101-6*tug)
   limb(rig,'thigh_r','calf_r','foot_r',(-15,-2,8),(-25,-25,65));limb(rig,'thigh_l','calf_l','foot_l',(15,-2,8),(25,-25,65))
  elif kind=='Grenade':
   if spy:
    take=ease(.12,.55,t);pull=ease(.62,1.05,t);plant=ease(1.25,1.9,t);shove=ease(2.05,2.3,t);release=ease(2.3,2.8,t)
    # LEFT arm keeps a continuous neck hook. RIGHT steals, arms, inserts and shoves.
    # Pin ring is caught by the left glove without releasing the forearm hook.
    right=lerp(right,(-23,-37,108),take)
    right=lerp(right,(-6.5,-55,155),ease(.55,.77,t))
    right=lerp(right,(-25,-45,153),pull)
    right=lerp(right,(-8,-52,99),plant)
    right=lerp(right,(-16,-39,133),shove)
    right=lerp(right,(-16,-18,120),release)
    # Establish the replacement neck hook before the stealing hand leaves.
    left=lerp(left,(-12,-60.5,154),ease(0,.16,t))
    left=lerp(left,(-10,-60.5,154),ease(.55,.8,t))
    left=lerp(left,(-12,-60.5,154),pull)
    left=lerp(left,(-12,-60.5,154),plant)
    left=lerp(left,(16,-35,136),shove)
    left=lerp(left,(15,-18,120),release)
    rot(rig,'spine_01',14*plant*(1-shove))
    m=rig.pose.bones['pelvis'].matrix.copy();m.translation+=Vector((0,-5*plant*(1-shove),-4*plant*(1-shove)));rig.pose.bones['pelvis'].matrix=m;bpy.context.view_layer.update()
   else:
    bend=ease(1.4,2,t)*(1-ease(2.2,2.8,t));rot(rig,'spine_01',12*bend);rot(rig,'head',10*bend)
    for side,sign,phase in [('r',-1,0),('l',1,.5)]:
     step=max(0,min(1,(t-2.2)/.6));lift=max(0,math.sin((step*2+phase)*math.pi))*18*math.sin(step*math.pi)
     limb(rig,'thigh_'+side,'calf_'+side,'foot_'+side,(sign*15,-10*math.sin(step*math.pi*2+phase),8+lift),(sign*35,-35,65))
  rpole=Vector((-35,-65,151) if spy else (-49,-27,132));lpole=Vector((35,-55,151) if spy else (55,-10,113))
  if spy:
   weight=1-ease(.1,.55,t) if kind=='ChokeExit' else 1-ease(2.3,2.8,t) if kind=='Grenade' else 1
   right_weight=weight*(1-ease(.05,.55,t)) if kind=='Grenade' else weight
   right=Vector(right)+Vector(NECK_FIT['offset'])*right_weight;left=Vector(left)+Vector(NECK_FIT['offset'])*weight
   if kind=='Grenade':rpole=rpole.lerp(Vector((-49,-27,132)),ease(.05,.55,t))
   for side,target,pole,factor,index in [('r',right,rpole,right_weight,0),('l',left,lpole,weight,1)]:
    shoulder=rig.pose.bones['upperarm_'+side].head;axis=(Vector(target)-shoulder).normalized();newpole=shoulder+Matrix.Rotation(math.radians(NECK_FIT['pole_angles'][index]*factor),3,axis)@(pole-shoulder)
    if side=='r':rpole=newpole
    else:lpole=newpole
  limb(rig,'upperarm_r','lowerarm_r','hand_r',right,rpole);limb(rig,'upperarm_l','lowerarm_l','hand_l',left,lpole)
  for side in ['r','l']:
   hand=rig.pose.bones['hand_'+side];rest=rig.data.bones[hand.name]
   if not spy:
    forward=(rig.data.bones['middle_01_'+side].head_local-rest.head_local).normalized()
    across=rig.data.bones['index_01_'+side].head_local-rig.data.bones['pinky_01_'+side].head_local;across=(across-forward*across.dot(forward)).normalized()
    src=Matrix((across,forward,across.cross(forward))).transposed()
    df=Vector((0,-.15,-1) if side=='r' else (-1,0,0)).normalized();da=Vector((0,-1,.15) if side=='r' else (0,1,0)).normalized();dst=Matrix((da,df,da.cross(df))).transposed()
    hand.matrix=Matrix.Translation(hand.head)@(dst@src.inverted()).to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
   else:
    direction=Vector((1,0,0) if side=='r' else (-1,0,-.3))
    if kind=='Grenade' and side=='r':direction=Vector((1,0,0)).lerp(Vector((0,0,-1)),ease(.1,.55,t))
    if kind=='ChokeExit':direction=direction.lerp(Vector((0,-1,0)),ease(.2,.5,t))
    q=(rest.tail_local-rest.head_local).rotation_difference(direction)
    hand.matrix=Matrix.Translation(hand.head)@q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
   bpy.context.view_layer.update()
  for side in ([] if kind=='ChokeFall' else ['r','l']):
   foot=rig.pose.bones['foot_'+side];position=foot.head.copy();foot.matrix=Matrix.Translation(position)@rig.data.bones[foot.name].matrix_local.to_quaternion().to_matrix().to_4x4();bpy.context.view_layer.update()
  for side in ['r','l']:
   index=rig.data.bones['index_01_'+side].head_local;pinky=rig.data.bones['pinky_01_'+side].head_local;middle=rig.data.bones['middle_01_'+side].head_local
   rest=rig.data.bones['hand_'+side];across=(index-pinky).normalized();forward=(middle-rest.head_local).normalized()
   if across.cross(forward).z>0:across=-across
   axis=(rig.pose.bones['hand_'+side].matrix.to_quaternion()@rest.matrix_local.to_quaternion().inverted())@across
   for finger in ['index','middle','ring','pinky']:
    for joint,angle in ([(1,22),(2,32),(3,18)] if spy else [(1,45),(2,85),(3,55)]):
     bone=rig.pose.bones[f'{finger}_{joint:02}_{side}'];origin=bone.head.copy()
     bone.matrix=Matrix.Translation(origin)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-origin)@bone.matrix;bpy.context.view_layer.update()
  if not spy:
   gun_hand(rig,'r');gun_hand(rig,'l')
  else:
   if kind=='Grenade':
    w=ease(.1,.32,t);df=Vector((1,0,0)).slerp(Vector((0,0,-1)),w);da=Vector((0,0,1)).lerp(Vector((0,-1,0)),w);angles=tuple(a+(b-a)*w for a,b in zip((85,65,25),(85,35,35)));hand_pose(rig,'r',df,da,{'default':angles},(2,2,3))
   else:neck_hand(rig,'r',release=ease(.15,.55,t) if kind=='ChokeExit' else 0)
   if kind=='Grenade':
    w=ease(0,.2,t);df,da=blend_hand_axes((-1,0,0),(0,0,1),(0,1,0),(0,0,-1),w);angles=tuple(a+(b-a)*w for a,b in zip((75,50,25),(70,30,20)));hand_pose(rig,'l',df,da,{'default':angles},(2,2,3))
   else:neck_hand(rig,'l',release=ease(.15,.55,t) if kind=='ChokeExit' else 0)
  if kind=='ChokeFall' and sole_vertices:
   bpy.context.view_layer.update();evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());surface=evaluated.to_mesh()
   minimum=min(surface.vertices[i].co.z for i in sole_vertices);evaluated.to_mesh_clear()
   # Ground against the rendered boot surface, not only the ankle bone.
   if minimum<0:
    pelvis=rig.pose.bones['pelvis'];m=pelvis.matrix.copy();m.translation.z-=minimum;pelvis.matrix=m;bpy.context.view_layer.update()
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=frame);b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('rotation_euler',frame=frame);b.keyframe_insert('scale',frame=frame)
 scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')));report[name]={'seconds':duration,'frames':scene.frame_end,'bones':len(rig.pose.bones)}
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if selected and (OUT/'animation_build.json').exists():report.update(json.loads((OUT/'animation_build.json').read_text()))
for kind,duration in [('Hold',.1),('Snap',.85),('BackChoke',5.),('Grenade',2.8)]:
 if selected and kind not in selected:continue
 for spy in [True,False]:animate(('Spy' if spy else 'Merc')+kind,spy,kind,duration)
for name,spy,kind,duration in [('SpyChokeExit',True,'ChokeExit',1.6),('MercChokeFall',False,'ChokeFall',.8),('MercPanic',False,'Panic',1.)]:
 if not selected or kind in selected:animate(name,spy,kind,duration)
(OUT/'animation_build.json').write_text(json.dumps(report,indent=2));print('GRAB_ANIMATIONS_BUILT',json.dumps(report))
