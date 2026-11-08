"""Original paired prototype animation; preserve the source character rigs."""
import bpy,math,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Grab';OUT.mkdir(parents=True,exist_ok=True)
report={}
def ease(a,b,t):
 x=max(0,min(1,(t-a)/(b-a)));return x*x*(3-2*x)
def limb(rig,upper,lower,end,target,pole):
 bpy.context.view_layer.update();u,l,e=[rig.pose.bones[n] for n in (upper,lower,end)]
 a,b,c=u.head.copy(),l.head.copy(),e.head.copy();um,lm=u.matrix.copy(),l.matrix.copy()
 n1=(b-a).length;n2=(c-b).length;target=Vector(target);direction=(target-a).normalized();distance=max(.5,min((target-a).length,n1+n2-.5));target=a+direction*distance
 along=(n1*n1-n2*n2+distance*distance)/(2*distance);normal=Vector(pole)-a;normal=(normal-direction*normal.dot(direction)).normalized();elbow=a+direction*along+normal*math.sqrt(max(0,n1*n1-along*along))
 for bone,mat,oldstart,oldend,newstart,newend in [(u,um,a,b,a,elbow),(l,lm,b,c,elbow,target)]:
  q=(oldend-oldstart).rotation_difference(newend-newstart).to_matrix().to_4x4();bone.matrix=Matrix.Translation(newstart)@q@Matrix.Translation(-oldstart)@mat;bpy.context.view_layer.update()
def rot(rig,name,x=0,y=0,z=0):
 bpy.context.view_layer.update();b=rig.pose.bones[name];m=b.matrix.copy();origin=b.head.copy()
 b.matrix=Matrix.Translation(origin)@Matrix.Rotation(math.radians(z),4,'Z')@Matrix.Rotation(math.radians(y),4,'Y')@Matrix.Rotation(math.radians(x),4,'X')@Matrix.Translation(-origin)@m
 bpy.context.view_layer.update()
def lerp(a,b,t):return tuple(Vector(a).lerp(Vector(b),t))
def animate(name,spy,kind,duration):
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters'/('Spy_rigged.blend' if spy else 'Merc_rigged.blend')))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01;scene.render.fps=30
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 scene.frame_start=1;scene.frame_end=round(duration*30)+1
 for frame in range(1,scene.frame_end+1):
  t=(frame-1)/30
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  right=(-7,-62,154) if spy else (-12,-17,151);left=(8,-59,151) if spy else (12,-17,150)
  if kind=='Snap':
   w=ease(.18,.5,t);rot(rig,'spine_03',0,0,(-18 if spy else 15)*w)
   if spy:right=(-9,-63,153);left=(8+12*w,-61,151+7*w)
   else:rot(rig,'head',0,25*w,50*w);rot(rig,'neck_01',0,0,18*w)
  elif kind=='Kick':
   kneel=ease(.6,1.2,t)
   if spy:
    reach=1-ease(.5,.85,t);right=(-12,-20-42*reach,132+22*reach);left=(15,-20-39*reach,132+19*reach)
    first=math.sin(math.pi*ease(.45,.95,t));second=math.sin(math.pi*ease(2.55,3.1,t))
    if first>.001:limb(rig,'thigh_r','calf_r','foot_r',(-12,-65*first,15+70*first),(-40,-70,100))
    if second>.001:limb(rig,'thigh_l','calf_l','foot_l',(12,-88*second,15+69*second),(40,-70,100))
    rot(rig,'spine_01',-12*max(first,second))
   else:
    pelvis=rig.pose.bones['pelvis'];m=pelvis.matrix.copy();m.translation+=Vector((0,-12*kneel,-56*kneel));pelvis.matrix=m
    rot(rig,'spine_01',28*kneel);rot(rig,'spine_02',24*kneel);rot(rig,'spine_03',15*kneel)
    impact=ease(2.8,3.1,t);rot(rig,'head',-32*impact,0,25*impact)
    right=lerp(right,(-22,-60,12),kneel);left=lerp(left,(22,-60,12),kneel)
    limb(rig,'thigh_r','calf_r','foot_r',(-15,30,8),(-15,-35,30));limb(rig,'thigh_l','calf_l','foot_l',(15,30,8),(15,-35,30))
  elif kind=='Grenade':
   if spy:
    take=ease(.15,.65,t);pull=ease(.85,1.2,t);plant=ease(1.25,1.9,t);shove=ease(2.,2.6,t)
    right=lerp(right,(-22,-66,112),take);right=lerp(right,(-10,-32,133),pull);right=lerp(right,(-5,-82,95),plant);right=lerp(right,(-16,-48,135),shove)
    left=lerp(left,(5,-32,133),pull);left=lerp(left,(14,-75,110),plant);left=lerp(left,(15,-48,135),shove);rot(rig,'spine_01',12*plant*(1-shove))
   else:
    bend=ease(1.4,2,t)*(1-ease(2.2,2.8,t));rot(rig,'spine_01',20*bend);rot(rig,'head',15*bend);right=(-15,-18,120);left=(15,-18,120)
  limb(rig,'upperarm_r','lowerarm_r','hand_r',right,(-65,-20,120));limb(rig,'upperarm_l','lowerarm_l','hand_l',left,(65,-20,120))
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=frame);b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('rotation_euler',frame=frame);b.keyframe_insert('scale',frame=frame)
 scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.,axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')));report[name]={'seconds':duration,'frames':scene.frame_end,'bones':len(rig.pose.bones)}
for kind,duration in [('Hold',.1),('Snap',.85),('Kick',3.1),('Grenade',3.8)]:
 for spy in [True,False]:animate(('Spy' if spy else 'Merc')+kind,spy,kind,duration)
(OUT/'animation_build.json').write_text(json.dumps(report,indent=2));print('GRAB_ANIMATIONS_BUILT',json.dumps(report))
