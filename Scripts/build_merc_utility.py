"""Original heavy utility rifle, status display and anatomical grip; centimeters."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Art/UtilityRifle';OUT.mkdir(parents=True,exist_ok=True)
report={};parts=[]
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def export(name,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
mats={}
for name,color,metal,rough in [('Shell',(.012,.016,.020,1),.15,.47),('Metal',(.065,.075,.08,1),.8,.3),('Rubber',(.0035,.0045,.006,1),0,.82),('Panel',(.004,.006,.007,1),.1,.3),('Amber',(1,.38,.025,1),0,.3),('Glass',(.014,.03,.04,1),.6,.15)]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 if name=='Amber':bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=1.5
 else:
  noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Detail'].default_value=2
  bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1 if name=='Rubber' else .045;bump.inputs['Distance'].default_value=.018;m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 mats[name]=m
def finish(o,name,material='Shell',bevel=.25):
 o.name=name;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[material])
 if bevel:
  mod=o.modifiers.new('Machined edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 for poly in o.data.polygons:poly.use_smooth=True
 mod=o.modifiers.new('Area weighted surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50;bpy.ops.object.modifier_apply(modifier=mod.name)
 parts.append(o);return o
def box(name,loc,size,mat='Shell',bevel=.25):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size;return finish(o,name,mat,bevel)
def tube(name,loc,radius,length,mat='Metal'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=length,location=loc,rotation=(0,math.pi/2,0));return finish(bpy.context.object,name,mat,.1)
# Shaped, machined bullpup body. Original geometry inspired by the user's silhouette reference.
def profile(name,points,depth,y=-2,mat='Shell',bevel=.16):
 verts=[(x,y+side*depth/2,z) for side in [-1,1] for x,z in points];n=len(points)
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);return finish(o,name,mat,bevel)
def cut(o,cutter):
 active(o);mod=o.modifiers.new('Machined recess','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);parts.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)
def side_slot(o,x,z,length,height,depth=1.1):
 for side in [-1,1]:cut(o,box('Temporary pocket',(x,-2+side*4.4,z),(length,depth,height),'Panel',min(.22,height*.25)))
def y_cylinder(name,loc,r,length,mat='Metal',vertices=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=length,location=loc,rotation=(math.pi/2,0,0));return finish(bpy.context.object,name,mat,.045)
def screw(x,z,y=-6.58):
 head=y_cylinder('Recessed Torx fastener',(x,y,z),.38,.14,'Metal');socket=y_cylinder('Hex drive',(x,y-.08 if y<0 else y+.08,z),.17,.07,'Panel',6)
 return head
# Swept polygon profiles preserve a manufactured silhouette rather than stacked cubes.
body=profile('Monolithic upper receiver',[(-30,8),(-29,15.7),(-23,17),(-9,17),(0,16),(34,16),(43,13.5),(44,7.2),(39,5),(9,5),(5,3),(-5,3),(-8,5),(-26,5)],9,bevel=.32)
for x in [-17,-10,-3,4,11,18,25,32]:side_slot(body,x,13.5,4.3,.9)
for x in [8,15,22,29]:side_slot(body,x,9.4,4.6,1.3)
# Deep ejection recess, exposed bolt and a guarded charging channel on both sides.
for side in [-1,1]:
 y=-2+side*4.54
 cut(body,box('Ejection machining',(4,y,11.5),(16,1.2,2.2),'Panel',.24))
 box('Ejection channel interior',(4,y-side*.42,11.5),(15.6,.12,1.8),'Panel',.1)
 box('Bolt carrier',(5,y-side*.3,11.5),(8.2,.16,1.25),'Metal',.16)
 for x in [2.5,3.4,4.3,5.2,6.1]:box('Bolt serration',(x,y-side*.17,11.5),(.25,.12,1.25),'Panel',.02)
 box('Charging lever',(-8,y+side*.55,9.9),(5.2,1.4,.72),'Metal',.15)
 for x in [-9.5,-8.9,-8.3,-7.7]:box('Lever grip cut',(x,y+side*1.25,9.9),(.18,.12,.75),'Panel',.025)
 # Layered access plates with a thin recessed perimeter seam.
 profile('Lower access seam',[(-26,5.7),(-25,8.3),(-13,8.3),(-11,6.8),(-12,4.9),(-25,4.9)],.12,y,'Panel',.1)
 profile('Lower access cover',[(-25.5,5.8),(-24.7,7.9),(-13.3,7.9),(-11.6,6.7),(-12.3,5.25),(-24.7,5.25)],.16,y+side*.1,'Shell',.1)
 for x,z in [(-27,11),(-12,6),(0,7),(18,7),(38,8),(36,14)]:screw(x,z,y+side*.12)
# Stock and open thumbhole frame are shaped extrusions, not a filled slab.
profile('Sculpted stock',[(-32,-6.5),(-33,14),(-29,16.2),(-19,16.5),(-14,14.5),(-14,6),(-18,4.8),(-27,5.4),(-27,-2.7),(-18,-5.5),(-10,-5.5),(-10,-7.5),(-18,-8.5)],7.5,bevel=.55)
profile('Elastomer recoil pad',[(-34,-6.7),(-34.6,14.3),(-32.5,14.7),(-31.6,13.5),(-31,-5.8),(-32,-7.2)],8.5,mat='Rubber',bevel=.45)
profile('Cheek weld cushion',[(-30,17),(-28,19),(-15,19),(-11,17.5),(-12,16.1),(-28,16)],7.7,mat='Rubber',bevel=.65)
for z in [-4,-2,0,2,4,6,8,10,12]:box('Recoil pad traction',(-34.25,-2,z),(.25,8.2,.4),'Rubber',.1)
# Rear bullpup magazine and latch.
profile('Magazine well',[(-18,5),(-7,5),(-7,-1),(-9,-2),(-17,-2)],6.5,bevel=.3)
profile('Bullpup magazine',[(-16.7,1),(-8.3,1),(-8.7,-8.6),(-10,-9.9),(-15.8,-9.9),(-17,-8.4)],5.3,mat='Metal',bevel=.35)
for side in [-1,1]:
 for x in [-15.2,-13.1,-11]:box('Magazine stamped rib',(x,-2+side*2.7,-4.1),(.52,.18,6.8),'Shell',.18)
 box('Magazine latch',(-6.8,-2+side*3.9,.8),(1.4,.65,2.5),'Metal',.18)
box('Magazine bumper',(-12.6,-2,-9.5),(9.2,6,1.5),'Rubber',.4)
# Shift the bullpup magazine rearward to leave real thumb clearance behind the grip.
for part in parts:
 if part.name.startswith(('Magazine well','Bullpup magazine','Magazine stamped rib','Magazine latch','Magazine bumper')):part.location.x-=4.5
# Swept pistol grip and an actual open guard with curved bevels.
profile('Pistol grip',[(-3.7,4.1),(1.8,3.6),(1.1,0),(-1.9,-8.2),(-5,-9.7),(-9.1,-7.6),(-5.1,-1)],4.4,mat='Rubber',bevel=.6)
for side in [-1,1]:
 profile('Grip insert',[(-4.4,-.5),(-.4,-.7),(-2.9,-7.1),(-5.2,-8),(-7,-6.8)],.18,-2+side*2.2,'Shell',.18)
 for z in [-2,-3,-4,-5,-6]:box('Grip molded texture',(-4.6+(z+4)*.25,-2+side*2.34,z),(2.2,.1,.13),'Rubber',.04)
profile('Trigger guard bow',[(1,3),(9,3),(11.2,.7),(10.7,-3.8),(8.7,-5.7),(1.2,-5.7),(.5,-4.5),(8,-4.5),(9.2,-3.1),(9.4,0),(8.2,1.5),(1,1.5)],2.4,mat='Metal',bevel=.25)
profile('Curved trigger',[(3,2.3),(3.9,2.3),(3.5,.5),(4,-1.2),(5,-1.7),(4.8,-2.4),(3.2,-1.8),(2.5,.3)],.85,mat='Metal',bevel=.1)
# Front handguard: tapered, relieved panels, ergonomic scalloped underside.
fore=profile('Tapered handguard',[(13,6),(17,8),(36,8),(41,5.4),(40,1.4),(35,-.8),(17,-.8),(13,1.5)],8.4,bevel=.55)
for side in [-1,1]:
 y=-2+side*4.25
 profile('Fore-end inset',[(16,5.6),(19,6.6),(35,6.6),(38.2,4.8),(37.5,2.1),(34.5,1.1),(17,1.1)],.2,y,'Rubber',.3)
 for x in [18,19.5,21,22.5,24,25.5,27,28.5,30,31.5,33,34.5]:box('Fine handguard rib',(x,y+side*.14,3.8),(.42,.24,4.5),'Rubber',.12)
 for x in [17,35]:screw(x,3.8,y+side*.25)
# Palm support at existing anchor; curved frontstop and low-profile accessory rail.
profile('Palm swell',[(15,.7),(32,.7),(34,-.6),(31,-2.1),(19,-2.2),(15,-1)],6.6,y=1,mat='Rubber',bevel=.55)
profile('Handstop',[(33,1),(35,1),(36,-2.9),(34.6,-3.4),(33,-2.4)],5.8,y=1,mat='Rubber',bevel=.35)
for x in range(17,32,2):box('Underside grip rib',(x,1,-2.1),(.6,6.3,.38),'Rubber',.12)
# Continuous low rail with machined teeth and slender folded iron sights.
profile('Top rail spine',[(-20,16.3),(40,16.3),(40,17.4),(-18,17.4)],3.4,mat='Metal',bevel=.12)
for x in range(-18,40,2):box('Picatinny tooth',(x,-2,17.65),(.95,4.2,.65),'Metal',.09)
for x in [-14,38]:
 box('Sight hinge',(x,-2,18.6),(3,4.4,1.25),'Metal',.18)
 for y in [-3.5,-.5]:profile('Sight protective wing',[(x-1,18.5),(x-.6,22),(x+.3,22),(x+1.2,18.5)],.65,y,mat='Metal',bevel=.12)
 if x==38:box('Front sight post',(x,-2,20.4),(.55,.5,3.8),'Metal',.08)
 else:
  # Aperture ring, open center, along bore axis.
  ring=tube('Rear aperture',(x,-2,20.5),1.05,1,'Metal');cut(ring,tube('Aperture cutter',(x,-2,20.5),.58,2,'Panel'))
# Barrel, gas block and real open flash-hider slots.
tube('Barrel extension',(44,-2,10),1.7,9,'Metal');tube('Gas collar',(43,-2,10),2.1,2,'Shell')
muzzle=tube('Ported flash hider',(50,-2,10),2.1,6,'Metal');cut(muzzle,tube('Bore tool',(51,-2,10),1.15,7,'Panel'))
for z in [8.7,11.3]:
 for y in [-3.5,-.5]:cut(muzzle,box('Flash hider mill',(50,y,z),(3.7,1.4,1.1),'Panel',.16))
for x in [45,45.6,46.2]:tube('Barrel shoulder',(x,-2,10),1.8,.22,'Metal')
# Compact functional light, protected lens and cable to pressure pad.
box('Light mount',(31,3.4,9.1),(6,2.2,3),'Metal',.3)
tube('Weapon light',(33,4.5,9.1),1.7,10,'Metal');tube('Light bezel',(38.2,4.5,9.1),2,1.2,'Shell');tube('Coated reflector',(38.85,4.5,9.1),1.48,.15,'Glass')
for x in [29,30,31,32]:tube('Light knurl ring',(x,4.5,9.1),1.77,.24,'Rubber')
box('Pressure pad',(23,2.45,6.2),(6,.35,1.9),'Rubber',.3)
profile('Utility sensor guard',[(26,8),(37,8),(39,9),(38,12),(29,12),(26,10.5)],3,y=-8,bevel=.35)
tube('Sensor lens',(38.8,-8,10),.65,.18,'Glass')
# Small recessed selectors, pins, sling loops and restrained identification marks.
for side in [-1,1]:
 y=-2+side*4.7
 y_cylinder('Fire selector hub',(-1,y,5.3),.62,.3,'Metal');box('Selector lever',(-2,y+side*.17,5.3),(2,.25,.5),'Metal',.16)
 for x in [-24,31]:
  loop=box('Sling eye',(x,y,7),(2.6,.75,1.8),'Metal',.3);cut(loop,box('Sling hole',(x,y,7),(1.5,1.5,.8),'Panel',.2))
 def label(txt,x,z,size):
  bpy.ops.object.text_add(location=(x,y+side*.05,z));o=bpy.context.object;o.data.body=txt;o.data.size=size;o.data.extrude=.002
  # local text X follows barrel, local Y vertical; normal toward the side.
  o.rotation_euler=(math.pi/2 if side<0 else -math.pi/2,0,0);active(o);bpy.ops.object.convert(target='MESH');finish(o,'Laser etched '+txt,'Metal',0)
 label('WARDEN  /  UT-9',-23,14.3,.64);label('7.62   /   SECURITY SYSTEMS',-21,9.4,.34);label('S  |  1',-3,6.4,.36)
# Status panel integrated into the rear cheek housing, lower than the sightline.
profile('Integrated rear instrument housing',[(-34.7,12.8),(-30,19.4),(-25,18.5),(-25,13),(-31,12)],8.1,mat='Shell',bevel=.35)
frame=Matrix(((0,.625,-.7806,-32),(-1,0,0,-2),(0,.7806,.625,16.0),(0,0,0,1)))
def panelbox(name,local,size,mat):
 o=box(name,(0,0,0),size,mat,.14);o.matrix_world=frame@Matrix.Translation(Vector(local))
panelbox('Integrated display surround',(0,0,-.5),(7.4,8.2,1.3),'Shell');panelbox('Display gasket',(0,0,.18),(6.7,7.4,.2),'Rubber');panelbox('Recessed display glass',(0,0,.32),(6.2,6.9,.14),'Panel')
for i in range(7):panelbox('ROF amber segment',(-2.1+i*.7,0,.43),(.36,1.7,.05),'Amber')
for text,loc,size in [('ROF',(-2.1,2,.46),.86),('SEMI',(-2.1,-2.7,.46),.8)]:
 bpy.ops.object.text_add();o=bpy.context.object;o.data.body=text;o.data.size=size;o.data.extrude=.005;o.matrix_world=frame@Matrix.Translation(Vector(loc));active(o);bpy.ops.object.convert(target='MESH');finish(bpy.context.object,'Display '+text,'Amber',0)

for o in parts:
 active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for poly in o.data.polygons:poly.use_smooth=False
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT')
arm=bpy.data.armatures.new('MercUtilitySkeleton');rig=bpy.data.objects.new('root',arm);scene.collection.objects.link(rig);active(rig);bpy.ops.object.mode_set(mode='EDIT')
for n,pos,parent in [('weapon_root',(0,0,0),None),('grip',(0,-2,-3),'weapon_root'),('support_grip',(17.3,1,-5),'weapon_root'),('muzzle',(53,-2,10),'weapon_root'),('flashlight',(39,4.5,9.1),'weapon_root'),('laser',(39,-8,10),'weapon_root'),('bolt',(2,3,11),'weapon_root'),('trigger',(3,-2,-1),'weapon_root'),('magazine',(-13,-2,-3),'weapon_root')]:
 b=arm.edit_bones.new(n);b.head=pos;b.tail=Vector(pos)+Vector((0,0,3))
 if parent:b.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for o in parts:
 group=o.vertex_groups.new(name='bolt' if o.name.startswith('Charging handle') else 'weapon_root');group.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Rigid skin','ARMATURE');mod.object=rig;o.parent=rig
rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('MercUtilityFire');scene.render.fps=30;scene.frame_start=1;scene.frame_end=7
for f,offset in [(1,0),(2,-2.2),(4,-.8),(7,0)]:
 rig.pose.bones['weapon_root'].location.x=offset;rig.pose.bones['bolt'].location.x=offset*.7
 for b in rig.pose.bones:b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('scale',frame=f)
for o in parts:o.name='GEO_'+o.name.replace(' ','_')
scene.frame_set(1);export('MercUtility',[rig]+parts);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MercUtility.blend'))
report['triangles']=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in parts);report['parts']=len(parts);report['bones']=len(arm.bones)
source=(P/'Scripts/prepare_grab_animations.py').read_text();exec(source[source.index('def ease('):source.index('def animate(')],globals())
def hand_pose(r,side):
 gun_hand(r,side)
for name,view in [('MercUtilityEquip',False),('MercUtilityEquipView',True)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters/Merc_rigged.blend'));scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01;scene.render.fps=30;scene.frame_start=1;scene.frame_end=22
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
 for f in range(1,23):
  scene.frame_set(f)
  w=ease(.15,.7,(f-1)/30)
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  # Shared shoulder protraction gives both views a reachable support grip.
  for side in ['r','l']:
   bone=rig.pose.bones['clavicle_'+side];m=bone.matrix.copy();m.translation+=Vector((0,-10,-26 if view else 0))*w;bone.matrix=m
  bpy.context.view_layer.update()
  limb(rig,'upperarm_r','lowerarm_r','hand_r',lerp((-14,-18,113),(-12,-26,133),w),(-30,0,55) if view else (-60,-2,125));limb(rig,'upperarm_l','lowerarm_l','hand_l',lerp((18,-22,114),(-3.7,-50.1,132.8),w),(30,0,55) if view else (60,-5,125));hand_pose(rig,'r');hand_pose(rig,'l')
  for b in rig.pose.bones:b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('scale',frame=f)
 export(name,[rig]);scene.frame_set(22);report[name]={'right':list(rig.pose.bones['hand_r'].head),'left':list(rig.pose.bones['hand_l'].head)}
(OUT/'build.json').write_text(json.dumps(report,indent=2));print('UTILITY_RIFLE_BUILT',json.dumps(report))
