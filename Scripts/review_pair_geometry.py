"""Offline diagnostic renders of the exported animation source, not gameplay."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Saved/ContactQA';OUT.mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
kind=args[0] if args else 'Hold';sample=float(args[1]) if len(args)>1 else 0
bpy.ops.wm.read_factory_settings(use_empty=True)
rigs=[]
for label in ['Spy','Merc']:
 clip=('ChokeExit' if label=='Spy' else 'ChokeFall') if kind=='Collapse' else kind
 path=P/'Art/Grab'/f'{label}{clip}.blend'
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=src.objects
 for obj in dst.objects:
  if obj: bpy.context.scene.collection.objects.link(obj)
 rig=next(o for o in dst.objects if o and o.type=='ARMATURE');rig.location.y=-40 if label=='Merc' else 0;rigs.append(rig)
 for obj in dst.objects:
  if obj and obj.type=='MESH':
   obj.data.materials.clear();m=bpy.data.materials.new(label);m.diffuse_color=(.16,.24,.32,1) if label=='Merc' else (.21,.22,.20,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=m.diffuse_color;obj.data.materials.append(m)
scene=bpy.context.scene;scene.frame_set(round(sample*30)+1)
if kind=='Hold':
 with bpy.data.libraries.load(str(P/'Art/UtilityRifle/MercUtility.blend'),link=False) as (src,dst):dst.objects=src.objects
 for obj in dst.objects:
  if obj:scene.collection.objects.link(obj)
 gun=next(o for o in dst.objects if o and o.type=='ARMATURE');gun.animation_data_clear()
 merc=rigs[1];palm=merc.matrix_world@((merc.pose.bones['hand_r'].head+merc.pose.bones['middle_01_r'].head)/2)
 rotation=Matrix.Rotation(-math.pi/2,4,'Z');gun.matrix_world=Matrix.Translation(palm+rotation.to_3x3()@Vector((1,3.55,0))-rotation.to_3x3()@(Vector((-4.5,-2,-4.5))*.75))@rotation@Matrix.Scale(.75,4)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Contact world');scene.world.color=(.3,.3,.3)
def point(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((100,-180,300),1800000,200),((-150,70,230),1400000,180)]:
 data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=size;o=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(o);o.location=loc;point(o,(0,-25,110))
bpy.ops.mesh.primitive_plane_add(size=1500);floor=bpy.context.object
data=bpy.data.cameras.new('Contact camera');cam=bpy.data.objects.new('Contact camera',data);scene.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';data.clip_end=5000
views=[('side',(300,-25,130),(0,-25,105),220),('front',(0,-350,150),(0,-25,125),160),('neck',(170,-180,170),(0,-25,153),85),('gun',(-180,-120,150),(-8,-77,132),65)]
if kind=='Collapse':views=[('side',(300,-50,80),(20,-50,40),190),('front',(20,-350,80),(20,-50,40),190),('back',(-200,100,120),(20,-50,40),190)]
for view,loc,target,scale in views:
 cam.location=loc;point(cam,target);data.ortho_scale=scale;scene.render.filepath=str(OUT/f'{kind}-{sample:g}-{view}.png');bpy.ops.render.render(write_still=True)
report={r.name:{b.name:list(r.matrix_world@b.head) for b in r.pose.bones if b.name in ['hand_r','hand_l','lowerarm_r','lowerarm_l','head','neck_01','pelvis','calf_r','calf_l','foot_r','foot_l']} for r in rigs}
(OUT/f'{kind}-{sample:g}-bones.json').write_text(json.dumps(report,indent=2))
