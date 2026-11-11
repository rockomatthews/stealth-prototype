"""Inspect the actual rest glove geometry against its animation skeleton."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];OUT=P/'Saved/HandContactQA';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/ContactCharacters/Merc_contact.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis.identity()
mesh=next(o for o in scene.objects if o.type=='MESH');mesh.data.materials.clear();m=bpy.data.materials.new('Audit');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.23,.27,.3,1);mesh.data.materials.append(m)
w=rig.data.bones['hand_r'].head_local.copy();f=(rig.data.bones['middle_01_r'].head_local-w).normalized();a=(rig.data.bones['index_01_r'].head_local-rig.data.bones['pinky_01_r'].head_local).normalized();n=a.cross(f).normalized();target=w+f*6
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Audit world');scene.world.color=(.3,.3,.3)
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc in [target+n*40+f*20,target-n*40-a*10]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=35000;d.size=30;o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o);o.location=loc;point(o,target)
d=bpy.data.cameras.new('Audit');cam=bpy.data.objects.new('Audit',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=27
for label,loc in [('back',target+n*45),('palm',target-n*45)]:
 cam.location=loc;point(cam,target);scene.render.filepath=str(OUT/f'bind-{label}.png');bpy.ops.render.render(write_still=True)
data={}
for b in rig.data.bones:
 if b.name.endswith('_r') and b.name.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')):
  group=mesh.vertex_groups.get(b.name);verts=[v for v in mesh.data.vertices if group and any(g.group==group.index and g.weight>.5 for g in v.groups)]
  data[b.name]={'head':list(b.head_local),'tail':list(b.tail_local),'weighted_vertices':len(verts),'weighted_center':list(sum((v.co for v in verts),Vector())/len(verts)) if verts else None}
(OUT/'bind.json').write_text(json.dumps(data,indent=2));print('AUDITED_HAND')
