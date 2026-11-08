"""Blender 4.5: derive independent goggles, launcher and rigged carbine.
Original rig/source files stay untouched. All measurements are centimeters.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Equipment';OUT.mkdir(parents=True,exist_ok=True)
report={}
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def export(name,objs,anim=False):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},
  add_leaf_bones=False,use_armature_deform_only=False,bake_anim=anim,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
  bake_anim_simplify_factor=0.,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
def cap(mesh):
 bm=bmesh.new();bm.from_mesh(mesh)
 edges=[e for e in bm.edges if e.is_boundary]
 if edges:
  result=bmesh.ops.holes_fill(bm,edges=edges,sides=0)
  for face in result['faces']:
   face.material_index=len(mesh.materials)-1
   for v in face.verts:
    if 162<v.co.z<176 and abs(v.co.x)<11:v.co.y=max(v.co.y,-8.5)
 bm.to_mesh(mesh);bm.free();mesh.update()
def remove_faces(mesh,predicate):
 bm=bmesh.new();bm.from_mesh(mesh)
 faces=[f for f in bm.faces if predicate(f.calc_center_median())]
 bmesh.ops.delete(bm,geom=faces,context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(mesh);bm.free();mesh.update()
# Separate the moving binocular body; the head strap and top mount stay fixed.
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters/Spy_rigged.blend'))
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
body=next(o for o in scene.objects if o.type=='MESH');rig=next(o for o in scene.objects if o.type=='ARMATURE')
goggle_region=lambda v:163<v.z<175 and v.y<-12
part=body.copy();part.data=body.data.copy();scene.collection.objects.link(part);part.name='SM_Goggles'
world=part.matrix_world.copy();part.parent=None;part.matrix_world=world;part.modifiers.clear();part.vertex_groups.clear()
remove_faces(part.data,lambda c:not goggle_region(c))
dark=bpy.data.materials.new('OpticGlass');part.data.materials.append(dark)
for face in part.data.polygons:
 if face.center.y<-22:face.material_index=len(part.data.materials)-1
for v in part.data.vertices:v.co-=Vector((0,-11,174))
part.matrix_world=Matrix.Identity(4)
export('Goggles',[part])
bpy.data.objects.remove(part,do_unlink=True)
remove_faces(body.data,lambda c:163<c.z<175 and c.y<-8.5 and abs(c.x)<10.5)
# Remove only the old fused launcher grip above the retained back holster.
remove_faces(body.data,lambda c:-24<c.x<-2 and c.y>11 and c.z>141)
body.data.materials.append(bpy.data.materials.new('FabricRepair'));cap(body.data)
# Replace the discarded rear eyecups with small visible eyes in the balaclava opening.
eye_white=bpy.data.materials.new('EyeWhite');eye_white.diffuse_color=(.55,.52,.45,1)
iris_mat=bpy.data.materials.new('Iris');iris_mat.diffuse_color=(.012,.018,.012,1)
eyes=[]
for x in [-3.4,3.4]:
 for material,loc,scale in [(eye_white,(x,-9.5,168),(.92,.3,.38)),(iris_mat,(x,-9.79,168),(.28,.09,.28))]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc)
  eye=bpy.context.object;eye.scale=scale;active(eye);bpy.ops.object.transform_apply(location=True,rotation=False,scale=True)
  eye.data.materials.append(material);group=eye.vertex_groups.new(name='head');group.add(list(range(len(eye.data.vertices))),1.,'REPLACE')
  eyes.append(eye)
active(body)
for eye in eyes:eye.select_set(True)
bpy.ops.object.join()
body.name='SK_SpyEquipment';export('SpyEquipment',[rig,body])
report['spy_triangles']=sum(len(f.vertices)-2 for f in body.data.polygons)
# Author a shoulder reach -> two-handed ready pose, layered over locomotion.
def pose_hand(side,target,pole):
 upper=rig.pose.bones['upperarm_'+side];lower=rig.pose.bones['lowerarm_'+side];hand=rig.pose.bones['hand_'+side]
 a=rig.data.bones[upper.name].head_local.copy();b=rig.data.bones[lower.name].head_local.copy();c=rig.data.bones[hand.name].head_local.copy()
 l1=(b-a).length;l2=(c-b).length;target=Vector(target);direction=(target-a).normalized();distance=min((target-a).length,l1+l2-.5)
 target=a+direction*distance;along=(l1*l1-l2*l2+distance*distance)/(2*distance)
 normal=Vector(pole)-a;normal=(normal-direction*normal.dot(direction)).normalized()
 elbow=a+direction*along+normal*math.sqrt(max(0,l1*l1-along*along))
 for bone,old_start,old_end,new_start,new_end in [(upper,a,b,a,elbow),(lower,b,c,elbow,target)]:
  delta=(old_end-old_start).rotation_difference(new_end-new_start).to_matrix().to_4x4()
  bone.matrix=Matrix.Translation(new_start)@delta@Matrix.Translation(-old_start)@rig.data.bones[bone.name].matrix_local
  bpy.context.view_layer.update()
 # Align palm/fingers along the barrel, and curl around the grip.
 rest=rig.data.bones[hand.name];direction_old=rest.tail_local-rest.head_local
 q=direction_old.rotation_difference(Vector((0,-1,0)))
 hand.matrix=Matrix.Translation(target)@q.to_matrix().to_4x4()@rest.matrix_local.to_quaternion().to_matrix().to_4x4()
 bpy.context.view_layer.update()
 for bone in rig.pose.bones:
  if any(bone.name.startswith(f+'_'+str(i).zfill(2)+'_') for f in ['index','middle','ring','pinky'] for i in [1,2,3]):
   bone.rotation_mode='XYZ';bone.rotation_euler.x=math.radians(32)
def save_equip(name,reach_r,reach_l,hold_r,hold_l):
 rig.animation_data_clear();rig.animation_data_create();action=bpy.data.actions.new(name);rig.animation_data.action=action
 scene.frame_start=1;scene.frame_end=22;scene.render.fps=30
 for frame,t in [(1,0),(7,0),(22,1)]:
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  for side,start,end,pole in [('r',reach_r,hold_r,(-60,-5,120)),('l',reach_l,hold_l,(60,-5,120))]:
   pose_hand(side,Vector(start).lerp(Vector(end),t),pole)
  for bone in rig.pose.bones:
   bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('scale',frame=frame)
 report[name+'_grip']={'right':list(rig.pose.bones['hand_r'].head),'left':list(rig.pose.bones['hand_l'].head),
  'support_error_cm':(rig.pose.bones['hand_l'].head-rig.pose.bones['hand_r'].head-Vector((2,-17,0))).length}
 if report[name+'_grip']['support_error_cm']>5:raise RuntimeError('Support hand misses weapon: '+str(report[name+'_grip']))
 export(name,[rig],True)
 rig.animation_data_clear()
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
save_equip('SpyEquip',(-12,18,149),(25,-20,128),(-12,-26,133),(-10,-43,133))
save_equip('MercEquip',(-14,-18,113),(18,-22,114),(-12,-26,133),(-10,-43,133))
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SpyEquipment.blend'))
# Equipment gets an independent rigid skeleton: grip, muzzle, trigger, bolt and magazine.
def make_rig(objects,name,muzzle):
 arm=bpy.data.armatures.new(name+'Skeleton');r=bpy.data.objects.new('root',arm);scene.collection.objects.link(r);active(r)
 bpy.ops.object.mode_set(mode='EDIT')
 for n,pos,parent in [('weapon_root',(0,0,0),None),('grip',(0,0,0),'weapon_root'),('muzzle',muzzle,'weapon_root'),('bolt',(8,0,6),'weapon_root'),('trigger',(3,0,-1),'weapon_root'),('magazine',(9,0,-5),'weapon_root')]:
  b=arm.edit_bones.new(n);b.head=pos;b.tail=Vector(pos)+Vector((0,0,3))
  if parent:b.parent=arm.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT')
 for o in objects:
  group=o.vertex_groups.new(name='weapon_root');group.add(list(range(len(o.data.vertices))),1,'REPLACE')
  m=o.modifiers.new('Weapon skeleton','ARMATURE');m.object=r;o.parent=r
 # A short bolt stroke drives actual skeletal recoil, with an explicit muzzle bone.
 r.animation_data_create();r.animation_data.action=bpy.data.actions.new(name+'Fire')
 scene.frame_start=1;scene.frame_end=7;scene.render.fps=30
 for frame,offset in [(1,0),(2,-2.8),(4,-1),(7,0)]:
  r.pose.bones['weapon_root'].location=(offset,0,0)
  r.pose.bones['bolt'].location=(offset*.5,0,0)
  for bone in r.pose.bones:
   bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('scale',frame=frame)
 scene.frame_set(1);export(name,[r]+objects,True)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
 return r
# Make a compact contemporary nonlethal launcher; base at the pistol grip.
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
parts=[]
def box(name,loc,scale):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);parts.append(o);return o
def barrel(name,loc,radius,length):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=length,location=loc,rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=name;active(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);parts.append(o);return o
box('Receiver',(8,0,5),(23,5.5,8));box('Grip',(-1,0,-4),(5,4.5,10));box('Foregrip',(18,0,-.5),(8,5,4));box('Rail',(6,0,10),(17,2.2,1))
barrel('LauncherBarrel',(23,0,5),2.4,14);barrel('Muzzle',(30,0,5),2.8,2)
box('RearSight',(-2,0,12),(2,3,3));box('FrontSight',(17,0,12),(2,2,2));box('TriggerGuard',(3,0,-3),(5,1.8,1));box('TriggerGuardFront',(5,0,-1),(1.5,1.8,5))
active(parts[0])
for o in parts:o.select_set(True)
bpy.ops.object.join();launcher=bpy.context.object;world=launcher.matrix_world.copy()
for v in launcher.data.vertices:v.co=world@v.co
launcher.matrix_world=Matrix.Identity(4);launcher.name='SK_Launcher'
make_rig([launcher],'Launcher',(31,0,5));report['launcher_triangles']=sum(len(f.vertices)-2 for f in launcher.data.polygons)
# Optimize the supplied carbine, preserve UVs, and place its grip at the origin.
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
fbx=next((P/'Art/MeshySource').rglob('*Tactical_Frontline*.fbx'));bpy.ops.import_scene.fbx(filepath=str(fbx))
carbine=next(o for o in scene.objects if o.type=='MESH');active(carbine)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Source is meters, long axis X; original source is kept unchanged.
assert 70 < carbine.dimensions.x < 100, str(carbine.dimensions)
tri=sum(len(f.vertices)-2 for f in carbine.data.polygons);dec=carbine.modifiers.new('Gameplay reduction','DECIMATE');dec.ratio=24000/tri;bpy.ops.object.modifier_apply(modifier=dec.name)
# Receiver/grip is near the rear third. Barrel orientation verified in QA renders.
for v in carbine.data.vertices:v.co=Vector((18-v.co.x,-v.co.y,v.co.z-8))
carbine.name='SK_Carbine'
make_rig([carbine],'Carbine',(58,0,8));report['carbine_triangles']=sum(len(f.vertices)-2 for f in carbine.data.polygons)
# Build the camera-only forearms without retaining torso influences.
arm_script=P/'Scripts/build_first_person_arms.py'
exec(compile(arm_script.read_text(),str(arm_script),'exec'),{'__file__':str(arm_script),'__name__':'__main__'})
report['merc_arm_triangles']=json.loads((OUT/'first-person-arms-build.json').read_text())['triangles']
(OUT/'equipment_build_report.json').write_text(json.dumps(report,indent=2));print('EQUIPMENT_BUILT',json.dumps(report))
